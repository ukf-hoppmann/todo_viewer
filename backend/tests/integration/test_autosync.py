"""The automatic sync (STORY-059) with the real storage adapters: a tick is one check of all projects."""
from __future__ import annotations

import dataclasses
import threading
import time
from datetime import datetime
from pathlib import Path

import pytest

from todo_viewer.application.services import AutoSyncService, SyncService, SyncStatusService
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.database import (
    Database,
    DatabaseBacklogRepository,
    DatabaseDocumentStore,
    DatabaseSourceRepository,
    DatabaseSyncStateStore,
)
from todo_viewer.infrastructure.markdown import KeyedLocks, build_markdown_documents, build_markdown_repository
from todo_viewer.infrastructure.markdown.layout import LayoutFactory, SourcePathResolver
from todo_viewer.infrastructure.markdown.merge_markers import MarkdownMergeMarkers
from todo_viewer.infrastructure.routing import RoutingBacklogRepository, RoutingDocumentStore

FIXTURE = Path(__file__).parents[1] / "fixtures" / "backlog"
NOW = datetime(2026, 10, 14, 9, 30, 0).astimezone()


class World:
    def __init__(self, tmp: Path, switch: bool = True):
        self.tmp = tmp
        locks = KeyedLocks()
        db = Database(f"sqlite:///{tmp / 'todo.db'}")
        self.backlogs = RoutingBacklogRepository({"markdown": build_markdown_repository(Path("/"), locks),
                                                  "database": DatabaseBacklogRepository(db)})
        self.documents = RoutingDocumentStore({"markdown": build_markdown_documents(Path("/"), locks),
                                               "database": DatabaseDocumentStore(db)})
        self.sources = DatabaseSourceRepository(db)
        markers = MarkdownMergeMarkers(LayoutFactory(SourcePathResolver(Path("/"))))
        self.sync = SyncService(self.backlogs, self.documents, states=DatabaseSyncStateStore(db), markers=markers)
        self.status = SyncStatusService(self.sync, self.sources, lambda: NOW)
        self.now = NOW
        self.auto = AutoSyncService(self.sync, self.status, self.sources, interval=0, clock=lambda: self.now)
        project = Source(project="Central", path="", backend="database", id="central", sync_path=str(tmp / "md"),
                         auto_sync=switch)
        items = build_markdown_repository(Path("/")).load(Source(project="P", path=str(FIXTURE))).items
        self.backlogs.write_backlog(project, items, "en")
        for path in sorted((FIXTURE / "items").glob("*/*.md")):
            self.documents.write(project, path.parent.name, path.name, path.read_text(encoding="utf-8"), None)
        with self.sources.edit() as sources:
            sources.append(project)
        self.project = project
        self.md = dataclasses.replace(project, backend="markdown", path=str(tmp / "md"), sync_path=None)
        # a manual sync first: both sides equal, every entry has a stored state
        self.status.run(project, self.sync.preview(project).token)
        self.sources_stored = lambda: next(s for s in self.sources.all() if s.id == "central")

    def retitle(self, source: Source, label: str, title: str) -> None:
        items = self.backlogs.load(source).items
        self.backlogs.write_backlog(source, [dataclasses.replace(i, title=title) if i.id == label else i
                                             for i in items], "en")

    def title(self, source: Source, label: str) -> str:
        return self.backlogs.get(source, label).title


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


def test_a_change_of_the_folder_is_taken_over_once_it_stayed_the_same_for_two_checks(world: World):
    world.retitle(world.md, "TASK-001", "Pulled from the cloud")

    world.auto.tick()
    assert world.title(world.project, "TASK-001") != "Pulled from the cloud"  # a pull may still be writing
    world.auto.tick()

    assert world.title(world.project, "TASK-001") == "Pulled from the cloud"
    assert world.auto.info("central").last_run_at == NOW.isoformat(timespec="seconds")
    assert world.auto.info("central").paused is None
    assert world.sources_stored().baseline is not None  # recorded like any other sync


def test_a_change_that_keeps_moving_waits(world: World):
    for n in range(3):
        world.retitle(world.md, "TASK-001", f"Pull in progress {n}")
        world.auto.tick()

    assert world.title(world.project, "TASK-001") != "Pull in progress 2"
    world.auto.tick()
    assert world.title(world.project, "TASK-001") == "Pull in progress 2"


def test_the_database_side_goes_to_the_folder_too(world: World):
    world.retitle(world.project, "TASK-002", "Edited in the viewer")

    world.auto.tick()
    world.auto.tick()

    assert world.title(world.md, "TASK-002") == "Edited in the viewer"


def test_conflicts_stay_open_and_visible_while_the_rest_is_carried_over(world: World):
    world.retitle(world.project, "TASK-001", "In the database")
    world.retitle(world.md, "TASK-001", "In the file")
    world.retitle(world.md, "TASK-002", "Free change")

    world.auto.tick()
    world.auto.tick()
    world.auto.tick()

    assert (world.title(world.project, "TASK-001"), world.title(world.md, "TASK-001")) == ("In the database",
                                                                                           "In the file")
    assert world.title(world.project, "TASK-002") == "Free change"
    assert world.status.status(world.sources_stored()).conflicts == 1


def test_it_never_deletes(world: World):
    world.backlogs.write_backlog(world.md, [i for i in world.backlogs.load(world.md).items if i.id != "TASK-003"],
                                 "en")

    for _ in range(3):
        world.auto.tick()

    assert world.backlogs.get(world.project, "TASK-003")
    assert world.status.status(world.sources_stored()).conflicts == 1


def test_with_the_switch_off_nothing_happens(tmp_path: Path):
    world = World(tmp_path, switch=False)
    world.retitle(world.md, "TASK-001", "Pulled from the cloud")

    world.auto.tick()
    world.auto.tick()

    assert world.title(world.project, "TASK-001") != "Pulled from the cloud"
    assert not world.auto.active()


def test_a_project_without_a_mirror_is_ignored_although_the_switch_is_on(tmp_path: Path):
    world = World(tmp_path)
    with world.sources.edit() as sources:
        sources[0] = dataclasses.replace(sources[0], mirror_disabled=True)

    assert not world.auto.active()
    world.auto.tick()


def test_files_with_merge_markers_pause_the_project_and_nothing_is_read(world: World):
    world.retitle(world.md, "TASK-001", "Half merged")
    todo = world.tmp / "md" / "TODO.md"
    todo.write_text(todo.read_text(encoding="utf-8") + "\n<<<<<<< HEAD\na\n=======\nb\n>>>>>>> origin/main\n",
                    encoding="utf-8")

    world.auto.tick()
    world.auto.tick()

    assert world.auto.info("central").paused == "merge_markers"
    assert world.title(world.project, "TASK-001") != "Half merged"


def test_an_unreadable_or_missing_folder_pauses_and_the_next_good_check_resumes(world: World):
    todo = world.tmp / "md" / "TODO.md"
    good = todo.read_text(encoding="utf-8")
    todo.write_text("Not a backlog.\n", encoding="utf-8")

    world.auto.tick()
    assert world.auto.info("central").paused is not None

    todo.write_text(good, encoding="utf-8")
    world.auto.tick()
    assert world.auto.info("central").paused is None


def test_a_failure_in_one_check_does_not_stop_the_next(world: World, monkeypatch: pytest.MonkeyPatch):
    def boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(world.sync, "preview", boom)
    world.auto.tick()
    monkeypatch.undo()
    world.retitle(world.md, "TASK-001", "After the failure")
    world.auto.tick()
    world.auto.tick()

    assert world.title(world.project, "TASK-001") == "After the failure"


def test_the_checks_are_cheap_and_leave_everything_alone_when_nothing_changed(world: World):
    versions = {i.id: i.version for i in world.backlogs.load(world.project).items}
    baseline = world.sources_stored().baseline

    for _ in range(3):
        world.auto.tick()

    assert {i.id: i.version for i in world.backlogs.load(world.project).items} == versions
    assert world.sources_stored().baseline == baseline and world.auto.info("central").last_run_at is None


def test_an_unknown_project_has_no_info(world: World):
    info = world.auto.info("nobody")

    assert (info.last_run_at, info.paused) == (None, None)


# --- the timer ---

def _wait(condition, seconds: float = 3.0) -> bool:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if condition():
            return True
        time.sleep(0.01)
    return False


def test_the_timer_runs_only_while_a_project_has_the_switch_on(tmp_path: Path):
    world = World(tmp_path)
    ticks = threading.Event()
    count = [0]
    auto = AutoSyncService(world.sync, world.status, world.sources, interval=0.01, clock=lambda: NOW)

    def counting() -> None:
        count[0] += 1
        ticks.set()

    auto.tick = counting  # type: ignore[method-assign]
    auto.ensure_running()
    assert ticks.wait(3) and _wait(lambda: count[0] >= 3)

    with world.sources.edit() as sources:  # the owner switches it off
        sources[0] = dataclasses.replace(sources[0], auto_sync=False)
    assert _wait(lambda: not auto.running)
    seen = count[0]
    time.sleep(0.1)
    assert count[0] == seen

    with world.sources.edit() as sources:  # and on again
        sources[0] = dataclasses.replace(sources[0], auto_sync=True)
    auto.ensure_running()
    assert _wait(lambda: count[0] > seen + 1)
    auto.stop()
    assert not auto.running


def test_without_an_interval_or_a_switch_no_timer_starts(tmp_path: Path):
    world = World(tmp_path)
    off = AutoSyncService(world.sync, world.status, world.sources, interval=0, clock=lambda: NOW)
    nothing = World(tmp_path / "other", switch=False)
    idle = AutoSyncService(nothing.sync, nothing.status, nothing.sources, interval=0.01, clock=lambda: NOW)

    off.ensure_running()
    idle.ensure_running()

    assert not off.running and not idle.running

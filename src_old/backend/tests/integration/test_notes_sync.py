"""Notes, topics, and their documents in the sync (STORY-047), with the real adapters."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from todo_viewer.application.services import NotesSync, SyncService
from todo_viewer.application.services.sync import SyncResult
from todo_viewer.domain.documents import content_version
from todo_viewer.domain.errors import DatabaseBackupFailedError, SyncSourceInvalidError
from todo_viewer.domain.item import Item
from todo_viewer.domain.notes import (
    LinkRole,
    LinkTarget,
    NewNote,
    NewTrigger,
    NoteChanges,
    NoteStatus,
    TargetKind,
    TriggerKind,
)
from todo_viewer.domain.notes_markdown import render_note
from todo_viewer.domain.source import Source
from todo_viewer.domain.sync import Choice, Resolution, SyncDirection
from todo_viewer.infrastructure.database import (
    Database,
    DatabaseBacklogRepository,
    DatabaseDocumentStore,
    DatabaseNoteDocumentStore,
    DatabaseNoteRepository,
    DatabaseSyncStateStore,
)
from todo_viewer.infrastructure.markdown import KeyedLocks, build_markdown_documents, build_markdown_repository
from todo_viewer.infrastructure.notes_files import FilesNotesMirror
from todo_viewer.infrastructure.routing import RoutingBacklogRepository, RoutingDocumentStore

NOON = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
P = "Central"
TO_MD, FROM_MD = SyncDirection.TO_MD, SyncDirection.FROM_MD


@dataclass
class World:
    tmp: Path
    notes: DatabaseNoteRepository
    docs: DatabaseNoteDocumentStore
    service: SyncService
    project: Source
    backups: list[str]

    @property
    def notes_dir(self) -> Path:
        return self.tmp / "md" / "notes"

    def files(self) -> dict[str, str]:
        if not self.notes_dir.is_dir():
            return {}
        return {p.name: p.read_bytes().decode("utf-8")
                for p in sorted(self.notes_dir.iterdir()) if p.is_file()}

    def put(self, name: str, text: str) -> None:
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        (self.notes_dir / name).write_text(text, encoding="utf-8", newline="")

    def sync(self, *resolutions: Resolution, direction: SyncDirection | None = None) -> SyncResult:
        preview = self.service.preview(self.project, direction)
        return self.service.run(self.project, preview.token, resolutions, direction, "en")

    def rendered(self, label: str) -> str:
        return render_note(self.notes.get_note(P, label), self.notes.triggers_of(P, label),
                           self.notes.links_of(P, label))


class Backup:
    def __init__(self, sink: list[str]) -> None:
        self.sink = sink

    def create(self, reason: str) -> str | None:
        self.sink.append(reason)
        return "backup.db"


def build(tmp: Path, name: str = "todo.db") -> World:
    locks = KeyedLocks()
    db = Database(f"sqlite:///{tmp / name}")
    backlogs = RoutingBacklogRepository({"markdown": build_markdown_repository(Path("/"), locks),
                                         "database": DatabaseBacklogRepository(db)})
    documents = RoutingDocumentStore({"markdown": build_markdown_documents(Path("/"), locks),
                                      "database": DatabaseDocumentStore(db)})
    notes = DatabaseNoteRepository(db, clock=lambda: NOON)  # a fixed clock: the files are the same every time
    docs, mirror = DatabaseNoteDocumentStore(db), FilesNotesMirror(Path("/"))
    backups: list[str] = []
    service = SyncService(backlogs, documents, db_backup=Backup(backups), states=DatabaseSyncStateStore(db),
                          notes_sync=NotesSync(notes, docs, mirror), notes_mirror=mirror)
    project = Source(project=P, path="", backend="database", id="central", sync_path=str(tmp / "md"))
    backlogs.write_backlog(project, [Item(id="STORY-003", title="A story", project=P, item_type="Story")], "en")
    return World(tmp, notes, docs, service, project, backups)


@pytest.fixture
def world(tmp_path: Path) -> World:
    return build(tmp_path)


def fill(world: World) -> None:
    """A project with a topic tree, notes of every kind of trigger and link, documents, archive and trash."""
    root = world.notes.create_topic(P, "Sync", None, NOON + timedelta(days=30), 3)
    child = world.notes.create_topic(P, "Format | Dateien", root.label, None, 3)
    world.notes.create_note(P, NewNote("Plain"))
    full = world.notes.create_note(P, NewNote("Prüfen, ob der Sync Notes trägt", "# Text\n\nÄöü\n", child.label,
                                              NOON + timedelta(days=7)))
    story = LinkTarget(TargetKind.ITEM, P, "STORY-003")
    world.notes.add_link(P, full.label, story, LinkRole.REFERENCE)
    world.notes.add_link(P, full.label, LinkTarget(TargetKind.NOTE, P, "NOTE-001"), LinkRole.ORIGIN)
    world.notes.add_link(P, full.label, LinkTarget(TargetKind.ITEM, "Other Project", "TASK-9"), LinkRole.REFERENCE)
    world.notes.add_link(P, full.label, LinkTarget(TargetKind.ITEM, "Gone Project", "TASK-1"), LinkRole.REFERENCE)
    world.notes.add_trigger(P, full.label, NewTrigger(TriggerKind.TIME, at=NOON, fired_at=NOON))
    world.notes.add_trigger(P, full.label, NewTrigger(TriggerKind.EVENT, target=story, target_status="Completed",
                                                      fired_at=NOON, already_met=True))
    world.notes.add_trigger(P, full.label, NewTrigger(TriggerKind.TOPIC_DUE))
    world.docs.write(P, full.label, f"{full.label}_notes.md", "# Notes\n\nZeile\n", None)
    world.docs.write(P, full.label, f"{full.label}_spec_ui.md", "# Spec\n", None)
    old = world.notes.create_note(P, NewNote("Old"))
    world.notes.update_note(P, old.label, old.version, NoteChanges(status=NoteStatus.DONE, archived=True))
    trashed = world.notes.create_note(P, NewNote("Trashed"))
    world.notes.delete_note(P, trashed.label, NOON)


def all_notes(world: World) -> dict[str, str]:
    return {n.label: world.rendered(n.label) for n in world.notes.list_notes(P, include_deleted=True)}


def all_topics(world: World) -> list[tuple[object, ...]]:
    return [(t.label, t.name, t.parent, t.due_at, t.deleted) for t in world.notes.list_topics(P, include_deleted=True)]


def test_a_preview_changes_nothing_and_lists_topics_notes_and_documents(world: World):
    fill(world)
    before = all_notes(world)

    preview = world.service.preview(world.project)

    assert [e.label for e in preview.topics.created] == ["TOPIC-001", "TOPIC-002"]
    assert [e.label for e in preview.notes.created] == ["NOTE-001", "NOTE-002", "NOTE-003", "NOTE-004"]
    assert [e.name for e in preview.note_documents.created] == ["NOTE-002_notes.md", "NOTE-002_spec_ui.md"]
    assert world.files() == {} and all_notes(world) == before


def test_round_trip_database_to_folder_to_an_empty_database_loses_nothing(world: World, tmp_path: Path):
    fill(world)
    world.sync()
    other = build(tmp_path, "other.db")  # an empty database for the same project and the same folder

    other.sync()

    assert all_notes(other) == all_notes(world) and all_topics(other) == all_topics(world)
    assert other.notes.counters(P) == world.notes.counters(P) == {"note": 4, "topic": 2}
    assert other.docs.read(P, "NOTE-002", "NOTE-002_spec_ui.md") == "# Spec\n"
    old = other.notes.get_note(P, "NOTE-003")
    assert (old.status, old.archived) == (NoteStatus.DONE, True) and other.notes.get_note(P, "NOTE-004").deleted == NOON
    assert other.service.in_sync(other.project)
    assert other.service.preview(other.project).conflicts == ()


def test_the_files_are_the_documented_format(world: World):
    fill(world)

    world.sync()

    files = world.files()
    assert set(files) == {"NOTE-001.md", "NOTE-002.md", "NOTE-003.md", "NOTE-004.md", "NOTE-002_notes.md",
                          "NOTE-002_spec_ui.md", "topics.md", "counters.md"}
    assert files["counters.md"] == "NOTE: 4\nTOPIC: 2\n"
    assert files["topics.md"].splitlines()[1].startswith("  - TOPIC-002 | Format \\| Dateien |")
    assert "- event Central:STORY-003 Completed [fired 2026-10-12T09:00:00Z] [already_met]" in files["NOTE-002.md"]
    assert "- reference Gone Project:TASK-1" in files["NOTE-002.md"]  # a link to an unknown project is kept


def test_a_second_sync_finds_nothing_and_an_edit_in_either_place_goes_to_the_other(world: World):
    fill(world)
    world.sync()
    assert world.service.in_sync(world.project)

    note = world.notes.get_note(P, "NOTE-001")
    world.notes.update_note(P, "NOTE-001", note.version, NoteChanges(summary="Edited in the viewer"))
    world.put("NOTE-002.md", world.files()["NOTE-002.md"].replace("Prüfen, ob", "Geprüft, ob"))
    result = world.sync()

    assert {e.label for e in result.resolved} == {"NOTE-001", "NOTE-002"} and result.deferred == ()
    assert "Summary: Edited in the viewer" in world.files()["NOTE-001.md"]
    assert world.notes.get_note(P, "NOTE-002").summary.startswith("Geprüft, ob")
    assert world.service.in_sync(world.project)


def test_a_note_without_a_label_gets_the_next_one_and_its_file_documents_and_references_are_renamed(world: World):
    fill(world)
    world.sync()
    world.put("new-idea.md", "# NEW\nSummary: Aus der Cloud\nStatus: waiting\nTopic: new:Ideen\nMode: any\n"
                             "Links:\n- reference note:new-other\n- reference note:NOTE-001\n\nText aus der Cloud\n")
    world.put("new-idea_notes.md", "# notes of the idea\n")
    world.put("new-other.md", "# NEW\nSummary: Die andere\n")
    topics = world.files()["topics.md"] + "- NEW | Ideen | due=2026-12-24T00:00:00Z\n"
    world.put("topics.md", topics)

    result = world.sync()

    labels = {e.label: e.origin for e in result.preview.notes.created}
    assert labels == {"new-idea": labels["new-idea"], "new-other": labels["new-other"]} and len(labels) == 2
    idea, other = world.notes.get_note(P, "NOTE-005"), world.notes.get_note(P, "NOTE-006")
    assert (idea.summary, other.summary) == ("Aus der Cloud", "Die andere")
    assert world.notes.get_topic(P, "TOPIC-003").name == "Ideen" and idea.topic == "TOPIC-003"
    assert [(link.target.kind, link.target.label) for link in world.notes.links_of(P, "NOTE-005")] == [
        (TargetKind.NOTE, "NOTE-006"), (TargetKind.NOTE, "NOTE-001")]
    assert world.docs.read(P, "NOTE-005", "NOTE-005_notes.md") == "# notes of the idea\n"
    files = world.files()
    assert "new-idea.md" not in files and "new-other.md" not in files and "new-idea_notes.md" not in files
    assert "reference note:NOTE-006" in files["NOTE-005.md"] and "Topic: TOPIC-003" in files["NOTE-005.md"]
    assert "- TOPIC-003 | Ideen |" in files["topics.md"] and "NEW" not in files["topics.md"]
    assert files["NOTE-005_notes.md"] == "# notes of the idea\n" and files["counters.md"] == "NOTE: 6\nTOPIC: 3\n"
    assert world.service.in_sync(world.project)


def test_labels_are_never_reused_the_counter_is_the_highest_of_database_file_and_labels(world: World):
    world.notes.raise_counter(P, "note", 3)
    world.put("counters.md", "NOTE: 9\nTOPIC: 2\n")
    world.put("NOTE-020.md", "# NOTE-020\nSummary: Hoch\n")
    world.put("new-a.md", "# NEW\nSummary: A\n")

    world.sync()

    assert world.notes.get_note(P, "NOTE-021").summary == "A" and world.notes.counters(P)["note"] == 21
    assert world.notes.get_note(P, "NOTE-020").summary == "Hoch"


def test_a_note_edited_on_both_sides_is_a_conflict_that_is_decided_per_note(world: World):
    fill(world)
    world.sync()
    note = world.notes.get_note(P, "NOTE-001")
    world.notes.update_note(P, "NOTE-001", note.version, NoteChanges(summary="In the database"))
    world.put("NOTE-001.md", world.files()["NOTE-001.md"].replace("Summary: Plain", "Summary: In the file"))

    preview = world.service.preview(world.project)
    left = world.sync()
    [conflict] = preview.conflicts
    assert (conflict.entry.kind, conflict.entry.label, conflict.reason.value) == ("note", "NOTE-001", "both_changed")
    assert dict(conflict.database.fields)["summary"] == "In the database"  # type: ignore[union-attr]
    assert dict(conflict.markdown.fields)["summary"] == "In the file"  # type: ignore[union-attr]
    assert [e.label for e in left.deferred] == ["NOTE-001"]
    assert world.notes.get_note(P, "NOTE-001").summary == "In the database"

    world.sync(Resolution("note", "NOTE-001", None, Choice.MARKDOWN))

    assert world.notes.get_note(P, "NOTE-001").summary == "In the file"
    assert world.service.in_sync(world.project)


def test_a_note_document_conflict_and_a_topic_conflict_are_decided_on_their_own(world: World):
    fill(world)
    world.sync()
    world.docs.write(P, "NOTE-002", "NOTE-002_notes.md", "database\n", content_version("# Notes\n\nZeile\n"))
    world.put("NOTE-002_notes.md", "file\n")
    world.notes.update_topic(P, "TOPIC-001", "Renamed in the viewer", None)
    world.put("topics.md", world.files()["topics.md"].replace("| Sync |", "| Renamed in the file |"))

    kinds = sorted((c.entry.kind, c.entry.label) for c in world.service.preview(world.project).conflicts)
    world.sync(Resolution("note_document", "NOTE-002", "NOTE-002_notes.md", Choice.DATABASE),
               Resolution("topic", "TOPIC-001", None, Choice.MARKDOWN))

    assert kinds == [("note_document", "NOTE-002"), ("topic", "TOPIC-001")]
    assert world.files()["NOTE-002_notes.md"] == "database\n"
    assert world.notes.get_topic(P, "TOPIC-001").name == "Renamed in the file"


@pytest.mark.parametrize("choice", [Choice.DATABASE, Choice.MARKDOWN])
def test_a_note_gone_from_the_folder_is_deleted_only_with_a_decision(world: World, choice: Choice):
    fill(world)
    world.sync()
    for name in ("NOTE-002.md", "NOTE-002_notes.md", "NOTE-002_spec_ui.md"):
        (world.notes_dir / name).unlink()

    preview = world.service.preview(world.project)
    kept = world.sync()
    assert [(c.entry.label, c.reason.value) for c in preview.conflicts] == [("NOTE-002", "markdown_deleted")]
    assert world.notes.get_note(P, "NOTE-002") and [e.label for e in kept.kept] == ["NOTE-002"]

    done = world.sync(Resolution("note", "NOTE-002", None, choice))

    if choice is Choice.MARKDOWN:  # the state of the files holds: the note is deleted for good, with its documents
        assert [e.label for e in done.deleted] == ["NOTE-002"]
        labels = [n.label for n in world.notes.list_notes(P, include_deleted=True)]
        assert labels == ["NOTE-001", "NOTE-003", "NOTE-004"]
    else:  # the database holds: the files are written again
        assert {"NOTE-002.md", "NOTE-002_notes.md"} <= set(world.files())


def test_a_note_gone_from_the_database_is_deleted_from_the_folder_only_with_a_decision(world: World):
    fill(world)
    world.sync()
    world.notes.purge_note(P, "NOTE-001")

    world.sync()
    assert "NOTE-001.md" in world.files()

    world.sync(Resolution("note", "NOTE-001", None, Choice.DATABASE))

    assert "NOTE-001.md" not in world.files() and world.service.in_sync(world.project)


def test_a_topic_deeper_than_the_limit_is_imported(world: World):
    world.put("topics.md", "- TOPIC-001 | a\n  - TOPIC-002 | b\n    - TOPIC-003 | c\n      - TOPIC-004 | d\n"
                           "        - TOPIC-005 | e\n")

    world.sync()

    assert world.notes.get_topic(P, "TOPIC-005").parent == "TOPIC-004"


def test_a_link_to_a_project_or_note_that_does_not_exist_is_kept(world: World):
    world.put("NOTE-001.md", "# NOTE-001\nSummary: x\nLinks:\n- reference Nowhere:TASK-1\n- reference note:NOTE-099\n")

    world.sync()

    assert [(link.target.project, link.target.label) for link in world.notes.links_of(P, "NOTE-001")] == [
        ("Nowhere", "TASK-1"), (P, "NOTE-099")]


@pytest.mark.parametrize("name, text, fragment", [
    ("NOTE-001.md", "# NOTE-001\nSummary: x\nStatus: sleeping\n", "NOTE-001.md, line 3"),
    ("NOTE-001.md", "# NOTE-002\nSummary: x\n", "named NOTE-001"),
    ("new-a.md", "# NOTE-005\nSummary: x\n", "named new-a"),
    ("topics.md", "- TOPIC-001\n", "topics.md, line 1"),
    ("counters.md", "NOTES: 3\n", "counters.md, line 1"),
])
def test_a_file_that_does_not_follow_the_format_stops_the_sync_before_anything_is_changed(
        world: World, name: str, text: str, fragment: str):
    fill(world)
    world.sync()
    world.put(name, text)
    before = all_notes(world)

    with pytest.raises(SyncSourceInvalidError) as error:
        world.service.preview(world.project)

    assert error.value.details["reason"] == "note_format" and fragment in error.value.message
    assert all_notes(world) == before


def test_the_direction_restricts_which_side_is_written_and_a_note_without_label_waits_for_both(world: World):
    fill(world)
    world.sync()
    note = world.notes.get_note(P, "NOTE-001")
    world.notes.update_note(P, "NOTE-001", note.version, NoteChanges(summary="Database edit"))
    world.put("NOTE-003.md", world.files()["NOTE-003.md"].replace("Summary: Old", "Summary: File edit"))
    world.put("new-x.md", "# NEW\nSummary: Waiting\n")

    world.sync(direction=FROM_MD)
    assert world.notes.get_note(P, "NOTE-003").summary == "File edit"
    assert "Summary: Plain" in world.files()["NOTE-001.md"]  # not written: the folder was excluded
    assert "new-x.md" in world.files() and len(world.notes.list_notes(P, include_deleted=True)) == 4

    world.sync(direction=TO_MD)
    assert "Summary: Database edit" in world.files()["NOTE-001.md"]
    assert "new-x.md" in world.files()

    world.sync()
    assert "new-x.md" not in world.files() and world.notes.get_note(P, "NOTE-005").summary == "Waiting"


def test_a_sync_that_writes_notes_into_the_database_makes_a_backup_first_and_one_that_only_writes_files_does_not(
        world: World):
    fill(world)
    world.sync()
    assert world.backups == []
    world.put("new-x.md", "# NEW\nSummary: x\n")

    world.sync()

    assert world.backups == ["sync"]


def test_a_failed_backup_leaves_notes_and_files_as_they_are(world: World):
    fill(world)
    world.sync()
    world.put("new-x.md", "# NEW\nSummary: x\n")

    class Broken:
        def create(self, reason: str) -> str | None:
            raise DatabaseBackupFailedError("disk full")

    world.service._db_backup = Broken()  # type: ignore[assignment]
    before = world.files()

    with pytest.raises(DatabaseBackupFailedError):
        world.sync()

    assert world.files() == before and len(world.notes.list_notes(P, include_deleted=True)) == 4


def test_the_status_counts_note_conflicts_too(world: World):
    fill(world)
    world.sync()
    note = world.notes.get_note(P, "NOTE-001")
    world.notes.update_note(P, "NOTE-001", note.version, NoteChanges(summary="In the database"))
    world.put("NOTE-001.md", world.files()["NOTE-001.md"].replace("Summary: Plain", "Summary: In the file"))
    world.project = Source(project=P, path="", backend="database", id="central", sync_path=str(world.tmp / "md"))

    sides = world.service.fingerprints(world.project)

    assert sides is not None and sides.conflicts == 1


def test_a_project_without_notes_has_the_same_fingerprints_as_before(world: World):
    from todo_viewer.domain.sync import fingerprint

    assert fingerprint([], {}) == fingerprint([], {}, {})
    story = [Item(id="STORY-003", title="A story", project=P, item_type="Story")]
    sides = world.service.fingerprints(world.project)
    assert sides is not None and sides.primary == fingerprint(story, {}) and sides.mirror == fingerprint([], {})


def test_a_file_that_changes_while_the_sync_runs_is_not_overwritten(world: World, monkeypatch: pytest.MonkeyPatch):
    fill(world)
    world.sync()
    note = world.notes.get_note(P, "NOTE-001")
    world.notes.update_note(P, "NOTE-001", note.version, NoteChanges(summary="In the database"))
    preview = world.service.preview(world.project)
    original = FilesNotesMirror.write

    def meanwhile(self: FilesNotesMirror, source: Source, name: str, text: str, expected: str | None) -> None:
        (world.notes_dir / name).write_text("edited meanwhile\n", encoding="utf-8")
        original(self, source, name, text, expected)

    monkeypatch.setattr(FilesNotesMirror, "write", meanwhile)
    from todo_viewer.domain.errors import MirrorConflictError

    with pytest.raises(MirrorConflictError):
        world.service.run(world.project, preview.token, (), None, "en")

    assert world.files()["NOTE-001.md"] == "edited meanwhile\n"


def test_the_whole_chain_from_the_database_to_the_folder_is_pinned_by_a_golden_file(world: World):
    """Notes, topics, links, triggers, documents, archive, trash, and counters as the files hold them."""
    import json
    import os

    fill(world)
    world.sync()
    golden = Path(__file__).parents[1] / "golden" / "notes" / "mirror_folder.json"
    if os.environ.get("UPDATE_GOLDEN") == "1" or not golden.exists():
        golden.write_text(json.dumps(world.files(), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                          encoding="utf-8")
        if os.environ.get("UPDATE_GOLDEN") != "1":
            pytest.fail("golden file mirror_folder.json created, re-run to verify")

    assert world.files() == json.loads(golden.read_text(encoding="utf-8"))

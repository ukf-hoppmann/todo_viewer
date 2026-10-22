"""Der Papierkorb nimmt Einträge auf, die ein Plugin beisteuert und selbst wiederherstellt oder löscht (STORY-094)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

from viewer.core.application.ports import Transaction
from viewer.plugins.workspace.domain.model import TrashEntry
from workspace_env import Env


class FakeSource:
    """Hält Einträge im Speicher und merkt sich, was mit ihnen geschah."""

    def __init__(self) -> None:
        self.entries: dict[str, TrashEntry] = {}
        self.restored: list[str] = []
        self.purged: list[str] = []
        self.queries: list[tuple[Sequence[str] | None, str]] = []

    def add(
        self, uid: str, project_uid: str, deleted_at: datetime, label: str = "TASK-001", title: str = "x_spec.md"
    ) -> None:
        self.entries[uid] = TrashEntry(uid, project_uid, "document", label, title, deleted_at, "owner-1")

    def list_deleted(self, tx: Transaction, project_uids: Sequence[str] | None, query: str) -> list[TrashEntry]:
        self.queries.append((project_uids, query))
        return [e for e in self.entries.values() if project_uids is None or e.project_uid in project_uids]

    def get(self, tx: Transaction, uid: str) -> TrashEntry | None:
        return self.entries.get(uid)

    def restore(self, tx: Transaction, uid: str) -> None:
        self.restored.append(uid)
        del self.entries[uid]

    def purge(self, tx: Transaction, uid: str) -> None:
        self.purged.append(uid)
        del self.entries[uid]


def _source(env: Env) -> FakeSource:
    source = FakeSource()
    env.workspace.trash.register_source(source)
    return source


def _trash(env: Env, **params: Any) -> list[dict[str, Any]]:
    return env.client.get("/api/workspace/trash", params=params).json()  # type: ignore[no-any-return]


def test_the_trash_lists_entries_of_a_source_among_the_elements_newest_first(env: Env) -> None:
    project = str(env.general()["uid"])
    source = _source(env)
    task = env.kinds.add(project, "task", title="Aufgabe")
    version = env.kinds.run(lambda r, tx: r.get(tx, task.uid)).revision
    env.client.request("DELETE", f"/api/workspace/elements/{task.uid}", params={"version": version, "cascade": False})
    env.clock.advance(timedelta(minutes=1))
    source.add("doc-1", project, env.clock.now())

    listed = _trash(env)

    assert [(e["uid"], e["kind"], e["owner_uid"]) for e in listed] == [
        ("doc-1", "document", "owner-1"),
        (task.uid, "task", None),
    ]


def test_the_filters_reach_the_source(env: Env) -> None:
    source = _source(env)
    project = str(env.general()["uid"])

    _trash(env, projects=project, query="spec")

    assert source.queries == [([project], "spec")]


def test_restoring_an_entry_of_a_source_hands_it_to_the_source(env: Env) -> None:
    source = _source(env)
    source.add("doc-1", str(env.general()["uid"]), env.clock.now())

    r = env.client.post("/api/workspace/trash/restore", json={"uids": ["doc-1"]})

    assert r.json() == {"uids": ["doc-1"]}
    assert source.restored == ["doc-1"]
    assert _trash(env) == []


def test_purging_an_entry_of_a_source_backs_up_first_and_hands_it_to_the_source(env: Env) -> None:
    source = _source(env)
    source.add("doc-1", str(env.general()["uid"]), env.clock.now())

    r = env.client.post("/api/workspace/trash/purge", json={"uids": ["doc-1"]})

    assert r.json() == {"uids": ["doc-1"]}
    assert source.purged == ["doc-1"]
    assert len(sorted((env.tmp_path / "backups").glob("*-purge.db"))) == 1


def test_a_failing_backup_leaves_the_entry_of_a_source_alone(env: Env) -> None:
    source = _source(env)
    source.add("doc-1", str(env.general()["uid"]), env.clock.now())
    (env.tmp_path / "backups").write_text("keine Ordner")

    r = env.client.post("/api/workspace/trash/purge", json={"uids": ["doc-1"]})

    assert r.status_code >= 400
    assert source.purged == []


def test_an_unknown_uid_is_not_found(env: Env) -> None:
    _source(env)

    r = env.client.post("/api/workspace/trash/restore", json={"uids": ["gibt-es-nicht"]})

    assert (r.status_code, r.json()["code"]) == (404, "not_found")


def test_elements_and_entries_of_a_source_can_be_restored_together(env: Env) -> None:
    project = str(env.general()["uid"])
    source = _source(env)
    source.add("doc-1", project, env.clock.now())
    task = env.kinds.add(project, "task")
    version = env.kinds.run(lambda r, tx: r.get(tx, task.uid)).revision
    env.client.request("DELETE", f"/api/workspace/elements/{task.uid}", params={"version": version, "cascade": False})

    r = env.client.post("/api/workspace/trash/restore", json={"uids": [task.uid, "doc-1"]})

    assert sorted(r.json()["uids"]) == sorted([task.uid, "doc-1"])
    assert source.restored == ["doc-1"]

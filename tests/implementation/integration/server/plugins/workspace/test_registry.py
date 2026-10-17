from __future__ import annotations

import pytest
from viewer.core.domain.errors import InvalidInput, NotFound, VersionConflict
from viewer.plugins.workspace.domain.model import UnknownElementKind
from workspace_env import Env


def _register(env: Env, project: str, kind: str):  # type: ignore[no-untyped-def]
    return env.kinds.run(lambda registry, tx: registry.register(tx, project, kind))


def test_labels_count_per_project_and_prefix(env: Env) -> None:
    a = str(env.create("A")["uid"])
    b = str(env.create("B")["uid"])

    labels = [
        _register(env, a, "task").label,
        _register(env, a, "task").label,
        _register(env, a, "story").label,
        _register(env, b, "task").label,
    ]

    assert labels == ["TASK-001", "TASK-002", "STORY-001", "TASK-001"]


def test_a_label_is_never_given_out_again(env: Env) -> None:
    project = str(env.general()["uid"])
    first = _register(env, project, "task")
    env.kinds.run(lambda registry, tx: registry.mark_deleted(tx, first.uid))
    env.kinds.run(lambda registry, tx: registry.purge(tx, first.uid))

    again = _register(env, project, "task")

    assert (first.label, again.label) == ("TASK-001", "TASK-002")
    assert env.kinds.run(lambda registry, tx: registry.get(tx, first.uid)) is None


def test_relabel_gives_a_new_label_and_the_old_one_still_resolves(env: Env) -> None:
    project = str(env.general()["uid"])
    task = _register(env, project, "task")

    moved = env.kinds.run(lambda registry, tx: registry.relabel(tx, task.uid, "story"))
    newer = _register(env, project, "task")

    assert (moved.uid, moved.kind, moved.label) == (task.uid, "story", "STORY-001")
    assert newer.label == "TASK-002"
    for label in ("TASK-001", "STORY-001"):
        found = env.kinds.run(lambda registry, tx, label=label: registry.find_by_label(tx, project, label))
        assert found is not None and found.uid == task.uid
    assert env.client.get(f"/api/workspace/projects/{project}/labels/TASK-001").json()["uid"] == task.uid
    assert env.client.get(f"/api/workspace/projects/{project}/labels/TASK-099").status_code == 400


def test_relabel_to_the_same_kind_changes_nothing(env: Env) -> None:
    task = _register(env, str(env.general()["uid"]), "task")

    same = env.kinds.run(lambda registry, tx: registry.relabel(tx, task.uid, "task"))

    assert same.label == "TASK-001"


def test_unknown_kind_and_unknown_project_are_refused(env: Env) -> None:
    project = str(env.general()["uid"])

    with pytest.raises(UnknownElementKind):
        _register(env, project, "gibt-es-nicht")
    with pytest.raises(NotFound):
        _register(env, "kein-projekt", "task")


def test_revision_conflict_and_restore(env: Env) -> None:
    task = _register(env, str(env.general()["uid"]), "task")

    assert env.kinds.run(lambda registry, tx: registry.bump_revision(tx, task.uid, 1)) == 2
    with pytest.raises(VersionConflict):
        env.kinds.run(lambda registry, tx: registry.bump_revision(tx, task.uid, 1))
    deleted = env.kinds.run(lambda registry, tx: registry.mark_deleted(tx, task.uid))
    restored = env.kinds.run(lambda registry, tx: registry.restore(tx, task.uid))

    assert deleted.deleted_at is not None and restored.deleted_at is None


def test_browse_folders_lists_sub_folders_and_marks_todo_folders(env: Env) -> None:
    (env.tmp_path / "plain").mkdir()
    (env.tmp_path / "docs").mkdir()
    (env.tmp_path / "docs" / "TODO.md").write_text("x", encoding="utf-8")
    (env.tmp_path / ".hidden").mkdir()

    r = env.client.get("/api/workspace/folders", params={"path": str(env.tmp_path)})

    body = r.json()
    assert body["path"] == str(env.tmp_path.resolve())
    assert [d["name"] for d in body["folders"]] == ["docs", "plain"]
    assert [d["has_mirror"] for d in body["folders"]] == [True, False]


def test_a_label_can_be_reserved_and_an_element_created_with_a_given_uid_and_label(env: Env) -> None:
    project = str(env.general()["uid"])

    reserved = env.kinds.run(lambda registry, tx: registry.reserve_label(tx, project, "task"))
    element = env.kinds.run(
        lambda registry, tx: registry.register_as(tx, project, "story", "u-1", "STORY-007", "Titel")
    )
    after = _register(env, project, "story")
    next_task = _register(env, project, "task")

    assert reserved == "TASK-001" and next_task.label == "TASK-002"  # die Reservierung wird nie wieder vergeben
    assert (element.uid, element.label, element.title) == ("u-1", "STORY-007", "Titel")
    assert after.label == "STORY-008"  # der Zähler zog mit dem vorgegebenen Label nach
    found = env.kinds.run(lambda registry, tx: registry.find_by_label(tx, project, "STORY-007"))
    assert found is not None and found.uid == "u-1"


def test_register_as_refuses_a_label_of_another_type_a_label_in_use_and_an_unknown_project(env: Env) -> None:
    project = str(env.general()["uid"])
    env.kinds.run(lambda registry, tx: registry.register_as(tx, project, "task", "u-1", "TASK-005"))

    with pytest.raises(InvalidInput):
        env.kinds.run(lambda registry, tx: registry.register_as(tx, project, "task", "u-2", "STORY-001"))
    with pytest.raises(InvalidInput):
        env.kinds.run(lambda registry, tx: registry.register_as(tx, project, "task", "u-3", "TASK-005"))
    with pytest.raises(NotFound):
        env.kinds.run(lambda registry, tx: registry.register_as(tx, "kein-projekt", "task", "u-4", "TASK-009"))


def test_noted_labels_raise_the_counters_without_creating_anything(env: Env) -> None:
    project = str(env.general()["uid"])

    env.kinds.run(lambda registry, tx: registry.note_labels(tx, project, ["TASK-010", "STORY-003", "kein-label"]))

    assert _register(env, project, "task").label == "TASK-011"
    assert _register(env, project, "story").label == "STORY-004"


def test_an_element_can_be_deleted_at_a_given_time(env: Env) -> None:
    from datetime import UTC, datetime

    project = str(env.general()["uid"])
    task = _register(env, project, "task")
    at = datetime(2026, 10, 10, tzinfo=UTC)

    deleted = env.kinds.run(lambda registry, tx: registry.mark_deleted(tx, task.uid, at))

    assert deleted.deleted_at == at

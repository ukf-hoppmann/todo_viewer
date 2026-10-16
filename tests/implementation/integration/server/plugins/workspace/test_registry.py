from __future__ import annotations

import pytest
from viewer.core.domain.errors import NotFound, VersionConflict
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

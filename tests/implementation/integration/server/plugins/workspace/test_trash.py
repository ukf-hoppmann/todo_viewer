from __future__ import annotations

from datetime import timedelta
from typing import Any

from workspace_env import Env


def _tree(env: Env) -> tuple[str, Any, Any, Any, Any]:
    """epic ─┬─ story ── task, epic ── task2; dazu ein loses Element."""
    project = str(env.general()["uid"])
    epic = env.kinds.add(project, "epic", title="Epic")
    story = env.kinds.add(project, "story", epic.uid, "Story")
    task = env.kinds.add(project, "task", story.uid, "Task")
    other = env.kinds.add(project, "task", epic.uid, "Zweite")
    return project, epic, story, task, other


def _delete(env: Env, element: Any, cascade: bool = False, version: int | None = None) -> Any:
    params = {"version": version or env.kinds.run(lambda r, tx: r.get(tx, element.uid)).revision, "cascade": cascade}
    return env.client.request("DELETE", f"/api/workspace/elements/{element.uid}", params=params)


def _trash(env: Env, **params: Any) -> list[dict[str, Any]]:
    return env.client.get("/api/workspace/trash", params=params).json()  # type: ignore[no-any-return]


def _get(env: Env, element: Any) -> Any:
    return env.kinds.run(lambda r, tx: r.get(tx, element.uid))


def test_deleting_an_element_without_children_puts_it_in_the_trash(env: Env) -> None:
    _, _, _, task, _ = _tree(env)

    r = _delete(env, task)

    assert r.json() == {"has_children": False, "children": 0, "deleted": 1}
    assert _get(env, task).deleted_at is not None
    assert [e["label"] for e in _trash(env)] == ["TASK-001"]


def test_deleting_an_element_with_children_asks_first_and_then_takes_the_whole_subtree(env: Env) -> None:
    _, epic, story, task, other = _tree(env)

    asked = _delete(env, epic)
    assert asked.json() == {"has_children": True, "children": 3, "deleted": 0}
    assert _get(env, epic).deleted_at is None

    done = _delete(env, epic, cascade=True)

    assert done.json() == {"has_children": False, "children": 3, "deleted": 4}
    stamps = {_get(env, e).deleted_at for e in (epic, story, task, other)}
    assert len(stamps) == 1 and None not in stamps


def test_delete_with_an_old_version_is_a_conflict_and_a_deleted_element_is_gone(env: Env) -> None:
    _, _, _, task, _ = _tree(env)

    stale = _delete(env, task, version=99)
    _delete(env, task)
    again = _delete(env, task)

    assert (stale.status_code, stale.json()["code"]) == (409, "version_conflict")
    assert again.status_code == 404
    assert _get(env, task).deleted_at is not None


def test_a_subtree_member_that_was_deleted_earlier_keeps_its_own_date(env: Env) -> None:
    _, epic, story, task, other = _tree(env)
    _delete(env, other)
    env.clock.advance(timedelta(minutes=5))

    _delete(env, epic, cascade=True)

    assert _get(env, other).deleted_at != _get(env, epic).deleted_at
    assert _get(env, story).deleted_at == _get(env, epic).deleted_at


def test_restore_brings_back_the_element_with_the_children_deleted_with_it_but_not_earlier_ones(env: Env) -> None:
    _, epic, story, task, other = _tree(env)
    _delete(env, other)
    env.clock.advance(timedelta(minutes=5))
    _delete(env, epic, cascade=True)

    r = env.client.post("/api/workspace/trash/restore", json={"uids": [epic.uid]})

    assert sorted(r.json()["uids"]) == sorted([epic.uid, story.uid, task.uid])
    assert [_get(env, e).deleted_at is None for e in (epic, story, task)] == [True, True, True]
    assert _get(env, other).deleted_at is not None


def test_the_restore_rule_of_the_plugin_applies(env: Env) -> None:
    _, epic, story, task, _ = _tree(env)
    _delete(env, epic, cascade=True)

    r = env.client.post("/api/workspace/trash/restore", json={"uids": [story.uid]})

    assert (r.status_code, r.json()["code"]) == (400, "parent_in_trash")
    assert _get(env, story).deleted_at is not None and _get(env, task).deleted_at is not None


def test_a_failing_bulk_restore_changes_nothing(env: Env) -> None:
    _, epic, story, _, other = _tree(env)
    _delete(env, epic, cascade=True)

    r = env.client.post("/api/workspace/trash/restore", json={"uids": [other.uid, story.uid]})

    assert r.status_code == 400
    # `other` liegt unter `epic`, das nicht mehr gewählt ist: die Regel greift schon beim ersten
    assert _get(env, other).deleted_at is not None


def test_a_chosen_descendant_of_a_chosen_element_is_skipped(env: Env) -> None:
    _, epic, story, task, other = _tree(env)
    _delete(env, epic, cascade=True)

    r = env.client.post("/api/workspace/trash/restore", json={"uids": [task.uid, epic.uid, story.uid]})

    assert sorted(r.json()["uids"]) == sorted([epic.uid, story.uid, task.uid, other.uid])


def test_restoring_something_that_is_not_in_the_trash_is_refused(env: Env) -> None:
    _, epic, _, _, _ = _tree(env)

    r = env.client.post("/api/workspace/trash/restore", json={"uids": [epic.uid]})

    assert (r.status_code, r.json()["code"]) == (400, "not_deleted")


def test_an_element_of_a_removed_project_cannot_be_restored(env: Env) -> None:
    project = env.create("Weg")
    element = env.kinds.add(str(project["uid"]), "task")
    _delete(env, element)
    removed = env.client.request(
        "DELETE", f"/api/workspace/projects/{project['uid']}", params={"version": 1, "confirm": True}
    )
    assert removed.status_code == 200

    r = env.client.post("/api/workspace/trash/restore", json={"uids": [element.uid]})

    assert (r.status_code, r.json()["code"]) == (400, "project_in_trash")


def test_purge_removes_the_subtree_plugin_data_and_links(env: Env) -> None:
    project, epic, story, task, other = _tree(env)
    outside = env.kinds.add(project, "task", title="Draußen")
    env.client.post("/api/workspace/links", json={"from_uid": outside.uid, "to_uid": task.uid, "role": "reference"})
    _delete(env, epic, cascade=True)

    r = env.client.post("/api/workspace/trash/purge", json={"uids": [epic.uid]})

    assert sorted(r.json()["uids"]) == sorted([epic.uid, story.uid, task.uid, other.uid])
    assert env.kinds.purged[-1] == epic.uid  # Kinder zuerst, das Elternelement zuletzt
    assert all(_get(env, e) is None for e in (epic, story, task, other))
    assert env.client.get(f"/api/workspace/elements/{outside.uid}/links").json()["outgoing"] == []
    assert _trash(env) == []


def test_purge_only_takes_elements_from_the_trash(env: Env) -> None:
    _, _, _, task, _ = _tree(env)

    r = env.client.post("/api/workspace/trash/purge", json={"uids": [task.uid]})

    assert (r.status_code, r.json()["code"]) == (400, "not_deleted")
    assert _get(env, task) is not None


def test_the_trash_lists_by_project_and_text_newest_first(env: Env) -> None:
    other = env.create("Anderes")
    one = env.kinds.add(str(env.general()["uid"]), "task", title="Sync reparieren")
    two = env.kinds.add(str(other["uid"]), "story", title="Anderes Thema")
    _delete(env, one)
    env.clock.advance(timedelta(minutes=1))
    _delete(env, two)

    assert [e["uid"] for e in _trash(env)] == [two.uid, one.uid]
    assert [e["uid"] for e in _trash(env, projects=str(other["uid"]))] == [two.uid]
    assert [e["uid"] for e in _trash(env, query="sync")] == [one.uid]
    assert _trash(env, projects="") == []
    assert {"uid", "project_uid", "kind", "label", "title", "deleted_at"} <= set(_trash(env)[0])


def test_changes_are_public_events_and_purging_is_no_mcp_tool(env: Env) -> None:
    _, _, _, task, _ = _tree(env)
    seen: list[tuple[bool, str, int]] = []
    env.app.state.events.subscribe(
        "workspace.element.changed", lambda e: seen.append((e.public, e.payload["change"], len(e.payload["uids"])))
    )

    _delete(env, task)
    env.client.post("/api/workspace/trash/restore", json={"uids": [task.uid]})
    _delete(env, task)
    env.client.post("/api/workspace/trash/purge", json={"uids": [task.uid]})

    assert seen == [(True, "deleted", 1), (True, "restored", 1), (True, "deleted", 1), (True, "purged", 1)]
    mcp = {
        op.name
        for p in env.app.state.plugin_host.plugins
        if p.definition.id == "workspace"
        for op in p.definition.operations
        if op.mcp
    }
    assert {"delete_element", "list_trash", "restore_elements"} <= mcp
    assert "purge_elements" not in mcp

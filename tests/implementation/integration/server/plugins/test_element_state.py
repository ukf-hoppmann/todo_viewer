"""Backlog und Notes melden beim Register von `workspace` an, wann ihre Elemente geschlossen sind."""

from __future__ import annotations

from typing import Any

from workspace_env import Env


def _project(env: Env) -> str:
    return str(env.general()["uid"])


def _is_open(env: Env, uid: str) -> bool:
    with env.app.state.database.transaction() as tx:
        return bool(env.workspace.registry.is_open(tx, uid))


def _task(env: Env) -> dict[str, Any]:
    fields = {"title": "T", "area": "A", "goal": "G", "completion_criteria": "C"}
    response = env.client.post("/api/backlog/items", json={"project": _project(env), "type": "Task", "fields": fields})
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _set_status(env: Env, item: dict[str, Any], status: str, **body: Any) -> dict[str, Any]:
    response = env.client.put(
        f"/api/backlog/items/{item['uid']}", json={"version": item["version"], "fields": {"status": status}, **body}
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def test_a_backlog_item_is_closed_when_completed_or_rejected(full: Env) -> None:
    item = _task(full)
    assert _is_open(full, item["uid"])
    item = _set_status(full, item, "Awaiting confirmation")
    assert _is_open(full, item["uid"])
    item = _set_status(full, item, "Completed", resolution="fertig")
    assert not _is_open(full, item["uid"])
    item = _set_status(full, item, "In progress")
    assert _is_open(full, item["uid"])


def test_a_memo_is_closed_when_finished_and_a_topic_when_archived(full: Env) -> None:
    memo = full.client.post("/api/memos/memos", json={"project": _project(full), "fields": {"summary": "N"}}).json()
    assert _is_open(full, memo["uid"])
    finished = full.client.post(
        f"/api/memos/memos/{memo['uid']}/finish", json={"version": memo["version"], "status": "done"}
    )
    assert finished.status_code == 200, finished.text
    assert not _is_open(full, memo["uid"])

    topic = full.client.post("/api/memos/topics", json={"project": _project(full), "name": "T"}).json()
    assert _is_open(full, topic["uid"])
    archived = full.client.post(
        f"/api/memos/topics/{topic['uid']}/archive", json={"version": 1}
    )  # neu angelegt: Version 1
    assert archived.status_code == 200, archived.text
    assert not _is_open(full, topic["uid"])

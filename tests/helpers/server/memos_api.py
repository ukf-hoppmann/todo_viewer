"""Kleine Hilfen für die Tests der Memos über die HTTP-Schnittstelle (mit dem echten `backlog` daneben)."""

from __future__ import annotations

from typing import Any

from workspace_env import Env

NOTES = "/api/memos"
BACKLOG = "/api/backlog"
ITEM_FIELDS = {"title": "Ein Item", "goal": "Ziel", "completion_criteria": "Kriterien"}


def project(env: Env) -> str:
    return str(env.general()["uid"])


def new_memo(env: Env, summary: str = "Idee", **fields: Any) -> dict[str, Any]:
    response = env.client.post(
        f"{NOTES}/memos", json={"project": project(env), "fields": {"summary": summary, **fields}}
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def new_item(env: Env, type_: str = "Task", **fields: Any) -> dict[str, Any]:
    response = env.client.post(
        f"{BACKLOG}/items", json={"project": project(env), "type": type_, "fields": {**ITEM_FIELDS, **fields}}
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def item(env: Env, uid: str) -> dict[str, Any]:
    return env.client.get(f"{BACKLOG}/items/{uid}").json()  # type: ignore[no-any-return]


def set_status(env: Env, entry: dict[str, Any], status: str, resolution: str | None = None) -> dict[str, Any]:
    current = item(env, entry["uid"])
    response = env.client.put(
        f"{BACKLOG}/items/{entry['uid']}",
        json={"version": current["version"], "fields": {"status": status}, "resolution": resolution},
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def memo(env: Env, uid: str) -> dict[str, Any]:
    response = env.client.get(f"{NOTES}/memos/{uid}")
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def link(env: Env, from_uid: str, to_uid: str, role: str = "reference") -> None:
    response = env.client.post("/api/workspace/links", json={"from_uid": from_uid, "to_uid": to_uid, "role": role})
    assert response.status_code == 200, response.text


def links(env: Env, uid: str) -> dict[str, list[dict[str, Any]]]:
    return env.client.get(f"/api/workspace/elements/{uid}/links").json()  # type: ignore[no-any-return]


def add_trigger(env: Env, entry: dict[str, Any], **body: Any) -> Any:
    return env.client.post(f"{NOTES}/memos/{entry['uid']}/triggers", json=body)


def decide(env: Env, hint_uid: str, decision: str, **body: Any) -> Any:
    return env.client.post(f"{NOTES}/hints/{hint_uid}/decide", json={"decision": decision, **body})

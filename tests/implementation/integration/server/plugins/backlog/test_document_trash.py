"""Notiz- und Spec-Dokumente löschen (STORY-094): sie gehen in den Papierkorb und lassen sich von dort zurückholen."""

from __future__ import annotations

from typing import Any

from workspace_env import Env

BASE = {"title": "Ein Item", "area": "Server", "goal": "Ziel", "completion_criteria": "Kriterien"}


def _create(env: Env, **fields: Any) -> dict[str, Any]:
    body = {"project": str(env.general()["uid"]), "type": "Task", "fields": {**BASE, **fields}}
    return env.client.post("/api/backlog/items", json=body).json()  # type: ignore[no-any-return]


def _note(env: Env, item: dict[str, Any], **body: Any) -> Any:
    payload = {"topic": "Thema", "discussed": ["Besprochen"], "decided": [], "open": [], **body}
    return env.client.post(f"/api/backlog/items/{item['uid']}/notes", json=payload)


def _spec(env: Env, item: dict[str, Any], name: str = "TASK-001_spec.md") -> None:
    env.client.put(f"/api/backlog/items/{item['uid']}/documents/{name}", json={"content": "# Spec\n"})


def _delete(env: Env, item: dict[str, Any], name: str, version: int = 1) -> Any:
    return env.client.delete(f"/api/backlog/items/{item['uid']}/documents/{name}", params={"version": version})


def _names(env: Env, item: dict[str, Any]) -> list[str]:
    listed = env.client.get(f"/api/backlog/items/{item['uid']}/documents").json()
    return [d["name"] for d in listed]


def _detail(env: Env, item: dict[str, Any]) -> dict[str, Any]:
    return env.client.get(f"/api/backlog/items/{item['uid']}").json()  # type: ignore[no-any-return]


def test_a_spec_can_be_deleted_and_created_again(backlog: Env) -> None:
    item = _create(backlog)
    _spec(backlog, item)

    deleted = _delete(backlog, item, "TASK-001_spec.md")

    assert deleted.status_code == 200
    assert _names(backlog, item) == []
    assert backlog.client.get(f"/api/backlog/items/{item['uid']}/documents/TASK-001_spec.md").status_code == 400
    again = backlog.client.put(
        f"/api/backlog/items/{item['uid']}/documents/TASK-001_spec.md", json={"content": "# Neu\n"}
    )
    assert again.status_code == 200 and again.json()["version"] == 1


def test_a_topic_spec_is_deleted_like_the_main_spec_and_leaves_the_others(backlog: Env) -> None:
    item = _create(backlog)
    _spec(backlog, item)
    _spec(backlog, item, "TASK-001_spec_api.md")

    _delete(backlog, item, "TASK-001_spec_api.md")

    assert _names(backlog, item) == ["TASK-001_spec.md"]


def test_deleting_the_notes_takes_the_head_the_entries_and_the_summary_with_it(backlog: Env) -> None:
    item = _create(backlog)
    _note(backlog, item, summary="Kurzfassung")

    deleted = _delete(backlog, item, "TASK-001_notes.md")

    assert deleted.status_code == 200
    assert _names(backlog, item) == []
    detail = _detail(backlog, item)
    assert (detail["notes"], detail["summary"]) == ([], None)
    assert backlog.client.get(f"/api/backlog/items/{item['uid']}/notes/state").status_code == 400
    fresh = _note(backlog, item, topic="Neu", discussed=["Frisch"], summary="Andere Kurzfassung")
    assert fresh.status_code == 200 and fresh.json()["version"] == 1
    assert "Besprochen" not in fresh.json()["content"] and "Frisch" in fresh.json()["content"]


def test_deleting_a_spec_keeps_the_summary_of_the_item(backlog: Env) -> None:
    item = _create(backlog, summary="Bleibt")
    _spec(backlog, item)

    _delete(backlog, item, "TASK-001_spec.md")

    assert _detail(backlog, item)["summary"] == "Bleibt"


def test_a_changed_document_is_a_version_conflict_and_nothing_goes_away(backlog: Env) -> None:
    item = _create(backlog)
    _spec(backlog, item)

    stale = _delete(backlog, item, "TASK-001_spec.md", version=7)

    assert (stale.status_code, stale.json()["code"]) == (409, "version_conflict")
    assert _names(backlog, item) == ["TASK-001_spec.md"]


def test_an_unknown_document_is_not_found(backlog: Env) -> None:
    item = _create(backlog)

    missing = _delete(backlog, item, "TASK-001_spec.md")

    assert (missing.status_code, missing.json()["code"]) == (400, "document_not_found")


def test_the_documents_of_an_item_in_the_trash_cannot_be_deleted(backlog: Env) -> None:
    item = _create(backlog)
    _spec(backlog, item)
    version = _detail(backlog, item)["version"]
    backlog.client.delete(f"/api/workspace/elements/{item['uid']}", params={"version": version, "cascade": False})

    refused = _delete(backlog, item, "TASK-001_spec.md")

    assert refused.json()["code"] == "item_deleted"
    assert _names(backlog, item) == ["TASK-001_spec.md"]

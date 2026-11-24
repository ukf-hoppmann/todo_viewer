"""Notiz- und Spec-Dokumente löschen (STORY-094): sie gehen in den Papierkorb und lassen sich von dort zurückholen."""

from __future__ import annotations

from typing import Any

from workspace_env import Env

BASE = {"title": "Ein Item", "goal": "Ziel", "completion_criteria": "Kriterien"}


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


# --- Papierkorb: auflisten, wiederherstellen, endgültig löschen ---------------------------------------------------


def _trash(env: Env) -> list[dict[str, Any]]:
    return env.client.get("/api/workspace/trash").json()  # type: ignore[no-any-return]


def _content(env: Env, item: dict[str, Any], name: str) -> str:
    return str(env.client.get(f"/api/backlog/items/{item['uid']}/documents/{name}").json()["content"])


def _restore(env: Env, uid: str) -> Any:
    return env.client.post("/api/workspace/trash/restore", json={"uids": [uid]})


def _trash_item(env: Env, item: dict[str, Any]) -> None:
    version = _detail(env, item)["version"]
    env.client.delete(f"/api/workspace/elements/{item['uid']}", params={"version": version, "cascade": False})


def test_a_deleted_document_shows_up_in_the_trash_with_its_item(backlog: Env) -> None:
    item = _create(backlog)
    _spec(backlog, item)

    _delete(backlog, item, "TASK-001_spec.md")

    [entry] = _trash(backlog)
    assert (entry["kind"], entry["label"], entry["title"], entry["owner_uid"]) == (
        "document",
        "TASK-001",
        "TASK-001_spec.md",
        item["uid"],
    )


def test_restoring_a_spec_brings_the_text_back(backlog: Env) -> None:
    item = _create(backlog)
    _spec(backlog, item)
    _delete(backlog, item, "TASK-001_spec.md")
    [entry] = _trash(backlog)

    restored = _restore(backlog, entry["uid"])

    assert restored.json() == {"uids": [entry["uid"]]}
    assert _content(backlog, item, "TASK-001_spec.md") == "# Spec\n"
    assert _trash(backlog) == []


def test_restoring_the_notes_brings_back_head_entries_and_summary(backlog: Env) -> None:
    item = _create(backlog)
    _note(backlog, item, summary="Kurzfassung", state="Der Kopf")
    _note(backlog, item, topic="Zweites", discussed=["Mehr"])
    before = _content(backlog, item, "TASK-001_notes.md")
    head = backlog.client.get(f"/api/backlog/items/{item['uid']}/notes/state").json()
    version = backlog.client.get(f"/api/backlog/items/{item['uid']}/documents/TASK-001_notes.md").json()["version"]
    _delete(backlog, item, "TASK-001_notes.md", version)
    [entry] = _trash(backlog)

    _restore(backlog, entry["uid"])

    assert _content(backlog, item, "TASK-001_notes.md") == before
    again = backlog.client.get(f"/api/backlog/items/{item['uid']}/notes/state").json()
    assert (again["content"], again["stamp"], again["state"]) == (head["content"], head["stamp"], head["state"])
    detail = _detail(backlog, item)
    assert (detail["summary"], detail["notes"]) == ("Kurzfassung", ["TASK-001_notes.md"])


def test_restoring_is_refused_when_the_name_is_taken_again(backlog: Env) -> None:
    item = _create(backlog)
    _spec(backlog, item)
    _delete(backlog, item, "TASK-001_spec.md")
    _spec(backlog, item)
    [entry] = _trash(backlog)

    refused = _restore(backlog, entry["uid"])

    assert (refused.status_code, refused.json()["code"]) == (400, "document_exists")
    assert len(_trash(backlog)) == 1


def test_restoring_notes_is_refused_when_the_item_has_new_notes(backlog: Env) -> None:
    item = _create(backlog)
    _note(backlog, item, summary="Alt")
    _delete(backlog, item, "TASK-001_notes.md")
    _note(backlog, item, topic="Neu", summary="Neu")
    [entry] = _trash(backlog)

    refused = _restore(backlog, entry["uid"])

    assert (refused.status_code, refused.json()["code"]) == (400, "document_exists")
    assert _detail(backlog, item)["summary"] == "Neu"


def test_restoring_is_refused_while_the_item_is_in_the_trash(backlog: Env) -> None:
    item = _create(backlog)
    _spec(backlog, item)
    _delete(backlog, item, "TASK-001_spec.md")
    _trash_item(backlog, item)
    entry = next(e for e in _trash(backlog) if e["kind"] == "document")

    refused = _restore(backlog, entry["uid"])

    assert (refused.status_code, refused.json()["code"]) == (400, "item_deleted")
    assert any(e["kind"] == "document" for e in _trash(backlog))


def test_purging_removes_the_snapshot_for_good_after_a_backup(backlog: Env) -> None:
    item = _create(backlog)
    _spec(backlog, item)
    _delete(backlog, item, "TASK-001_spec.md")
    [entry] = _trash(backlog)

    purged = backlog.client.post("/api/workspace/trash/purge", json={"uids": [entry["uid"]]})

    assert purged.json() == {"uids": [entry["uid"]]}
    assert _trash(backlog) == []
    assert len(sorted((backlog.tmp_path / "backups").glob("*-purge.db"))) == 1
    assert _restore(backlog, entry["uid"]).status_code == 404


def test_purging_an_item_takes_its_deleted_documents_with_it(backlog: Env) -> None:
    item = _create(backlog)
    _spec(backlog, item)
    _delete(backlog, item, "TASK-001_spec.md")
    _trash_item(backlog, item)

    backlog.client.post("/api/workspace/trash/purge", json={"uids": [item["uid"]]})

    assert _trash(backlog) == []


def test_the_trash_filters_documents_by_text(backlog: Env) -> None:
    item = _create(backlog)
    _spec(backlog, item)
    _spec(backlog, item, "TASK-001_spec_api.md")
    _delete(backlog, item, "TASK-001_spec.md")
    _delete(backlog, item, "TASK-001_spec_api.md")

    found = backlog.client.get("/api/workspace/trash", params={"query": "spec_api"}).json()

    assert [e["title"] for e in found] == ["TASK-001_spec_api.md"]

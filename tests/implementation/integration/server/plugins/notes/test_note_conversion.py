from __future__ import annotations

from typing import Any

from notes_api import NOTES, item, link, links, new_item, new_note, note, project, set_status
from workspace_env import Env

FIELDS = {"area": "Server", "goal": "Das Ziel", "completion_criteria": "Die Kriterien"}


def _promote(env: Env, entry: dict[str, Any], **body: Any) -> Any:
    payload = {"version": entry["version"], "type": "Task", "fields": FIELDS, **body}
    return env.client.post(f"{NOTES}/notes/{entry['uid']}/promote", json=payload)


def _origin(env: Env, uid: str) -> list[dict[str, Any]]:
    return [entry for entry in links(env, uid)["outgoing"] if entry["role"] == "origin"]


def _note_with_documents(env: Env) -> dict[str, Any]:
    entry = new_note(env, "Eine gute Idee", body="Erste Zeile\n\nZweite Zeile")
    base = f"{NOTES}/notes/{entry['uid']}/documents"
    env.client.post(f"{NOTES}/notes/{entry['uid']}/entries", json={"topic": "Gespräch", "decided": ["Machen"]})
    env.client.put(f"{base}/{entry['label']}_spec_api.md", json={"content": "# Spec\n\nAPI"})
    return note(env, entry["uid"])


def test_promote_creates_the_item_links_it_and_closes_the_note(notes: Env) -> None:
    entry = _note_with_documents(notes)

    result = _promote(notes, entry)

    assert result.status_code == 200, result.text
    body = result.json()
    promoted = body["note"]
    assert (promoted["status"], promoted["archived"]) == ("promoted", True)
    created = item(notes, body["item_uid"])
    assert (created["type"], created["status"], created["title"], created["summary"]) == (
        "Task",
        "Open",
        "Eine gute Idee",
        "Eine gute Idee",
    )
    assert (created["area"], created["goal"], created["completion_criteria"]) == ("Server", "Das Ziel", "Die Kriterien")
    assert [o["uid"] for o in _origin(notes, entry["uid"])] == [body["item_uid"]]


def test_promote_takes_over_text_notes_and_specs(notes: Env) -> None:
    entry = _note_with_documents(notes)

    body = _promote(notes, entry).json()

    created = item(notes, body["item_uid"])
    label = created["label"]
    assert created["notes"] == [f"{label}_notes.md"] and created["spec"] == [f"{label}_spec_api.md"]
    document = notes.client.get(f"/api/backlog/items/{body['item_uid']}/documents/{label}_notes.md").json()["content"]
    assert document.startswith(f"# {label} — Eine gute Idee\n")
    assert f"Aus Note {entry['label']} befördert" in document
    assert "- Erste Zeile" in document and "- Zweite Zeile" in document
    assert "## 2026-10-16 — Gespräch" in document and "- Machen" in document
    spec = notes.client.get(f"/api/backlog/items/{body['item_uid']}/documents/{label}_spec_api.md").json()["content"]
    assert spec == "# Spec\n\nAPI"


def test_given_fields_win_over_the_summary_of_the_note(notes: Env) -> None:
    entry = new_note(notes, "Kurz")

    body = _promote(
        notes, entry, type="Story", fields={**FIELDS, "title": "Ein besserer Titel", "priority": "Urgent"}
    ).json()

    created = item(notes, body["item_uid"])
    assert (created["type"], created["title"], created["priority"], created["summary"]) == (
        "Story",
        "Ein besserer Titel",
        "Urgent",
        "Kurz",
    )


def test_a_refused_item_changes_nothing(notes: Env) -> None:
    entry = new_note(notes)

    refused = _promote(notes, entry, fields={"area": "Server"})

    assert refused.status_code in (400, 422)
    assert note(notes, entry["uid"])["stored_status"] == "waiting"
    assert _origin(notes, entry["uid"]) == []
    assert notes.client.get("/api/backlog/items").json() == []


def test_a_stale_version_or_a_closed_note_cannot_be_promoted(notes: Env) -> None:
    entry = new_note(notes)
    stale = _promote(notes, entry, version=entry["version"] + 5)
    assert (stale.status_code, stale.json()["code"]) == (409, "version_conflict")
    first = _promote(notes, entry)
    assert first.status_code == 200
    again = _promote(notes, note(notes, entry["uid"]))
    assert again.json()["code"] == "note_archived"


def test_repeating_a_promotion_that_stopped_halfway_creates_no_second_item(notes: Env) -> None:
    entry = new_note(notes, "Halb fertig", body="Text")
    first = _promote(notes, entry).json()
    # Zustand nach einem Abbruch vor dem Schließen der Note: die Note ist wieder offen, das Item und `origin` sind da
    reopened = notes.client.post(
        f"{NOTES}/notes/{entry['uid']}/restore", json={"version": first["note"]["version"]}
    ).json()

    second = _promote(notes, reopened)

    assert second.status_code == 200, second.text
    assert second.json()["item_uid"] == first["item_uid"]
    assert len(notes.client.get("/api/backlog/items").json()) == 1
    label = item(notes, first["item_uid"])["label"]
    document = notes.client.get(f"/api/backlog/items/{first['item_uid']}/documents/{label}_notes.md").json()["content"]
    assert document.count("befördert") == 1


def test_promote_is_refused_when_the_item_of_an_earlier_try_is_gone(notes: Env) -> None:
    entry = new_note(notes)
    ghost = new_item(notes)
    link(notes, entry["uid"], ghost["uid"], "origin")
    notes.client.request("DELETE", f"/api/workspace/elements/{ghost['uid']}", params={"version": ghost["version"]})

    refused = _promote(notes, entry)

    assert refused.json()["code"] == "promote_origin_missing"


def test_the_new_item_is_not_told_that_its_note_was_promoted_but_other_references_are(notes: Env) -> None:
    entry, other = new_note(notes, "Mit Verweis"), new_item(notes)
    link(notes, entry["uid"], other["uid"])

    body = _promote(notes, entry).json()

    assert [n["kind"] for n in notes.client.get(f"{NOTES}/items/{other['uid']}/notices").json()] == ["note_promoted"]
    assert notes.client.get(f"{NOTES}/items/{body['item_uid']}/notices").json() == []


def _demote(env: Env, target: dict[str, Any], **body: Any) -> Any:
    current = item(env, target["uid"])
    payload = {"version": current["version"], **body}
    return env.client.post(f"{NOTES}/items/{target['uid']}/demote", json=payload)


def test_demote_turns_an_open_item_into_a_note_and_rejects_the_item(notes: Env) -> None:
    target = new_item(notes, title="Ein Task", summary="Kurz")
    base = f"/api/backlog/items/{target['uid']}/documents"
    notes.client.put(
        f"{base}/{target['label']}_notes.md", json={"content": f"# {target['label']} — Ein Task\n", "summary": "Kurz"}
    )
    notes.client.put(f"{base}/{target['label']}_spec.md", json={"content": "Spec"})

    result = _demote(notes, target)

    assert result.status_code == 200, result.text
    body = result.json()
    created = body["note"]
    assert (created["summary"], created["body"], created["status"]) == ("Ein Task", "Kurz", "waiting")
    assert created["documents"] == [f"{created['label']}_notes.md", f"{created['label']}_spec.md"]
    assert [o["uid"] for o in _origin(notes, created["uid"])] == [target["uid"]]
    rejected = item(notes, target["uid"])
    assert (rejected["status"], rejected["resolution"]) == ("Rejected", "zur Notiz zurückgestuft")
    spec = notes.client.get(f"{NOTES}/notes/{created['uid']}/documents/{created['label']}_spec.md").json()
    assert spec["content"] == "Spec"


def test_demote_can_put_the_note_into_a_topic(notes: Env) -> None:
    topic = notes.client.post(f"{NOTES}/topics", json={"project": project(notes), "name": "Zurück"}).json()
    target = new_item(notes)

    created = _demote(notes, target, topic=topic["uid"]).json()["note"]

    assert created["topic_uid"] == topic["uid"]


def test_demote_is_refused_for_items_that_are_not_open_or_in_use(notes: Env) -> None:
    started = new_item(notes)
    set_status(notes, started, "In progress")
    assert _demote(notes, started).json()["code"] == "demote_not_open"

    epic = new_item(notes, "Epic")
    child = new_item(notes, "Story", parent=epic["uid"], required_for_parent=True)
    assert _demote(notes, epic).json()["code"] == "demote_has_children"

    needed = new_item(notes)
    dependent = new_item(notes, dependencies=[needed["uid"]])
    assert _demote(notes, needed).json()["code"] == "demote_referenced"

    for entry in (started, epic, needed):
        assert item(notes, entry["uid"])["status"] != "Rejected"
    assert notes.client.get(f"{NOTES}/index").json()["notes"] == []
    assert child and dependent


def test_demote_refuses_a_stale_version_and_an_unknown_item(notes: Env) -> None:
    target = new_item(notes)
    stale = notes.client.post(f"{NOTES}/items/{target['uid']}/demote", json={"version": target["version"] + 9})
    assert (stale.status_code, stale.json()["code"]) == (409, "version_conflict")
    assert notes.client.post(f"{NOTES}/items/gibt-es-nicht/demote", json={"version": 1}).status_code == 404


def test_demote_by_label_with_the_project(notes: Env) -> None:
    target = new_item(notes)

    result = notes.client.post(
        f"{NOTES}/items/{target['label']}/demote",
        json={"version": item(notes, target["uid"])["version"], "project": project(notes)},
    )

    assert result.status_code == 200, result.text


def test_repeating_a_demotion_that_stopped_halfway_creates_no_second_note(notes: Env) -> None:
    target = new_item(notes, title="Halb zurück")
    first = _demote(notes, target).json()
    # Zustand nach einem Abbruch vor dem Ablehnen des Items: das Item ist wieder offen, Note und `origin` sind da
    current = item(notes, target["uid"])
    reopened = notes.client.put(
        f"/api/backlog/items/{target['uid']}",
        json={"version": current["version"], "fields": {"status": "Open"}, "resolution": None},
    )
    assert reopened.status_code == 200, reopened.text

    second = _demote(notes, target)

    assert second.status_code == 200, second.text
    assert second.json()["note"]["uid"] == first["note"]["uid"]
    assert len(notes.client.get(f"{NOTES}/index").json()["notes"]) == 1

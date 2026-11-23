from __future__ import annotations

from typing import Any

from memos_api import NOTES, item, link, links, memo, new_item, new_memo, project, set_status
from workspace_env import Env

FIELDS = {"area": "Server", "goal": "Das Ziel", "completion_criteria": "Die Kriterien"}


def _promote(env: Env, entry: dict[str, Any], **body: Any) -> Any:
    payload = {"version": entry["version"], "type": "Task", "fields": FIELDS, **body}
    return env.client.post(f"{NOTES}/memos/{entry['uid']}/promote", json=payload)


def _origin(env: Env, uid: str) -> list[dict[str, Any]]:
    return [entry for entry in links(env, uid)["outgoing"] if entry["role"] == "origin"]


def _memo_with_documents(env: Env) -> dict[str, Any]:
    entry = new_memo(env, "Eine gute Idee", body="Erste Zeile\n\nZweite Zeile")
    base = f"{NOTES}/memos/{entry['uid']}/documents"
    env.client.post(f"{NOTES}/memos/{entry['uid']}/entries", json={"topic": "Gespräch", "decided": ["Machen"]})
    env.client.put(f"{base}/{entry['label']}_spec_api.md", json={"content": "# Spec\n\nAPI"})
    return memo(env, entry["uid"])


def test_promote_creates_the_item_links_it_and_closes_the_memo(memos: Env) -> None:
    entry = _memo_with_documents(memos)

    result = _promote(memos, entry)

    assert result.status_code == 200, result.text
    body = result.json()
    promoted = body["memo"]
    assert (promoted["status"], promoted["archived"]) == ("promoted", True)
    created = item(memos, body["item_uid"])
    assert (created["type"], created["status"], created["title"], created["summary"]) == (
        "Task",
        "Open",
        "Eine gute Idee",
        "Eine gute Idee",
    )
    assert (created["area"], created["goal"], created["completion_criteria"]) == ("Server", "Das Ziel", "Die Kriterien")
    assert [o["uid"] for o in _origin(memos, entry["uid"])] == [body["item_uid"]]


def test_promote_works_without_area(memos: Env) -> None:
    entry = new_memo(memos)

    result = _promote(memos, entry, fields={"goal": "Das Ziel", "completion_criteria": "Die Kriterien"})

    assert result.status_code == 200, result.text
    assert item(memos, result.json()["item_uid"])["area"] is None


def test_promote_takes_over_text_memos_and_specs(memos: Env) -> None:
    entry = _memo_with_documents(memos)

    body = _promote(memos, entry).json()

    created = item(memos, body["item_uid"])
    label = created["label"]
    assert created["notes"] == [f"{label}_notes.md"] and created["spec"] == [f"{label}_spec_api.md"]
    document = memos.client.get(f"/api/backlog/items/{body['item_uid']}/documents/{label}_notes.md").json()["content"]
    assert document.startswith(f"# {label} — Eine gute Idee\n")
    assert f"Aus Memo {entry['label']} befördert" in document
    assert "- Erste Zeile" in document and "- Zweite Zeile" in document
    assert "## 2026-10-16 — Gespräch" in document and "- Machen" in document
    spec = memos.client.get(f"/api/backlog/items/{body['item_uid']}/documents/{label}_spec_api.md").json()["content"]
    assert spec == "# Spec\n\nAPI"


def test_given_fields_win_over_the_summary_of_the_memo(memos: Env) -> None:
    entry = new_memo(memos, "Kurz")

    body = _promote(
        memos, entry, type="Story", fields={**FIELDS, "title": "Ein besserer Titel", "priority": "Urgent"}
    ).json()

    created = item(memos, body["item_uid"])
    assert (created["type"], created["title"], created["priority"], created["summary"]) == (
        "Story",
        "Ein besserer Titel",
        "Urgent",
        "Kurz",
    )


def test_a_refused_item_changes_nothing(memos: Env) -> None:
    entry = new_memo(memos)

    refused = _promote(memos, entry, fields={"goal": "Das Ziel"})

    assert refused.status_code in (400, 422)
    assert memo(memos, entry["uid"])["stored_status"] == "waiting"
    assert _origin(memos, entry["uid"]) == []
    assert memos.client.get("/api/backlog/items").json() == []


def test_a_stale_version_or_a_closed_memo_cannot_be_promoted(memos: Env) -> None:
    entry = new_memo(memos)
    stale = _promote(memos, entry, version=entry["version"] + 5)
    assert (stale.status_code, stale.json()["code"]) == (409, "version_conflict")
    first = _promote(memos, entry)
    assert first.status_code == 200
    again = _promote(memos, memo(memos, entry["uid"]))
    assert again.json()["code"] == "memo_archived"


def test_repeating_a_promotion_that_stopped_halfway_creates_no_second_item(memos: Env) -> None:
    entry = new_memo(memos, "Halb fertig", body="Text")
    first = _promote(memos, entry).json()
    # Zustand nach einem Abbruch vor dem Schließen des Memos: das Memo ist wieder offen, das Item und `origin` sind da
    reopened = memos.client.post(
        f"{NOTES}/memos/{entry['uid']}/restore", json={"version": first["memo"]["version"]}
    ).json()

    second = _promote(memos, reopened)

    assert second.status_code == 200, second.text
    assert second.json()["item_uid"] == first["item_uid"]
    assert len(memos.client.get("/api/backlog/items").json()) == 1
    label = item(memos, first["item_uid"])["label"]
    document = memos.client.get(f"/api/backlog/items/{first['item_uid']}/documents/{label}_notes.md").json()["content"]
    assert document.count("befördert") == 1


def test_promote_is_refused_when_the_item_of_an_earlier_try_is_gone(memos: Env) -> None:
    entry = new_memo(memos)
    ghost = new_item(memos)
    link(memos, entry["uid"], ghost["uid"], "origin")
    memos.client.request("DELETE", f"/api/workspace/elements/{ghost['uid']}", params={"version": ghost["version"]})

    refused = _promote(memos, entry)

    assert refused.json()["code"] == "promote_origin_missing"


def test_the_new_item_is_not_told_that_its_memo_was_promoted_but_other_references_are(memos: Env) -> None:
    entry, other = new_memo(memos, "Mit Verweis"), new_item(memos)
    link(memos, entry["uid"], other["uid"])

    body = _promote(memos, entry).json()

    assert [n["kind"] for n in memos.client.get(f"{NOTES}/items/{other['uid']}/hints").json()] == ["memo_promoted"]
    assert memos.client.get(f"{NOTES}/items/{body['item_uid']}/hints").json() == []


def _demote(env: Env, target: dict[str, Any], **body: Any) -> Any:
    current = item(env, target["uid"])
    payload = {"version": current["version"], **body}
    return env.client.post(f"{NOTES}/items/{target['uid']}/demote", json=payload)


def test_demote_turns_an_open_item_into_a_memo_and_rejects_the_item(memos: Env) -> None:
    target = new_item(memos, title="Ein Task", summary="Kurz")
    base = f"/api/backlog/items/{target['uid']}/documents"
    memos.client.put(
        f"{base}/{target['label']}_notes.md", json={"content": f"# {target['label']} — Ein Task\n", "summary": "Kurz"}
    )
    memos.client.put(f"{base}/{target['label']}_spec.md", json={"content": "Spec"})

    result = _demote(memos, target)

    assert result.status_code == 200, result.text
    body = result.json()
    created = body["memo"]
    assert (created["summary"], created["body"], created["status"]) == ("Ein Task", "Kurz", "waiting")
    assert created["documents"] == [f"{created['label']}_notes.md", f"{created['label']}_spec.md"]
    assert [o["uid"] for o in _origin(memos, created["uid"])] == [target["uid"]]
    rejected = item(memos, target["uid"])
    assert (rejected["status"], rejected["resolution"]) == ("Rejected", "zur Notiz zurückgestuft")
    spec = memos.client.get(f"{NOTES}/memos/{created['uid']}/documents/{created['label']}_spec.md").json()
    assert spec["content"] == "Spec"


def test_demote_can_put_the_memo_into_a_topic(memos: Env) -> None:
    topic = memos.client.post(f"{NOTES}/topics", json={"project": project(memos), "name": "Zurück"}).json()
    target = new_item(memos)

    created = _demote(memos, target, topic=topic["uid"]).json()["memo"]

    assert created["topic_uid"] == topic["uid"]


def test_demote_is_refused_for_items_that_are_not_open_or_in_use(memos: Env) -> None:
    started = new_item(memos)
    set_status(memos, started, "In progress")
    assert _demote(memos, started).json()["code"] == "demote_not_open"

    epic = new_item(memos, "Epic")
    child = new_item(memos, "Story", parent=epic["uid"], required_for_parent=True)
    assert _demote(memos, epic).json()["code"] == "demote_has_children"

    needed = new_item(memos)
    dependent = new_item(memos, dependencies=[needed["uid"]])
    assert _demote(memos, needed).json()["code"] == "demote_referenced"

    for entry in (started, epic, needed):
        assert item(memos, entry["uid"])["status"] != "Rejected"
    assert memos.client.get(f"{NOTES}/index").json()["memos"] == []
    assert child and dependent


def test_demote_refuses_a_stale_version_and_an_unknown_item(memos: Env) -> None:
    target = new_item(memos)
    stale = memos.client.post(f"{NOTES}/items/{target['uid']}/demote", json={"version": target["version"] + 9})
    assert (stale.status_code, stale.json()["code"]) == (409, "version_conflict")
    assert memos.client.post(f"{NOTES}/items/gibt-es-nicht/demote", json={"version": 1}).status_code == 404


def test_demote_by_label_with_the_project(memos: Env) -> None:
    target = new_item(memos)

    result = memos.client.post(
        f"{NOTES}/items/{target['label']}/demote",
        json={"version": item(memos, target["uid"])["version"], "project": project(memos)},
    )

    assert result.status_code == 200, result.text


def test_repeating_a_demotion_that_stopped_halfway_creates_no_second_memo(memos: Env) -> None:
    target = new_item(memos, title="Halb zurück")
    first = _demote(memos, target).json()
    # Zustand nach einem Abbruch vor dem Ablehnen des Items: das Item ist wieder offen, Memo und `origin` sind da
    current = item(memos, target["uid"])
    reopened = memos.client.put(
        f"/api/backlog/items/{target['uid']}",
        json={"version": current["version"], "fields": {"status": "Open"}, "resolution": None},
    )
    assert reopened.status_code == 200, reopened.text

    second = _demote(memos, target)

    assert second.status_code == 200, second.text
    assert second.json()["memo"]["uid"] == first["memo"]["uid"]
    assert len(memos.client.get(f"{NOTES}/index").json()["memos"]) == 1

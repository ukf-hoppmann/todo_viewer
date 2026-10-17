from __future__ import annotations

from typing import Any

from notes_api import (
    NOTES,
    decide,
    item,
    link,
    links,
    new_item,
    new_note,
    note,
    set_status,
)
from workspace_env import Env


def _referencing(env: Env) -> tuple[dict[str, Any], dict[str, Any]]:
    entry, target = new_note(env, "Verweist"), new_item(env)
    link(env, entry["uid"], target["uid"])
    return entry, target


def _complete(env: Env, target: dict[str, Any]) -> None:
    for status in ("In progress", "Awaiting confirmation"):
        set_status(env, target, status)
    set_status(env, target, "Completed", "Fertig")


def _notice(env: Env, uid: str) -> dict[str, Any]:
    notices = note(env, uid)["notices"]
    assert len(notices) == 1, notices
    return notices[0]  # type: ignore[no-any-return]


def test_a_completed_item_tells_the_notes_that_refer_to_it(notes: Env) -> None:
    entry, target = _referencing(notes)

    _complete(notes, target)

    shown = note(notes, entry["uid"])
    assert (shown["status"], shown["reason"]) == ("due", "notice")
    notice = shown["notices"][0]
    assert (notice["kind"], notice["source"]["uid"], notice["decisions"]) == (
        "item_completed",
        target["uid"],
        ["keep", "detach", "drop", "promote"],
    )


def test_a_rejected_item_tells_them_too_and_in_progress_does_not(notes: Env) -> None:
    entry, target = _referencing(notes)
    set_status(notes, target, "In progress")
    assert note(notes, entry["uid"])["notices"] == []

    set_status(notes, target, "Rejected", "Nein")

    assert _notice(notes, entry["uid"])["kind"] == "item_rejected"


def test_an_open_notice_of_the_same_cause_stays_the_only_one(notes: Env) -> None:
    entry, target = _referencing(notes)
    _complete(notes, target)
    set_status(notes, target, "In progress")
    set_status(notes, target, "Awaiting confirmation")
    set_status(notes, target, "Completed", "Noch einmal")

    assert len(note(notes, entry["uid"])["notices"]) == 1


def test_a_note_without_a_reference_or_in_the_archive_is_not_told(notes: Env) -> None:
    plain, target = new_note(notes, "Ohne Verweis"), new_item(notes)
    closed = new_note(notes, "Abgeschlossen")
    link(notes, closed["uid"], target["uid"])
    notes.client.post(f"{NOTES}/notes/{closed['uid']}/finish", json={"version": closed["version"], "status": "done"})
    link(notes, plain["uid"], target["uid"], "origin")

    _complete(notes, target)

    assert note(notes, plain["uid"])["notices"] == []
    assert note(notes, closed["uid"])["notices"] == []


def test_a_deleted_item_tells_the_notes(notes: Env) -> None:
    entry, target = _referencing(notes)

    notes.client.request("DELETE", f"/api/workspace/elements/{target['uid']}", params={"version": target["version"]})

    assert _notice(notes, entry["uid"])["kind"] == "item_deleted"


def test_a_retyped_item_tells_the_notes(notes: Env) -> None:
    entry, target = _referencing(notes)
    story = new_item(notes, "Story")
    notes.client.put(
        f"/api/backlog/items/{target['uid']}",
        json={"version": target["version"], "fields": {"parent": story["uid"]}, "resolution": None},
    )
    current = item(notes, target["uid"])
    retyped = notes.client.post(
        f"/api/backlog/items/{target['uid']}/retype", json={"version": current["version"], "type": "Story"}
    )
    assert retyped.status_code == 200, retyped.text

    assert any(n["kind"] == "item_retyped" for n in note(notes, entry["uid"])["notices"])


def test_keep_moves_the_review_date_and_decides_the_notice(notes: Env) -> None:
    entry, target = _referencing(notes)
    _complete(notes, target)
    notice = _notice(notes, entry["uid"])

    decided = decide(notes, notice["uid"], "keep")

    assert decided.status_code == 200, decided.text
    result = decided.json()
    assert result["note"]["notices"] == [] and result["note"]["status"] == "waiting"
    assert result["note"]["review_at"].startswith("2026-11-15")


def test_detach_removes_the_reference_to_the_item(notes: Env) -> None:
    entry, target = _referencing(notes)
    _complete(notes, target)

    decided = decide(notes, _notice(notes, entry["uid"])["uid"], "detach")

    assert decided.status_code == 200, decided.text
    assert links(notes, entry["uid"])["outgoing"] == []
    assert decided.json()["note"]["status"] == "waiting"


def test_drop_archives_the_note_and_decides_the_notice(notes: Env) -> None:
    entry, target = _referencing(notes)
    _complete(notes, target)

    decided = decide(notes, _notice(notes, entry["uid"])["uid"], "drop").json()

    assert (decided["note"]["status"], decided["note"]["archived"], decided["note"]["notices"]) == ("dropped", True, [])


def test_a_decision_must_fit_the_side_and_a_notice_is_decided_once(notes: Env) -> None:
    entry, target = _referencing(notes)
    _complete(notes, target)
    uid = _notice(notes, entry["uid"])["uid"]

    assert decide(notes, uid, "acknowledge").status_code == 422
    assert decide(notes, uid, "keep").status_code == 200
    again = decide(notes, uid, "keep")
    assert (again.status_code, again.json()["code"]) == (400, "notice_decided")
    assert decide(notes, "gibt-es-nicht", "keep").status_code == 404


def test_a_failing_decision_leaves_the_notice_open(notes: Env) -> None:
    entry, target = _referencing(notes)
    _complete(notes, target)
    uid = _notice(notes, entry["uid"])["uid"]

    refused = decide(notes, uid, "promote", type="Task", fields={})

    assert refused.status_code in (400, 422)
    assert _notice(notes, entry["uid"])["uid"] == uid
    assert note(notes, entry["uid"])["stored_status"] == "waiting"


def test_promote_as_a_decision_creates_the_item_and_decides_the_notice(notes: Env) -> None:
    entry, target = _referencing(notes)
    _complete(notes, target)
    uid = _notice(notes, entry["uid"])["uid"]

    decided = decide(
        notes, uid, "promote", type="Task", fields={"area": "Server", "goal": "Ziel", "completion_criteria": "K"}
    )

    assert decided.status_code == 200, decided.text
    assert decided.json()["note"]["status"] == "promoted"
    assert decided.json()["notice"]["decisions"] == ["keep", "detach", "drop", "promote"]
    origin = [entry for entry in links(notes, entry["uid"])["outgoing"] if entry["role"] == "origin"]
    assert len(origin) == 1


def test_a_dropped_note_tells_the_items_it_refers_to_and_they_can_acknowledge(notes: Env) -> None:
    entry, target = _referencing(notes)
    dropped = notes.client.post(
        f"{NOTES}/notes/{entry['uid']}/finish", json={"version": entry["version"], "status": "dropped"}
    )
    assert dropped.status_code == 200

    listed = notes.client.get(f"{NOTES}/items/{target['uid']}/notices").json()

    assert [(n["kind"], n["source"]["uid"], n["decisions"]) for n in listed] == [
        ("note_dropped", entry["uid"], ["acknowledge"])
    ]
    decided = decide(notes, listed[0]["uid"], "acknowledge")
    assert decided.status_code == 200 and decided.json()["note"] is None
    assert notes.client.get(f"{NOTES}/items/{target['uid']}/notices").json() == []


def test_a_done_note_tells_nobody(notes: Env) -> None:
    entry, target = _referencing(notes)

    notes.client.post(f"{NOTES}/notes/{entry['uid']}/finish", json={"version": entry["version"], "status": "done"})

    assert notes.client.get(f"{NOTES}/items/{target['uid']}/notices").json() == []


def test_item_notices_can_be_asked_by_label_with_the_project(notes: Env) -> None:
    entry, target = _referencing(notes)
    notes.client.post(f"{NOTES}/notes/{entry['uid']}/finish", json={"version": entry["version"], "status": "dropped"})
    project_uid = str(notes.general()["uid"])

    by_label = notes.client.get(f"{NOTES}/items/{target['label']}/notices", params={"project": project_uid})

    assert len(by_label.json()) == 1
    assert notes.client.get(f"{NOTES}/items/gibt-es-nicht/notices").status_code == 404

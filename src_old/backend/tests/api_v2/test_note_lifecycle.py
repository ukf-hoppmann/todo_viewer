"""Lifecycle of notes through API v2: triggers, finish, snooze, trash, restore; no purge over HTTP."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tests.api_v2.conftest import BASE, OTHER_BASE


def _note(api, summary: str = "an idea", **extra) -> dict:
    resp = api.post(f"{BASE}/notes", {"summary": summary, **extra})
    assert resp.status_code == 201, resp.body
    return resp.body


def _at(days: float) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


def _story(api) -> str:
    """A story in the project `demo`; returns its label."""
    source = next(s for s in api.get("/api/v2/sources").body if s["project"] == "demo")
    resp = api.post("/api/v2/items", {"source_id": source["id"], "type": "Story", "title": "Watched", "area": "Core",
                                      "goal": "A goal.", "completion_criteria": "Checked."})
    assert resp.status_code == 201, resp.body
    return resp.body["id"]


def _set_status(api, label: str, status: str) -> None:
    source = next(s for s in api.get("/api/v2/sources").body if s["project"] == "demo")
    item = api.get(f"/api/v2/items/{source['id']}/{label}").body
    resp = api.patch(f"/api/v2/items/{source['id']}/{label}", {"version": item["version"],
                                                               "fields": {"status": status}})
    assert resp.status_code == 200, resp.body


# ---------- triggers ----------

def test_a_time_trigger_in_the_past_makes_the_note_due_and_removing_it_makes_it_wait(notes_api):
    _note(notes_api)
    added = notes_api.post(f"{BASE}/notes/NOTE-001/triggers", {"kind": "time", "at": _at(-1)})
    assert added.status_code == 201, added.body
    assert (added.body["status"], added.body["reason"]) == ("due", "trigger")
    trigger = added.body["triggers"][0]
    assert (trigger["kind"], trigger["id"] > 0) == ("time", True)

    removed = notes_api.delete(f"{BASE}/notes/NOTE-001/triggers/{trigger['id']}")
    assert removed.status_code == 200
    assert (removed.body["status"], removed.body["triggers"]) == ("waiting", [])


def test_a_future_trigger_leaves_the_note_waiting(notes_api):
    _note(notes_api)
    added = notes_api.post(f"{BASE}/notes/NOTE-001/triggers", {"kind": "time", "at": _at(2)})
    assert (added.body["status"], len(added.body["triggers"])) == ("waiting", 1)


def test_a_topic_trigger_needs_a_topic_and_arrives_with_its_due_date(notes_api):
    _note(notes_api)
    no_topic = notes_api.post(f"{BASE}/notes/NOTE-001/triggers", {"kind": "topic_due"})
    assert no_topic.body["code"] == "value_required"
    topic = notes_api.post(f"{BASE}/topics", {"name": "Ideas", "due_at": _at(-1)}).body
    note = notes_api.get(f"{BASE}/notes/NOTE-001").body
    notes_api.patch(f"{BASE}/notes/NOTE-001", {"version": note["version"], "topic": topic["label"]})
    added = notes_api.post(f"{BASE}/notes/NOTE-001/triggers", {"kind": "topic_due"})
    assert (added.body["status"], added.body["reason"]) == ("due", "topic_due")


def test_an_event_trigger_fires_when_the_item_reaches_the_status(notes_api):
    story = _story(notes_api)
    _note(notes_api)
    added = notes_api.post(f"{BASE}/notes/NOTE-001/triggers", {
        "kind": "event", "target": story, "target_status": "In progress"})
    assert added.status_code == 201, added.body
    assert (added.body["status"], added.body["triggers"][0]["target"]) == ("waiting", story)
    assert added.body["triggers"][0]["target_project"] == "demo"

    _set_status(notes_api, story, "In progress")
    due = notes_api.get(f"{BASE}/notes/NOTE-001").body
    assert (due["status"], due["reason"]) == ("due", "trigger")
    assert due["triggers"][0]["fired_at"] is not None


def test_an_event_that_has_already_happened_is_marked_so(notes_api):
    story = _story(notes_api)
    _set_status(notes_api, story, "In progress")
    _note(notes_api)
    added = notes_api.post(f"{BASE}/notes/NOTE-001/triggers", {
        "kind": "event", "target": story, "target_status": "In progress"})
    assert (added.body["triggers"][0]["already_met"], added.body["status"]) == (True, "due")


def test_a_trigger_with_missing_or_wrong_values_is_refused(notes_api):
    story = _story(notes_api)
    _note(notes_api)
    url = f"{BASE}/notes/NOTE-001/triggers"
    assert notes_api.post(url, {"kind": "time"}).body["code"] == "value_required"
    assert notes_api.post(url, {"kind": "time", "at": "2027-01-01T00:00:00"}).status_code == 400
    assert notes_api.post(url, {"kind": "alarm"}).status_code == 400
    assert notes_api.post(url, {"kind": "event", "target_status": "Completed"}).body["code"] == "value_required"
    wrong_status = notes_api.post(url, {"kind": "event", "target": story, "target_status": "Open"})
    assert (wrong_status.status_code, wrong_status.body["code"]) == (400, "invalid_value")
    missing_item = notes_api.post(url, {"kind": "event", "target": "STORY-099", "target_status": "Completed"})
    assert (missing_item.status_code, missing_item.body["code"]) == (404, "item_not_found")
    assert notes_api.get(f"{BASE}/notes/NOTE-001").body["triggers"] == []


def test_removing_an_unknown_trigger_is_not_found(notes_api):
    _note(notes_api)
    missing = notes_api.delete(f"{BASE}/notes/NOTE-001/triggers/99")
    assert (missing.status_code, missing.body["code"]) == (404, "trigger_not_found")


# ---------- finish ----------

def test_a_note_is_finished_as_done_or_dropped_and_then_closed_for_changes(notes_api):
    done, dropped = _note(notes_api, "a"), _note(notes_api, "b")
    finished = notes_api.post(f"{BASE}/notes/{done['label']}/finish", {"version": done["version"], "status": "done"})
    assert finished.status_code == 200, finished.body
    assert (finished.body["status"], finished.body["archived"]) == ("done", True)
    gone = notes_api.post(f"{BASE}/notes/{dropped['label']}/finish", {"version": dropped["version"],
                                                                      "status": "dropped"})
    assert gone.body["status"] == "dropped"

    closed = notes_api.patch(f"{BASE}/notes/{done['label']}", {"version": finished.body["version"], "summary": "x"})
    assert (closed.status_code, closed.body["code"]) == (409, "note_closed")
    again = notes_api.post(f"{BASE}/notes/{done['label']}/finish", {"version": finished.body["version"],
                                                                    "status": "dropped"})
    assert again.body["code"] == "note_closed"
    trigger = notes_api.post(f"{BASE}/notes/{done['label']}/triggers", {"kind": "time", "at": _at(1)})
    assert trigger.body["code"] == "note_closed"


def test_finishing_needs_done_or_dropped_and_the_current_version(notes_api):
    note = _note(notes_api)
    url = f"{BASE}/notes/NOTE-001/finish"
    assert notes_api.post(url, {"version": note["version"], "status": "waiting"}).status_code == 400
    # a note is promoted by the promotion workflow, not by closing it by hand
    assert notes_api.post(url, {"version": note["version"], "status": "promoted"}).status_code == 400
    stale = notes_api.post(url, {"version": "0000", "status": "done"})
    assert (stale.status_code, stale.body["code"]) == (409, "version_conflict")


# ---------- snooze ----------

def test_snoozing_a_due_note_sets_a_new_review_date(notes_api):
    note = _note(notes_api, review_at=_at(-1))
    assert note["status"] == "due"
    snoozed = notes_api.post(f"{BASE}/notes/NOTE-001/snooze", {"version": note["version"], "review_at": _at(7)})
    assert snoozed.status_code == 200, snoozed.body
    assert (snoozed.body["status"], snoozed.body["stored_status"]) == ("snoozed", "snoozed")
    assert timedelta(days=6) < datetime.fromisoformat(snoozed.body["review_at"]) - datetime.now(UTC)


def test_snoozing_with_a_new_trigger_replaces_the_old_ones(notes_api):
    note = _note(notes_api)
    notes_api.post(f"{BASE}/notes/NOTE-001/triggers", {"kind": "time", "at": _at(-1)})
    due = notes_api.get(f"{BASE}/notes/NOTE-001").body
    assert due["status"] == "due"

    snoozed = notes_api.post(f"{BASE}/notes/NOTE-001/snooze", {
        "version": due["version"], "trigger": {"kind": "time", "at": _at(3)}})
    assert snoozed.status_code == 200, snoozed.body
    assert snoozed.body["status"] == "snoozed"
    assert [t["kind"] for t in snoozed.body["triggers"]] == ["time"]
    assert datetime.fromisoformat(snoozed.body["triggers"][0]["at"]) > datetime.now(UTC)
    assert note["label"] == "NOTE-001"


def test_snoozing_without_a_trigger_drops_the_triggers_that_have_passed(notes_api):
    _note(notes_api)
    notes_api.post(f"{BASE}/notes/NOTE-001/triggers", {"kind": "time", "at": _at(-1)})
    due = notes_api.get(f"{BASE}/notes/NOTE-001").body
    snoozed = notes_api.post(f"{BASE}/notes/NOTE-001/snooze", {"version": due["version"]})
    assert (snoozed.body["status"], snoozed.body["triggers"]) == ("snoozed", [])


def test_a_bad_trigger_stops_the_snooze_before_anything_changes(notes_api):
    note = _note(notes_api)
    refused = notes_api.post(f"{BASE}/notes/NOTE-001/snooze", {
        "version": note["version"], "trigger": {"kind": "time"}})
    assert refused.body["code"] == "value_required"
    assert notes_api.get(f"{BASE}/notes/NOTE-001").body == note


def test_snoozing_with_a_stale_version_is_a_conflict(notes_api):
    note = _note(notes_api)
    stale = notes_api.post(f"{BASE}/notes/NOTE-001/snooze", {"version": "0000"})
    assert (stale.status_code, stale.body["code"]) == (409, "version_conflict")
    assert notes_api.get(f"{BASE}/notes/NOTE-001").body == note


# ---------- trash and restore ----------

def test_a_note_goes_to_the_trash_and_comes_back_waiting(notes_api):
    note = _note(notes_api, review_at=_at(-1))
    deleted = notes_api.delete(f"{BASE}/notes/NOTE-001")
    assert deleted.status_code == 200
    assert deleted.body["deleted"] is not None

    trash = notes_api.get(f"{BASE}/trash").body
    assert [n["label"] for n in trash["notes"]] == ["NOTE-001"]
    assert notes_api.get(f"{BASE}/trash").body["topics"] == []
    assert notes_api.delete(f"{BASE}/notes/NOTE-001").body["code"] == "note_deleted"
    change = notes_api.patch(f"{BASE}/notes/NOTE-001", {"version": deleted.body["version"], "summary": "x"})
    assert change.body["code"] == "note_deleted"

    restored = notes_api.post(f"{BASE}/notes/NOTE-001/restore", {})
    assert restored.status_code == 200, restored.body
    assert (restored.body["deleted"], restored.body["status"]) == (None, "waiting")
    assert restored.body["review_at"] != note["review_at"]
    assert notes_api.get(f"{BASE}/trash").body == {"topics": [], "notes": []}


def test_a_finished_note_is_restored_from_the_archive(notes_api):
    note = _note(notes_api)
    notes_api.post(f"{BASE}/notes/NOTE-001/finish", {"version": note["version"], "status": "done"})
    restored = notes_api.post(f"{BASE}/notes/NOTE-001/restore", {})
    assert (restored.body["status"], restored.body["archived"]) == ("waiting", False)
    nothing = notes_api.post(f"{BASE}/notes/NOTE-001/restore", {})
    assert (nothing.status_code, nothing.body["code"]) == (409, "note_not_restorable")


def test_deleting_a_topic_with_cascade_puts_its_notes_in_the_trash_too(notes_api):
    topic = notes_api.post(f"{BASE}/topics", {"name": "Ideas"}).body
    _note(notes_api, topic=topic["label"])
    refused = notes_api.delete(f"{BASE}/topics/{topic['label']}")
    assert (refused.status_code, refused.body["code"]) == (409, "topic_has_content")
    gone = notes_api.delete(f"{BASE}/topics/{topic['label']}", cascade="true")
    assert [n["label"] for n in gone.body["notes"]] == ["NOTE-001"]
    assert notes_api.post(f"{BASE}/notes/NOTE-001/restore", {}).body["code"] == "topic_deleted"
    back = notes_api.post(f"{BASE}/topics/{topic['label']}/restore", {})
    assert back.body["notes"] == []
    assert notes_api.get(f"{BASE}/notes/NOTE-001").body["deleted"] is None


def test_the_trash_is_per_project(notes_api):
    _note(notes_api)
    notes_api.delete(f"{BASE}/notes/NOTE-001")
    assert notes_api.get(f"{OTHER_BASE}/trash").body == {"topics": [], "notes": []}


def test_there_is_no_way_to_purge_over_http(notes_api):
    _note(notes_api)
    notes_api.delete(f"{BASE}/notes/NOTE-001")
    for path in (f"{BASE}/trash/NOTE-001", f"{BASE}/notes/NOTE-001/purge", f"{BASE}/trash"):
        assert notes_api.delete(path).status_code in (404, 405)
        assert notes_api.post(path, {}).status_code in (404, 405)
    schema = notes_api.get("/openapi.json").body
    assert not [p for p in schema["paths"] if "purge" in p]
    assert [n["label"] for n in notes_api.get(f"{BASE}/trash").body["notes"]] == ["NOTE-001"]

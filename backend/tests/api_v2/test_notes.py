"""Notes through API v2: create, read, change, keep, move to another project; version conflicts."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tests.api_v2.conftest import BASE, OTHER_BASE


def _note(api, summary: str = "an idea", **extra) -> dict:
    resp = api.post(f"{BASE}/notes", {"summary": summary, **extra})
    assert resp.status_code == 201, resp.body
    return resp.body


def _in(days: float) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


def test_a_note_is_created_with_a_review_date_and_read_back(notes_api):
    note = _note(notes_api, body="details")
    assert note["label"] == "NOTE-001"
    assert (note["summary"], note["body"], note["project"]) == ("an idea", "details", "demo")
    assert (note["status"], note["stored_status"], note["reason"]) == ("waiting", "waiting", None)
    assert (note["triggers"], note["trigger_mode"], note["archived"], note["deleted"]) == ([], "any", False, None)
    review = datetime.fromisoformat(note["review_at"])
    assert timedelta(days=29) < review - datetime.now(UTC) < timedelta(days=31)

    assert notes_api.get(f"{BASE}/notes/NOTE-001").body == note


def test_a_note_can_start_with_topic_review_date_and_mode(notes_api):
    topic = notes_api.post(f"{BASE}/topics", {"name": "Ideas"}).body
    note = _note(notes_api, topic=topic["label"], review_at=_in(3), trigger_mode="all")
    assert (note["topic"], note["trigger_mode"]) == ("TOPIC-001", "all")
    assert timedelta(days=2) < datetime.fromisoformat(note["review_at"]) - datetime.now(UTC) < timedelta(days=4)


def test_a_note_is_due_when_its_review_date_has_passed(notes_api):
    note = _note(notes_api, review_at=_in(-1))
    assert (note["status"], note["stored_status"], note["reason"]) == ("due", "waiting", "review_expired")


def test_creating_with_bad_input_is_refused(notes_api):
    assert notes_api.post(f"{BASE}/notes", {"summary": "  "}).body["code"] == "value_required"
    assert notes_api.post(f"{BASE}/notes", {"summary": "x", "topic": "TOPIC-009"}).body["code"] == "topic_not_found"
    assert notes_api.post(f"{BASE}/notes", {"summary": "x", "review_at": "2027-01-01T00:00:00"}).status_code == 400
    assert notes_api.post(f"{BASE}/notes", {"summary": "x", "trigger_mode": "some"}).status_code == 400
    missing = notes_api.post("/api/v2/projects/nope/notes", {"summary": "x"})
    assert (missing.status_code, missing.body["code"]) == (404, "source_gone")


def test_an_unknown_note_is_not_found(notes_api):
    missing = notes_api.get(f"{BASE}/notes/NOTE-009")
    assert (missing.status_code, missing.body["code"]) == (404, "note_not_found")


def test_a_note_is_changed_and_the_version_moves_on(notes_api):
    note = _note(notes_api, body="details")
    topic = notes_api.post(f"{BASE}/topics", {"name": "Ideas"}).body

    edited = notes_api.patch(f"{BASE}/notes/NOTE-001", {
        "version": note["version"], "summary": "better", "topic": topic["label"], "trigger_mode": "all"})
    assert edited.status_code == 200, edited.body
    assert (edited.body["summary"], edited.body["topic"], edited.body["trigger_mode"]) == ("better", "TOPIC-001", "all")
    assert edited.body["body"] == "details"  # not sent, not changed
    assert edited.body["version"] != note["version"]

    cleared = notes_api.patch(f"{BASE}/notes/NOTE-001", {
        "version": edited.body["version"], "topic": None, "body": None, "review_at": None})
    assert (cleared.body["topic"], cleared.body["body"], cleared.body["review_at"]) == (None, None, None)


def test_a_changed_text_moves_the_review_date_unless_one_is_given(notes_api):
    note = _note(notes_api, review_at=_in(3))
    same = notes_api.patch(f"{BASE}/notes/NOTE-001", {"version": note["version"], "trigger_mode": "all"}).body
    assert same["review_at"] == note["review_at"]
    moved = notes_api.patch(f"{BASE}/notes/NOTE-001", {"version": same["version"], "summary": "new"}).body
    assert timedelta(days=29) < datetime.fromisoformat(moved["review_at"]) - datetime.now(UTC)
    given = notes_api.patch(f"{BASE}/notes/NOTE-001", {
        "version": moved["version"], "summary": "newer", "review_at": _in(5)}).body
    assert datetime.fromisoformat(given["review_at"]) - datetime.now(UTC) < timedelta(days=6)


def test_a_stale_version_is_a_conflict(notes_api):
    note = _note(notes_api)
    first = notes_api.patch(f"{BASE}/notes/NOTE-001", {"version": note["version"], "summary": "first"})
    assert first.status_code == 200
    stale = notes_api.patch(f"{BASE}/notes/NOTE-001", {"version": note["version"], "summary": "second"})
    assert (stale.status_code, stale.body["code"]) == (409, "version_conflict")
    assert notes_api.get(f"{BASE}/notes/NOTE-001").body["summary"] == "first"


def test_a_change_needs_a_version_and_a_known_field(notes_api):
    note = _note(notes_api)
    assert notes_api.patch(f"{BASE}/notes/NOTE-001", {"summary": "x"}).status_code == 400
    assert notes_api.patch(f"{BASE}/notes/NOTE-001", {"version": note["version"], "colour": "red"}).status_code == 400
    assert notes_api.patch(f"{BASE}/notes/NOTE-001", {
        "version": note["version"], "topic": "TOPIC-009"}).body["code"] == "topic_not_found"
    assert notes_api.patch(f"{BASE}/notes/NOTE-001", {
        "version": note["version"], "summary": " "}).body["code"] == "value_required"


def test_keeping_a_note_moves_only_the_review_date(notes_api):
    note = _note(notes_api, review_at=_in(-2))
    assert note["status"] == "due"
    kept = notes_api.post(f"{BASE}/notes/NOTE-001/keep", {"version": note["version"]})
    assert kept.status_code == 200, kept.body
    assert (kept.body["status"], kept.body["summary"]) == ("waiting", "an idea")
    assert timedelta(days=29) < datetime.fromisoformat(kept.body["review_at"]) - datetime.now(UTC)
    stale = notes_api.post(f"{BASE}/notes/NOTE-001/keep", {"version": note["version"]})
    assert stale.body["code"] == "version_conflict"


def test_a_note_moves_to_another_project_with_a_new_label(notes_api):
    topic = notes_api.post(f"{OTHER_BASE}/topics", {"name": "Imported"}).body
    note = _note(notes_api, body="details")

    moved = notes_api.post(f"{BASE}/notes/NOTE-001/move", {
        "version": note["version"], "project": "other", "topic": topic["label"]})
    assert moved.status_code == 200, moved.body
    assert (moved.body["project"], moved.body["label"], moved.body["topic"]) == ("other", "NOTE-001", "TOPIC-001")
    assert (moved.body["summary"], moved.body["body"]) == ("an idea", "details")

    old = notes_api.get(f"{BASE}/notes/NOTE-001").body
    assert old["deleted"] is not None
    assert notes_api.get(f"{OTHER_BASE}/notes/NOTE-001").body["summary"] == "an idea"
    assert _note(notes_api, "next")["label"] == "NOTE-002"  # the label of the old note is never reused


def test_moving_is_refused_for_the_same_or_an_unknown_project_and_a_stale_version(notes_api):
    note = _note(notes_api)
    same = notes_api.post(f"{BASE}/notes/NOTE-001/move", {"version": note["version"], "project": "demo"})
    assert (same.status_code, same.body["code"]) == (409, "note_same_project")
    nowhere = notes_api.post(f"{BASE}/notes/NOTE-001/move", {"version": note["version"], "project": "nope"})
    assert (nowhere.status_code, nowhere.body["code"]) == (404, "source_gone")
    stale = notes_api.post(f"{BASE}/notes/NOTE-001/move", {"version": "0000", "project": "other"})
    assert (stale.status_code, stale.body["code"]) == (409, "version_conflict")
    wrong_topic = notes_api.post(f"{BASE}/notes/NOTE-001/move", {
        "version": note["version"], "project": "other", "topic": "TOPIC-009"})
    assert wrong_topic.body["code"] == "topic_not_found"
    assert notes_api.get(f"{BASE}/notes/NOTE-001").body["deleted"] is None  # nothing happened

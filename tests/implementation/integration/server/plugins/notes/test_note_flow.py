from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from viewer.core.domain.events import Event
from workspace_env import Env

API = "/api/notes"


def _project(env: Env) -> str:
    return str(env.general()["uid"])


def _create(env: Env, summary: str = "Idee", **fields: Any) -> dict[str, Any]:
    response = env.client.post(
        f"{API}/notes", json={"project": _project(env), "fields": {"summary": summary, **fields}}
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _act(env: Env, note: dict[str, Any], action: str, **body: Any) -> Any:
    return env.client.post(f"{API}/notes/{note['uid']}/{action}", json={"version": note["version"], **body})


def test_a_new_note_waits_with_a_label_and_a_review_date(notes: Env) -> None:
    note = _create(notes, "  Erste Idee  ", body="Langtext")
    assert note["label"] == "NOTE-001"
    assert (note["summary"], note["status"], note["archived"]) == ("Erste Idee", "waiting", False)
    assert note["review_at"].startswith("2026-11-15")  # 2026-10-16 + 30 Tage
    assert notes.client.get(f"{API}/notes/{note['uid']}").json()["body"] == "Langtext"


def test_a_label_needs_the_project_to_be_resolved(notes: Env) -> None:
    note = _create(notes)
    found = notes.client.get(f"{API}/notes/{note['label']}", params={"project": _project(notes)})
    assert found.json()["uid"] == note["uid"]
    assert notes.client.get(f"{API}/notes/{note['label']}").status_code == 422


def test_a_summary_is_required_and_unknown_fields_are_refused(notes: Env) -> None:
    project = _project(notes)
    for fields in ({}, {"summary": "  "}, {"summary": "x", "colour": "red"}, {"summary": "x", "trigger_mode": "some"}):
        response = notes.client.post(f"{API}/notes", json={"project": project, "fields": fields})
        assert response.status_code == 422, fields


def test_editing_a_text_moves_the_review_date_but_a_given_date_wins(notes: Env) -> None:
    note = _create(notes)
    notes.clock.advance(timedelta(days=10))
    edited = notes.client.put(
        f"{API}/notes/{note['uid']}", json={"version": note["version"], "fields": {"body": "neu"}}
    )
    assert edited.json()["review_at"].startswith("2026-11-25")
    again = notes.client.put(
        f"{API}/notes/{note['uid']}",
        json={"version": edited.json()["version"], "fields": {"body": "x", "review_at": "2027-01-01"}},
    )
    assert again.json()["review_at"].startswith("2027-01-01")


def test_a_stale_version_is_a_conflict(notes: Env) -> None:
    note = _create(notes)
    first = notes.client.put(f"{API}/notes/{note['uid']}", json={"version": note["version"], "fields": {"body": "a"}})
    assert first.status_code == 200
    stale = notes.client.put(f"{API}/notes/{note['uid']}", json={"version": note["version"], "fields": {"body": "b"}})
    assert (stale.status_code, stale.json()["code"]) == (409, "version_conflict")


def test_a_note_becomes_due_when_its_date_comes(notes: Env) -> None:
    note = _create(notes)
    assert notes.client.get(f"{API}/due").json() == {"count": 0, "notes": []}
    notes.clock.advance(timedelta(days=31))
    due = notes.client.get(f"{API}/due").json()
    assert (due["count"], due["notes"][0]["label"]) == (1, "NOTE-001")
    assert due["notes"][0]["due_since"] == due["notes"][0]["review_at"]
    shown = notes.client.get(f"{API}/notes/{note['uid']}").json()
    assert (shown["status"], shown["stored_status"]) == ("due", "waiting")


def test_the_next_review_date_is_scheduled_and_announced_as_notes_due(notes: Env) -> None:
    def pending() -> datetime | None:
        return notes.app.state.scheduler.pending_at("notes")  # type: ignore[no-any-return]

    seen: list[Event] = []
    notes.app.state.events.subscribe("notes.due", seen.append)
    assert pending() is None

    first = _create(notes, "Später")
    soon = _create(notes, "Bald", review_at="2026-10-20T08:00:00Z")
    assert pending() == datetime.fromisoformat("2026-10-20T08:00:00+00:00")

    notes.client.put(f"{API}/notes/{soon['uid']}", json={"version": soon["version"], "fields": {"review_at": None}})
    assert pending() == datetime.fromisoformat(first["review_at"])

    notes.clock.advance(timedelta(days=31))
    notes.notes.due_watch.fire()
    assert [event.topic for event in seen] == ["notes.due"]
    assert pending() is None


def test_keep_snooze_and_finish_lead_through_the_lifecycle(notes: Env) -> None:
    note = _create(notes)
    notes.clock.advance(timedelta(days=31))
    kept = _act(notes, note, "keep").json()
    assert (kept["status"], kept["review_at"][:10]) == ("waiting", "2026-12-16")
    snoozed = _act(notes, kept, "snooze", review_at="2027-03-01").json()
    assert (snoozed["status"], snoozed["review_at"][:10]) == ("snoozed", "2027-03-01")
    finished = _act(notes, snoozed, "finish", status="done").json()
    assert (finished["status"], finished["archived"]) == ("done", True)
    refused = _act(notes, finished, "keep")
    assert (refused.status_code, refused.json()["code"]) == (400, "note_archived")


def test_a_finished_note_comes_back_to_waiting(notes: Env) -> None:
    note = _create(notes)
    done = _act(notes, note, "finish", status="dropped").json()
    back = _act(notes, done, "restore").json()
    assert (back["status"], back["archived"]) == ("waiting", False)
    assert _act(notes, back, "restore").json()["code"] == "note_not_archived"


def test_only_done_and_dropped_can_be_chosen_from_outside(notes: Env) -> None:
    note = _create(notes)
    assert _act(notes, note, "finish", status="promoted").status_code == 422


def test_the_index_filters_by_status_and_text_with_the_derived_status(notes: Env) -> None:
    first = _create(notes, "Alpha")
    _create(notes, "Beta")
    _act(notes, first, "finish", status="done")
    notes.clock.advance(timedelta(days=31))
    everything = notes.client.get(f"{API}/index").json()
    assert {n["summary"]: n["status"] for n in everything["notes"]} == {"Alpha": "done", "Beta": "due"}
    only_due = notes.client.get(f"{API}/index", params={"statuses": "due"}).json()["notes"]
    assert [n["summary"] for n in only_due] == ["Beta"]
    by_text = notes.client.get(f"{API}/index", params={"query": "alp"}).json()["notes"]
    assert [n["summary"] for n in by_text] == ["Alpha"]
    assert notes.client.get(f"{API}/index", params={"statuses": "nope"}).status_code == 422


def test_deleting_a_note_uses_the_trash_of_the_workspace(notes: Env) -> None:
    note = _create(notes)
    deleted = notes.client.request(
        "DELETE", f"/api/workspace/elements/{note['uid']}", params={"version": note["version"]}
    )
    assert deleted.status_code == 200, deleted.text
    assert notes.client.get(f"{API}/index").json()["notes"] == []
    assert notes.client.get(f"{API}/notes/{note['uid']}").json()["deleted"] is True
    assert _act(notes, note, "keep").status_code in (400, 409)
    restored = notes.client.post("/api/workspace/trash/restore", json={"uids": [note["uid"]]})
    assert restored.status_code == 200, restored.text
    assert [n["uid"] for n in notes.client.get(f"{API}/index").json()["notes"]] == [note["uid"]]


def test_documents_follow_the_naming_rules_and_versions(notes: Env) -> None:
    note = _create(notes, "Doku")
    base = f"{API}/notes/{note['uid']}/documents"
    created = notes.client.put(f"{base}/NOTE-001_notes.md", json={"content": "# NOTE-001\n"})
    assert (created.status_code, created.json()["kind"], created.json()["version"]) == (200, "notes", 1)
    assert notes.client.put(f"{base}/NOTE-001_notes.md", json={"content": "x"}).json()["code"] == "document_exists"
    assert notes.client.put(f"{base}/other.md", json={"content": "x"}).status_code == 422
    replaced = notes.client.put(f"{base}/NOTE-001_notes.md", json={"content": "neu", "version": 1})
    assert replaced.json()["version"] == 2
    stale = notes.client.put(f"{base}/NOTE-001_notes.md", json={"content": "alt", "version": 1})
    assert stale.status_code == 409
    notes.client.put(f"{base}/NOTE-001_spec_api.md", json={"content": "s"})
    names = [(d["name"], d["kind"]) for d in notes.client.get(base).json()]
    assert names == [("NOTE-001_notes.md", "notes"), ("NOTE-001_spec_api.md", "spec")]
    assert notes.client.get(f"{base}/NOTE-001_notes.md").json()["content"] == "neu"
    assert notes.client.get(f"{base}/missing.md").json()["code"] == "document_not_found"
    assert notes.client.get(f"{API}/notes/{note['uid']}").json()["documents"] == [
        "NOTE-001_notes.md",
        "NOTE-001_spec_api.md",
    ]


def test_notes_entries_are_appended_to_the_notes_document(notes: Env) -> None:
    note = _create(notes, "Doku")
    url = f"{API}/notes/{note['uid']}/entries"
    first = notes.client.post(url, json={"topic": "Start", "discussed": ["a"]}).json()
    assert first["content"].startswith("# NOTE-001 — Doku\n\n## 2026-10-16 — Start")
    second = notes.client.post(url, json={"topic": "Weiter", "decided": ["b"]}).json()
    assert second["version"] == 2 and "## 2026-10-16 — Weiter" in second["content"]
    assert notes.client.post(url, json={"topic": "Leer"}).status_code == 422


def test_a_finished_note_refuses_document_changes_but_can_still_be_read(notes: Env) -> None:
    note = _create(notes)
    base = f"{API}/notes/{note['uid']}/documents"
    notes.client.put(f"{base}/NOTE-001_notes.md", json={"content": "x"})
    _act(notes, note, "finish", status="done")
    refused = notes.client.put(f"{base}/NOTE-001_spec.md", json={"content": "y"})
    assert (refused.status_code, refused.json()["code"]) == (400, "note_archived")
    assert notes.client.get(f"{base}/NOTE-001_notes.md").status_code == 200


def test_settings_change_the_review_interval_for_new_notes(notes: Env) -> None:
    assert notes.client.get(f"{API}/settings").json() == {"max_topic_depth": 3, "review_days": 30}
    changed = notes.client.put(f"{API}/settings", json={"review_days": 7})
    assert changed.json() == {"max_topic_depth": 3, "review_days": 7}
    assert _create(notes)["review_at"].startswith("2026-10-23")
    assert notes.client.put(f"{API}/settings", json={"max_topic_depth": 0}).status_code == 422

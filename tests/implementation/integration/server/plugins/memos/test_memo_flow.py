from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from viewer.core.domain.events import Event
from workspace_env import Env

API = "/api/memos"


def _project(env: Env) -> str:
    return str(env.general()["uid"])


def _create(env: Env, summary: str = "Idee", **fields: Any) -> dict[str, Any]:
    response = env.client.post(
        f"{API}/memos", json={"project": _project(env), "fields": {"summary": summary, **fields}}
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _act(env: Env, memo: dict[str, Any], action: str, **body: Any) -> Any:
    return env.client.post(f"{API}/memos/{memo['uid']}/{action}", json={"version": memo["version"], **body})


def test_a_new_memo_waits_with_a_label_and_a_review_date(memos: Env) -> None:
    memo = _create(memos, "  Erste Idee  ", body="Langtext")
    assert memo["label"] == "MEMO-001"
    assert (memo["summary"], memo["status"], memo["archived"]) == ("Erste Idee", "waiting", False)
    assert memo["review_at"].startswith("2026-11-15")  # 2026-10-16 + 30 Tage
    assert memos.client.get(f"{API}/memos/{memo['uid']}").json()["body"] == "Langtext"


def test_a_label_needs_the_project_to_be_resolved(memos: Env) -> None:
    memo = _create(memos)
    found = memos.client.get(f"{API}/memos/{memo['label']}", params={"project": _project(memos)})
    assert found.json()["uid"] == memo["uid"]
    assert memos.client.get(f"{API}/memos/{memo['label']}").status_code == 422


def test_a_summary_is_required_and_unknown_fields_are_refused(memos: Env) -> None:
    project = _project(memos)
    for fields in ({}, {"summary": "  "}, {"summary": "x", "colour": "red"}, {"summary": "x", "trigger_mode": "some"}):
        response = memos.client.post(f"{API}/memos", json={"project": project, "fields": fields})
        assert response.status_code == 422, fields


def test_editing_a_text_moves_the_review_date_but_a_given_date_wins(memos: Env) -> None:
    memo = _create(memos)
    memos.clock.advance(timedelta(days=10))
    edited = memos.client.put(
        f"{API}/memos/{memo['uid']}", json={"version": memo["version"], "fields": {"body": "neu"}}
    )
    assert edited.json()["review_at"].startswith("2026-11-25")
    again = memos.client.put(
        f"{API}/memos/{memo['uid']}",
        json={"version": edited.json()["version"], "fields": {"body": "x", "review_at": "2027-01-01"}},
    )
    assert again.json()["review_at"].startswith("2027-01-01")


def test_a_stale_version_is_a_conflict(memos: Env) -> None:
    memo = _create(memos)
    first = memos.client.put(f"{API}/memos/{memo['uid']}", json={"version": memo["version"], "fields": {"body": "a"}})
    assert first.status_code == 200
    stale = memos.client.put(f"{API}/memos/{memo['uid']}", json={"version": memo["version"], "fields": {"body": "b"}})
    assert (stale.status_code, stale.json()["code"]) == (409, "version_conflict")


def test_a_memo_becomes_due_when_its_date_comes(memos: Env) -> None:
    memo = _create(memos)
    assert memos.client.get(f"{API}/due").json() == {"count": 0, "memos": []}
    memos.clock.advance(timedelta(days=31))
    due = memos.client.get(f"{API}/due").json()
    assert (due["count"], due["memos"][0]["label"]) == (1, "MEMO-001")
    assert due["memos"][0]["due_since"] == due["memos"][0]["review_at"]
    shown = memos.client.get(f"{API}/memos/{memo['uid']}").json()
    assert (shown["status"], shown["stored_status"]) == ("due", "waiting")


def test_the_next_review_date_is_scheduled_and_announced_as_memos_due(memos: Env) -> None:
    def pending() -> datetime | None:
        return memos.app.state.scheduler.pending_at("memos")  # type: ignore[no-any-return]

    seen: list[Event] = []
    memos.app.state.events.subscribe("memos.due", seen.append)
    assert pending() is None

    first = _create(memos, "Später")
    soon = _create(memos, "Bald", review_at="2026-10-20T08:00:00Z")
    assert pending() == datetime.fromisoformat("2026-10-20T08:00:00+00:00")

    memos.client.put(f"{API}/memos/{soon['uid']}", json={"version": soon["version"], "fields": {"review_at": None}})
    assert pending() == datetime.fromisoformat(first["review_at"])

    memos.clock.advance(timedelta(days=31))
    memos.memos.due_watch.fire()
    assert [event.topic for event in seen] == ["memos.due"]
    assert pending() is None


def test_keep_snooze_and_finish_lead_through_the_lifecycle(memos: Env) -> None:
    memo = _create(memos)
    memos.clock.advance(timedelta(days=31))
    kept = _act(memos, memo, "keep").json()
    assert (kept["status"], kept["review_at"][:10]) == ("waiting", "2026-12-16")
    snoozed = _act(memos, kept, "snooze", review_at="2027-03-01").json()
    assert (snoozed["status"], snoozed["review_at"][:10]) == ("snoozed", "2027-03-01")
    finished = _act(memos, snoozed, "finish", status="done").json()
    assert (finished["status"], finished["archived"]) == ("done", True)
    refused = _act(memos, finished, "keep")
    assert (refused.status_code, refused.json()["code"]) == (400, "memo_archived")


def test_a_finished_memo_comes_back_to_waiting(memos: Env) -> None:
    memo = _create(memos)
    done = _act(memos, memo, "finish", status="dropped").json()
    back = _act(memos, done, "restore").json()
    assert (back["status"], back["archived"]) == ("waiting", False)
    assert _act(memos, back, "restore").json()["code"] == "memo_not_archived"


def test_only_done_and_dropped_can_be_chosen_from_outside(memos: Env) -> None:
    memo = _create(memos)
    assert _act(memos, memo, "finish", status="promoted").status_code == 422


def test_the_index_filters_by_status_and_text_with_the_derived_status(memos: Env) -> None:
    first = _create(memos, "Alpha")
    _create(memos, "Beta")
    _act(memos, first, "finish", status="done")
    memos.clock.advance(timedelta(days=31))
    everything = memos.client.get(f"{API}/index").json()
    assert {n["summary"]: n["status"] for n in everything["memos"]} == {"Alpha": "done", "Beta": "due"}
    only_due = memos.client.get(f"{API}/index", params={"statuses": "due"}).json()["memos"]
    assert [n["summary"] for n in only_due] == ["Beta"]
    by_text = memos.client.get(f"{API}/index", params={"query": "alp"}).json()["memos"]
    assert [n["summary"] for n in by_text] == ["Alpha"]
    assert memos.client.get(f"{API}/index", params={"statuses": "nope"}).status_code == 422


def test_deleting_a_memo_uses_the_trash_of_the_workspace(memos: Env) -> None:
    memo = _create(memos)
    deleted = memos.client.request(
        "DELETE", f"/api/workspace/elements/{memo['uid']}", params={"version": memo["version"]}
    )
    assert deleted.status_code == 200, deleted.text
    assert memos.client.get(f"{API}/index").json()["memos"] == []
    assert memos.client.get(f"{API}/memos/{memo['uid']}").json()["deleted"] is True
    assert _act(memos, memo, "keep").status_code in (400, 409)
    restored = memos.client.post("/api/workspace/trash/restore", json={"uids": [memo["uid"]]})
    assert restored.status_code == 200, restored.text
    assert [n["uid"] for n in memos.client.get(f"{API}/index").json()["memos"]] == [memo["uid"]]


def test_documents_follow_the_naming_rules_and_versions(memos: Env) -> None:
    memo = _create(memos, "Doku")
    base = f"{API}/memos/{memo['uid']}/documents"
    created = memos.client.put(f"{base}/MEMO-001_notes.md", json={"content": "# MEMO-001\n"})
    assert (created.status_code, created.json()["kind"], created.json()["version"]) == (200, "notes", 1)
    assert memos.client.put(f"{base}/MEMO-001_notes.md", json={"content": "x"}).json()["code"] == "document_exists"
    assert memos.client.put(f"{base}/other.md", json={"content": "x"}).status_code == 422
    replaced = memos.client.put(f"{base}/MEMO-001_notes.md", json={"content": "neu", "version": 1})
    assert replaced.json()["version"] == 2
    stale = memos.client.put(f"{base}/MEMO-001_notes.md", json={"content": "alt", "version": 1})
    assert stale.status_code == 409
    memos.client.put(f"{base}/MEMO-001_spec_api.md", json={"content": "s"})
    names = [(d["name"], d["kind"]) for d in memos.client.get(base).json()]
    assert names == [("MEMO-001_notes.md", "notes"), ("MEMO-001_spec_api.md", "spec")]
    assert memos.client.get(f"{base}/MEMO-001_notes.md").json()["content"] == "neu"
    assert memos.client.get(f"{base}/missing.md").json()["code"] == "document_not_found"
    assert memos.client.get(f"{API}/memos/{memo['uid']}").json()["documents"] == [
        "MEMO-001_notes.md",
        "MEMO-001_spec_api.md",
    ]


def test_memos_entries_are_appended_to_the_memos_document(memos: Env) -> None:
    memo = _create(memos, "Doku")
    url = f"{API}/memos/{memo['uid']}/entries"
    first = memos.client.post(url, json={"topic": "Start", "discussed": ["a"]}).json()
    assert first["content"].startswith("# MEMO-001 — Doku\n\n## 2026-10-16 — Start")
    second = memos.client.post(url, json={"topic": "Weiter", "decided": ["b"]}).json()
    assert second["version"] == 2 and "## 2026-10-16 — Weiter" in second["content"]
    assert memos.client.post(url, json={"topic": "Leer"}).status_code == 422


def test_a_finished_memo_refuses_document_changes_but_can_still_be_read(memos: Env) -> None:
    memo = _create(memos)
    base = f"{API}/memos/{memo['uid']}/documents"
    memos.client.put(f"{base}/MEMO-001_notes.md", json={"content": "x"})
    _act(memos, memo, "finish", status="done")
    refused = memos.client.put(f"{base}/MEMO-001_spec.md", json={"content": "y"})
    assert (refused.status_code, refused.json()["code"]) == (400, "memo_archived")
    assert memos.client.get(f"{base}/MEMO-001_notes.md").status_code == 200


def test_settings_change_the_review_interval_for_new_memos(memos: Env) -> None:
    assert memos.client.get(f"{API}/settings").json() == {"max_topic_depth": 3, "review_days": 30}
    changed = memos.client.put(f"{API}/settings", json={"review_days": 7})
    assert changed.json() == {"max_topic_depth": 3, "review_days": 7}
    assert _create(memos)["review_at"].startswith("2026-10-23")
    assert memos.client.put(f"{API}/settings", json={"max_topic_depth": 0}).status_code == 422

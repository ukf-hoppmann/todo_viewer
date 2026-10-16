"""Notices through API v2: list them, decide them, and see them make a note due."""
from __future__ import annotations

from tests.api_v2.conftest import BASE
from tests.conftest import ApiClient
from todo_viewer.domain.notes import LinkTarget, NewNotice, NoticeCause, NoticeSide, TargetKind

NOTICES = "/api/v2/notices"


def _note(api: ApiClient, summary: str = "an idea") -> str:
    resp = api.post(f"{BASE}/notes", {"summary": summary})
    assert resp.status_code == 201, resp.body
    return str(resp.body["label"])


def _story(api: ApiClient) -> str:
    source = next(s for s in api.get("/api/v2/sources").body if s["project"] == "demo")
    resp = api.post("/api/v2/items", {"source_id": source["id"], "type": "Story", "title": "Linked", "area": "Core",
                                      "goal": "A goal.", "completion_criteria": "Checked."})
    assert resp.status_code == 201, resp.body
    return str(resp.body["id"])


def _link(api: ApiClient, label: str, item: str) -> None:
    resp = api.post(f"{BASE}/notes/{label}/links", {"kind": "item", "target": item})
    assert resp.status_code == 201, resp.body


def _add(api: ApiClient, new: NewNotice) -> None:
    """Notices arise from item changes (TASK-011, TASK-012); here the service is told directly."""
    api._raw.app.state.container.notes.add_notice(new)


def _item_changed(api: ApiClient, label: str, item: str = "STORY-001") -> None:
    _add(api, NewNotice(NoticeSide.NOTE, "demo", label, NoticeCause.ITEM_COMPLETED,
                        LinkTarget(TargetKind.ITEM, "demo", item)))


def _open(api: ApiClient, label: str) -> list[dict]:
    resp = api.get(NOTICES, project="demo", label=label, side="note", open="true")
    assert resp.status_code == 200, resp.body
    return list(resp.body)


def test_an_open_notice_is_listed_and_makes_the_note_due_with_all_four_actions(notes_api):
    label = _note(notes_api)
    _item_changed(notes_api, label)

    listed = _open(notes_api, label)
    due = notes_api.get("/api/v2/notes/due").body

    assert len(listed) == 1
    first = listed[0]
    assert (first["side"], first["project"], first["label"], first["cause"]) == (
        "note", "demo", label, "item_completed")
    assert first["counterpart"] == {"kind": "item", "project": "demo", "label": "STORY-001"}
    assert (first["decision"], first["decided_at"], first["created_at"] is not None) == (None, None, True)
    assert first["options"] == ["keep", "detach", "drop", "promote"]
    assert [(n["label"], n["reason"], n["actions"]) for n in due] == [
        (label, "notice", ["keep", "detach", "drop", "promote"])]
    assert notes_api.get("/api/v2/notes/due/count").body["count"] == 1


def test_the_note_lists_its_open_notices(notes_api):
    label = _note(notes_api)
    _item_changed(notes_api, label)

    body = notes_api.get(f"{BASE}/notes/{label}").body

    assert (body["status"], body["reason"]) == ("due", "notice")
    assert [n["cause"] for n in body["open_notices"]] == ["item_completed"]


def test_keep_closes_the_notice_and_the_note_is_no_longer_due(notes_api):
    label = _note(notes_api)
    story = _story(notes_api)
    _link(notes_api, label, story)
    _item_changed(notes_api, label, story)
    notice = _open(notes_api, label)[0]

    resp = notes_api.post(f"{NOTICES}/{notice['id']}/decision", {"decision": "keep"})

    assert resp.status_code == 200, resp.body
    assert (resp.body["notice"]["decision"], resp.body["notice"]["decided_at"] is not None) == ("keep", True)
    assert (resp.body["note"]["status"], resp.body["note"]["open_notices"]) == ("waiting", [])
    assert notes_api.get(f"{BASE}/notes/{label}/links").body[0]["target"] == story
    assert notes_api.get("/api/v2/notes/due/count").body["count"] == 0
    assert _open(notes_api, label) == []
    assert len(notes_api.get(NOTICES, project="demo", label=label, side="note").body) == 1  # still readable


def test_detach_removes_the_link(notes_api):
    label = _note(notes_api)
    story = _story(notes_api)
    _link(notes_api, label, story)
    _item_changed(notes_api, label, story)

    resp = notes_api.post(f"{NOTICES}/{_open(notes_api, label)[0]['id']}/decision", {"decision": "detach"})

    assert resp.status_code == 200, resp.body
    assert notes_api.get(f"{BASE}/notes/{label}/links").body == []
    assert resp.body["note"]["status"] == "waiting"


def test_drop_drops_the_note(notes_api):
    label = _note(notes_api)
    _item_changed(notes_api, label)

    resp = notes_api.post(f"{NOTICES}/{_open(notes_api, label)[0]['id']}/decision", {"decision": "drop"})

    assert resp.status_code == 200, resp.body
    assert (resp.body["note"]["stored_status"], resp.body["note"]["archived"]) == ("dropped", True)
    assert notes_api.get("/api/v2/notes/due/count").body["count"] == 0


def test_promote_is_refused_for_now_and_the_notice_stays_open(notes_api):
    label = _note(notes_api)
    _item_changed(notes_api, label)
    notice = _open(notes_api, label)[0]

    resp = notes_api.post(f"{NOTICES}/{notice['id']}/decision", {"decision": "promote"})

    assert (resp.status_code, resp.body["code"]) == (409, "decision_not_available")
    assert len(_open(notes_api, label)) == 1


def test_a_second_decision_is_refused(notes_api):
    label = _note(notes_api)
    _item_changed(notes_api, label)
    notice = _open(notes_api, label)[0]
    assert notes_api.post(f"{NOTICES}/{notice['id']}/decision", {"decision": "keep"}).status_code == 200

    resp = notes_api.post(f"{NOTICES}/{notice['id']}/decision", {"decision": "detach"})

    assert (resp.status_code, resp.body["code"]) == (409, "notice_already_decided")


def test_a_stale_version_is_a_conflict(notes_api):
    label = _note(notes_api)
    _item_changed(notes_api, label)
    notice = _open(notes_api, label)[0]

    resp = notes_api.post(f"{NOTICES}/{notice['id']}/decision", {"decision": "keep", "version": "0000"})

    assert resp.status_code == 409 and resp.body["code"] == "version_conflict"
    assert len(_open(notes_api, label)) == 1


def test_an_unknown_notice_is_not_found_and_an_unknown_decision_is_invalid(notes_api):
    label = _note(notes_api)
    _item_changed(notes_api, label)

    assert notes_api.post(f"{NOTICES}/404/decision", {"decision": "keep"}).status_code == 404
    unknown = notes_api.post(f"{NOTICES}/{_open(notes_api, label)[0]['id']}/decision", {"decision": "shrug"})
    assert (unknown.status_code, unknown.body["code"]) == (400, "bad_request")


def test_a_decision_of_the_wrong_side_is_invalid(notes_api):
    label = _note(notes_api)
    _item_changed(notes_api, label)

    resp = notes_api.post(f"{NOTICES}/{_open(notes_api, label)[0]['id']}/decision", {"decision": "acknowledge"})

    assert (resp.status_code, resp.body["code"]) == (400, "invalid_value")


def test_an_item_notice_is_acknowledged_and_never_makes_a_note_due(notes_api):
    label = _note(notes_api)
    _add(notes_api, NewNotice(NoticeSide.ITEM, "demo", "STORY-001", NoticeCause.NOTE_DROPPED,
                              LinkTarget(TargetKind.NOTE, "demo", label)))

    listed = notes_api.get(NOTICES, project="demo", label="STORY-001", side="item", open="true").body
    assert [(n["side"], n["cause"], n["options"]) for n in listed] == [("item", "note_dropped", ["acknowledge"])]
    assert notes_api.get("/api/v2/notes/due/count").body["count"] == 0

    resp = notes_api.post(f"{NOTICES}/{listed[0]['id']}/decision", {"decision": "acknowledge"})

    assert resp.status_code == 200, resp.body
    assert (resp.body["notice"]["decision"], resp.body["note"]) == ("acknowledge", None)
    assert notes_api.get(NOTICES, project="demo", label="STORY-001", side="item", open="true").body == []


def test_listing_the_notices_of_an_unknown_note_is_not_found(notes_api):
    assert notes_api.get(NOTICES, project="demo", label="NOTE-009", side="note").status_code == 404


# ---------- both directions through the real item and note routes ----------

def _complete(api: ApiClient, item: str) -> None:
    source = next(s for s in api.get("/api/v2/sources").body if s["project"] == "demo")
    current = api.get(f"/api/v2/items/{source['id']}/{item}").body
    resp = api.patch(f"/api/v2/items/{source['id']}/{item}",
                     {"version": current["version"], "fields": {"status": "Completed"}, "resolution": "done"})
    assert resp.status_code == 200, resp.body


def test_completing_the_item_tells_the_note_and_dropping_the_note_tells_the_item(notes_api):
    story = _story(notes_api)
    first, second = _note(notes_api), _note(notes_api, "second")
    _link(notes_api, first, story)
    _link(notes_api, second, story)

    _complete(notes_api, story)

    assert [n["cause"] for n in _open(notes_api, first)] == ["item_completed"]
    assert [n["cause"] for n in _open(notes_api, second)] == ["item_completed"]
    drop = notes_api.post(f"{NOTICES}/{_open(notes_api, first)[0]['id']}/decision", {"decision": "drop"})
    assert drop.status_code == 200, drop.body

    on_item = notes_api.get(NOTICES, project="demo", label=story, side="item", open="true").body
    assert [(n["cause"], n["counterpart"]["label"]) for n in on_item] == [("note_dropped", first)]
    linked = {n["label"]: n["status"] for n in notes_api.get(f"{BASE}/items/{story}/notes").body}
    assert linked == {first: "dropped", second: "due"}  # the UI sees both notes and their state at the item
    assert notes_api.get("/api/v2/notes/due/count").body["count"] == 1  # the item notice does not count
    acknowledge = notes_api.post(f"{NOTICES}/{on_item[0]['id']}/decision", {"decision": "acknowledge"})
    assert acknowledge.status_code == 200
    again = notes_api.post(f"{NOTICES}/{on_item[0]['id']}/decision", {"decision": "acknowledge"})
    assert (again.status_code, again.body["code"]) == (409, "notice_already_decided")


def test_finishing_a_note_as_dropped_or_done_through_the_note_route(notes_api):
    story = _story(notes_api)
    dropped, done = _note(notes_api), _note(notes_api, "done")
    _link(notes_api, dropped, story)
    _link(notes_api, done, story)

    for label, status in ((dropped, "dropped"), (done, "done")):
        version = notes_api.get(f"{BASE}/notes/{label}").body["version"]
        assert notes_api.post(f"{BASE}/notes/{label}/finish", {"version": version, "status": status}).status_code == 200

    on_item = notes_api.get(NOTICES, project="demo", label=story, side="item").body
    assert [(n["cause"], n["counterpart"]["label"]) for n in on_item] == [("note_dropped", dropped)]

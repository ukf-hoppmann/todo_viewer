"""Links of notes through API v2: set, remove, and ask in both directions."""
from __future__ import annotations

from tests.api_v2.conftest import BASE, OTHER_BASE


def _note(api, summary: str = "an idea", base: str = BASE, **extra) -> dict:
    resp = api.post(f"{base}/notes", {"summary": summary, **extra})
    assert resp.status_code == 201, resp.body
    return resp.body


def _source(api, project: str = "demo") -> dict:
    return next(s for s in api.get("/api/v2/sources").body if s["project"] == project)


def _item(api, project: str = "demo", type_: str = "Story") -> dict:
    resp = api.post("/api/v2/items", {"source_id": _source(api, project)["id"], "type": type_, "title": "Linked",
                                      "area": "Core", "goal": "A goal.", "completion_criteria": "Checked."})
    assert resp.status_code == 201, resp.body
    return resp.body


def _link(api, label: str, kind: str, target: str, **extra):
    return api.post(f"{BASE}/notes/{label}/links", {"kind": kind, "target": target, **extra})


def test_a_note_is_linked_to_an_item_a_topic_and_another_note_and_the_links_are_listed(notes_api):
    story = _item(notes_api)
    topic = notes_api.post(f"{BASE}/topics", {"name": "Ideas"}).body
    _note(notes_api)
    _note(notes_api, "second")

    to_item = _link(notes_api, "NOTE-001", "item", story["id"])
    assert to_item.status_code == 201, to_item.body
    body = to_item.body
    assert (body["kind"], body["target"], body["target_project"]) == ("item", story["id"], "demo")
    assert (to_item.body["role"], to_item.body["id"] > 0) == ("reference", True)
    assert _link(notes_api, "NOTE-001", "topic", topic["label"]).status_code == 201
    assert _link(notes_api, "NOTE-001", "note", "NOTE-002").status_code == 201

    links = notes_api.get(f"{BASE}/notes/NOTE-001/links").body
    assert [(link["kind"], link["target"]) for link in links] == [
        ("item", story["id"]), ("topic", "TOPIC-001"), ("note", "NOTE-002")]


def test_a_link_can_point_into_another_project(notes_api):
    other_story = _item(notes_api, "other")
    _note(notes_api)
    linked = _link(notes_api, "NOTE-001", "item", other_story["id"], target_project="other")
    assert (linked.status_code, linked.body["target_project"]) == (201, "other")
    assert linked.body["target_display"] == f"other · {other_story['id']}"
    reverse = notes_api.get(f"{OTHER_BASE}/items/{other_story['id']}/notes").body
    assert [(n["project"], n["label"]) for n in reverse] == [("demo", "NOTE-001")]


def test_a_missing_target_is_refused(notes_api):
    _note(notes_api)
    for kind, target, extra in (("item", "STORY-099", {}), ("topic", "TOPIC-009", {}), ("note", "NOTE-009", {}),
                                ("item", "STORY-001", {"target_project": "nope"})):
        refused = _link(notes_api, "NOTE-001", kind, target, **extra)
        code = "link_project_unknown" if extra else "link_target_not_found"
        assert (refused.status_code, refused.body["code"]) == (404, code), (kind, refused.body)
    assert notes_api.get(f"{BASE}/notes/NOTE-001/links").body == []


def test_a_target_in_the_trash_counts_as_missing(notes_api):
    topic = notes_api.post(f"{BASE}/topics", {"name": "Ideas"}).body
    _note(notes_api)
    _note(notes_api, "second")
    notes_api.delete(f"{BASE}/topics/{topic['label']}")
    notes_api.delete(f"{BASE}/notes/NOTE-002")
    assert _link(notes_api, "NOTE-001", "topic", topic["label"]).body["code"] == "link_target_not_found"
    assert _link(notes_api, "NOTE-001", "note", "NOTE-002").body["code"] == "link_target_not_found"


def test_a_note_does_not_link_to_itself_twice_or_by_trigger_role(notes_api):
    story = _item(notes_api)
    _note(notes_api)
    assert _link(notes_api, "NOTE-001", "note", "NOTE-001").body["code"] == "invalid_value"
    assert _link(notes_api, "NOTE-001", "item", story["id"]).status_code == 201
    twice = _link(notes_api, "NOTE-001", "item", story["id"])
    assert (twice.status_code, twice.body["code"]) == (409, "link_exists")
    assert _link(notes_api, "NOTE-001", "item", story["id"], role="origin").status_code == 201
    assert _link(notes_api, "NOTE-001", "item", story["id"], role="trigger").status_code == 400
    assert _link(notes_api, "NOTE-001", "folder", "x").status_code == 400


def test_a_link_is_removed_but_the_link_of_an_event_trigger_stays_with_its_trigger(notes_api):
    story = _item(notes_api)
    _note(notes_api)
    link = _link(notes_api, "NOTE-001", "item", story["id"]).body
    notes_api.post(f"{BASE}/notes/NOTE-001/triggers", {"kind": "event", "target": story["id"],
                                                       "target_status": "Completed"})
    links = notes_api.get(f"{BASE}/notes/NOTE-001/links").body
    assert [link["role"] for link in links] == ["reference", "trigger"]

    refused = notes_api.delete(f"{BASE}/notes/NOTE-001/links/{links[1]['id']}")
    assert (refused.status_code, refused.body["code"]) == (409, "link_belongs_to_trigger")
    left = notes_api.delete(f"{BASE}/notes/NOTE-001/links/{link['id']}")
    assert left.status_code == 200
    assert [link["role"] for link in left.body] == ["trigger"]
    missing = notes_api.delete(f"{BASE}/notes/NOTE-001/links/{link['id']}")
    assert (missing.status_code, missing.body["code"]) == (404, "link_not_found")


def test_closed_notes_and_notes_in_the_trash_keep_their_links(notes_api):
    story = _item(notes_api)
    note = _note(notes_api)
    link = _link(notes_api, "NOTE-001", "item", story["id"]).body
    notes_api.post(f"{BASE}/notes/NOTE-001/finish", {"version": note["version"], "status": "done"})
    assert _link(notes_api, "NOTE-001", "item", story["id"], role="origin").body["code"] == "note_closed"
    assert notes_api.delete(f"{BASE}/notes/NOTE-001/links/{link['id']}").body["code"] == "note_closed"
    assert len(notes_api.get(f"{BASE}/notes/NOTE-001/links").body) == 1


def test_the_notes_that_point_at_an_item_a_topic_or_a_note_are_found(notes_api):
    story = _item(notes_api)
    topic = notes_api.post(f"{BASE}/topics", {"name": "Ideas"}).body
    for summary in ("one", "two", "three"):
        _note(notes_api, summary)
    _link(notes_api, "NOTE-001", "item", story["id"])
    _link(notes_api, "NOTE-002", "item", story["id"], role="origin")
    _link(notes_api, "NOTE-002", "topic", topic["label"])
    _link(notes_api, "NOTE-003", "note", "NOTE-001")

    by_item = notes_api.get(f"{BASE}/items/{story['id']}/notes").body
    assert [(n["label"], n["role"], n["summary"]) for n in by_item] == [
        ("NOTE-001", "reference", "one"), ("NOTE-002", "origin", "two")]
    assert by_item[0]["status"] == "waiting" and by_item[0]["link_id"] > 0
    assert [n["label"] for n in notes_api.get(f"{BASE}/topics/{topic['label']}/notes").body] == ["NOTE-002"]
    assert [n["label"] for n in notes_api.get(f"{BASE}/notes/NOTE-001/backlinks").body] == ["NOTE-003"]
    assert notes_api.get(f"{BASE}/items/STORY-099/notes").body == []

    notes_api.delete(f"{BASE}/notes/NOTE-001")
    assert [n["label"] for n in notes_api.get(f"{BASE}/items/{story['id']}/notes").body] == ["NOTE-002"]


def test_a_link_to_an_item_follows_the_item_when_its_type_changes(notes_api):
    story = _item(notes_api)
    _note(notes_api)
    _link(notes_api, "NOTE-001", "item", story["id"])

    retyped = notes_api.post(f"/api/v2/items/{_source(notes_api)['id']}/{story['id']}/retype",
                             {"version": story["version"], "type": "Task"})
    assert retyped.status_code == 200, retyped.body
    new_id = retyped.body["item"]["id"]
    assert new_id != story["id"]

    links = notes_api.get(f"{BASE}/notes/NOTE-001/links").body
    assert [(link["kind"], link["target"]) for link in links] == [("item", new_id)]
    assert notes_api.get(f"{BASE}/items/{story['id']}/notes").body == []
    assert [n["label"] for n in notes_api.get(f"{BASE}/items/{new_id}/notes").body] == ["NOTE-001"]


def test_an_event_trigger_in_another_project_is_shown_as_project_and_label(notes_api):
    other_story = _item(notes_api, "other")
    _note(notes_api)
    created = notes_api.post(f"{BASE}/notes/NOTE-001/triggers", {
        "kind": "event", "target": other_story["id"], "target_project": "other", "target_status": "Completed"})
    assert created.status_code == 201, created.body
    shown = notes_api.get(f"{BASE}/notes/NOTE-001").body
    assert [t["target_display"] for t in shown["triggers"]] == [f"other · {other_story['id']}"]


def test_a_link_to_an_unreadable_project_is_reported_unreachable_with_one_notice_and_no_error(notes_api, workspace):
    folder = workspace.add_backlog("backlog")
    project = notes_api.post("/api/v2/sources", {"path": str(folder)}).body["project"]
    _note(notes_api)
    _link(notes_api, "NOTE-001", "item", "STORY-001", target_project=project)
    notes_api.post(f"{BASE}/notes/NOTE-001/triggers", {"kind": "event", "target": "STORY-001",
                                                       "target_project": project, "target_status": "Completed"})
    assert [link["reachable"] for link in notes_api.get(f"{BASE}/notes/NOTE-001/links").body] == [True, True]

    (folder / "TODO.md").unlink()

    links = notes_api.get(f"{BASE}/notes/NOTE-001/links")
    assert links.status_code == 200
    assert [(link["reachable"], link["unreachable_reason"]) for link in links.body] == [
        (False, "source_unreadable")] * 2
    note = notes_api.get(f"{BASE}/notes/NOTE-001").body
    assert [(t["reachable"], t["unreachable_reason"]) for t in note["triggers"]] == [(False, "source_unreadable")]
    assert [n["cause"] for n in note["open_notices"]] == ["project_unreachable"]  # one, however often it is read
    assert note["status"] == "due" and note["reason"] == "notice"

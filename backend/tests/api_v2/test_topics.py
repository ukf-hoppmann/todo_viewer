"""Topics through API v2: create, read, rename, set a due date, move, trash, restore."""
from __future__ import annotations

from tests.api_v2.conftest import BASE

DUE = "2027-01-15T08:00:00+00:00"


def _topic(api, name: str, parent: str | None = None, **extra) -> dict:
    resp = api.post(f"{BASE}/topics", {"name": name, "parent": parent, **extra})
    assert resp.status_code == 201, resp.body
    return resp.body


def test_a_topic_is_created_read_and_listed(notes_api):
    topic = _topic(notes_api, "Ideas", due_at=DUE)
    assert topic["label"] == "TOPIC-001"
    assert (topic["name"], topic["parent"], topic["project"], topic["deleted"]) == ("Ideas", None, "demo", None)
    assert topic["due_at"].startswith("2027-01-15T08:00:00")
    sub = _topic(notes_api, "Later", topic["label"])
    assert sub["parent"] == "TOPIC-001"

    assert notes_api.get(f"{BASE}/topics/TOPIC-001").body == topic
    assert [t["label"] for t in notes_api.get(f"{BASE}/topics").body] == ["TOPIC-001", "TOPIC-002"]


def test_a_topic_is_renamed_and_its_due_date_set_and_cleared(notes_api):
    _topic(notes_api, "Ideas")
    renamed = notes_api.patch(f"{BASE}/topics/TOPIC-001", {"name": "Plans", "due_at": DUE})
    assert (renamed.status_code, renamed.body["name"]) == (200, "Plans")
    assert renamed.body["due_at"].startswith("2027-01-15")
    kept = notes_api.patch(f"{BASE}/topics/TOPIC-001", {"name": "Plans 2"}).body
    assert (kept["name"], kept["due_at"] is not None) == ("Plans 2", True)
    cleared = notes_api.patch(f"{BASE}/topics/TOPIC-001", {"due_at": None}).body
    assert cleared["due_at"] is None


def test_an_empty_name_or_an_empty_change_is_refused(notes_api):
    assert notes_api.post(f"{BASE}/topics", {"name": "  "}).body["code"] == "value_required"
    _topic(notes_api, "Ideas")
    assert notes_api.patch(f"{BASE}/topics/TOPIC-001", {}).status_code == 400
    assert notes_api.post(f"{BASE}/topics", {"name": "x", "due_at": "2027-01-15T08:00:00"}).status_code == 400


def test_an_unknown_topic_or_project_is_not_found(notes_api):
    assert notes_api.get(f"{BASE}/topics/TOPIC-009").body["code"] == "topic_not_found"
    assert notes_api.post(f"{BASE}/topics", {"name": "x", "parent": "TOPIC-009"}).body["code"] == "topic_not_found"
    missing = notes_api.get("/api/v2/projects/nope/topics")
    assert (missing.status_code, missing.body["code"]) == (404, "source_gone")


def test_topics_nest_no_deeper_than_the_limit(notes_api):
    a = _topic(notes_api, "a")
    b = _topic(notes_api, "b", a["label"])
    c = _topic(notes_api, "c", b["label"])
    too_deep = notes_api.post(f"{BASE}/topics", {"name": "d", "parent": c["label"]})
    assert (too_deep.status_code, too_deep.body["code"]) == (400, "topic_too_deep")


def test_a_topic_moves_but_not_into_itself_or_beyond_the_limit(notes_api):
    a, b, c = (_topic(notes_api, n) for n in "abc")
    moved = notes_api.post(f"{BASE}/topics/{b['label']}/move", {"parent": a["label"]})
    assert (moved.status_code, moved.body["parent"]) == (200, a["label"])
    loop = notes_api.post(f"{BASE}/topics/{a['label']}/move", {"parent": b["label"]})
    assert (loop.status_code, loop.body["code"]) == (400, "topic_loop")
    notes_api.post(f"{BASE}/topics/{c['label']}/move", {"parent": b["label"]})
    d = _topic(notes_api, "d")
    deep = notes_api.post(f"{BASE}/topics/{a['label']}/move", {"parent": d["label"]})
    assert deep.body["code"] == "topic_too_deep"
    to_root = notes_api.post(f"{BASE}/topics/{b['label']}/move", {"parent": None})
    assert to_root.body["parent"] is None


def test_deleting_a_topic_with_content_needs_the_cascade_and_it_can_be_restored(notes_api):
    a = _topic(notes_api, "a")
    b = _topic(notes_api, "b", a["label"])
    refused = notes_api.delete(f"{BASE}/topics/{a['label']}")
    assert (refused.status_code, refused.body["code"]) == (409, "topic_has_content")
    assert refused.body["details"]["items"] == b["label"]

    gone = notes_api.delete(f"{BASE}/topics/{a['label']}", cascade="true")
    assert gone.status_code == 200
    assert sorted(t["label"] for t in gone.body["topics"]) == [a["label"], b["label"]]
    assert notes_api.get(f"{BASE}/topics").body == []
    assert len(notes_api.get(f"{BASE}/topics", include_deleted="true").body) == 2

    back = notes_api.post(f"{BASE}/topics/{a['label']}/restore", {})
    assert back.status_code == 200
    assert [t["label"] for t in notes_api.get(f"{BASE}/topics").body] == [a["label"], b["label"]]
    again = notes_api.post(f"{BASE}/topics/{a['label']}/restore", {})
    assert again.body["code"] == "topic_not_deleted"


def test_a_childless_topic_is_deleted_without_the_cascade(notes_api):
    a = _topic(notes_api, "a")
    assert notes_api.delete(f"{BASE}/topics/{a['label']}").status_code == 200
    assert notes_api.get(f"{BASE}/topics/{a['label']}").body["deleted"] is not None

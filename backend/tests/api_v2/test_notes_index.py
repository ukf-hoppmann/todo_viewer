"""The lean notes index, the due counter, and the due list through API v2."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tests.api_v2.conftest import BASE, OTHER_BASE

INDEX = "/api/v2/notes/index"
COUNT = "/api/v2/notes/due/count"
DUE = "/api/v2/notes/due"


def _at(days: float) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


def _topic(api, name: str, parent: str | None = None, base: str = BASE, **extra) -> dict:
    return api.post(f"{base}/topics", {"name": name, "parent": parent, **extra}).body


def _note(api, summary: str, base: str = BASE, **extra) -> dict:
    resp = api.post(f"{base}/notes", {"summary": summary, "body": "a long text " * 50, **extra})
    assert resp.status_code == 201, resp.body
    return resp.body


def _story(api, project: str = "demo") -> str:
    source = next(s for s in api.get("/api/v2/sources").body if s["project"] == project)
    resp = api.post("/api/v2/items", {"source_id": source["id"], "type": "Story", "title": "Linked", "area": "Core",
                                      "goal": "A goal.", "completion_criteria": "Checked."})
    return resp.body["id"]


def _labels(response, key: str = "notes") -> list[str]:
    assert response.status_code == 200, response.body
    return [f"{n['project']}/{n['label']}" for n in response.body[key]]


def _world(api) -> None:
    """demo: TOPIC-001 Ideas > TOPIC-002 Later; NOTE-001 in Ideas, NOTE-002 in Later (due), NOTE-003 without topic,
    NOTE-004 done. other: NOTE-001 without topic."""
    _topic(api, "Ideas")
    _topic(api, "Later", "TOPIC-001", due_at=_at(5))
    _note(api, "in ideas", topic="TOPIC-001")
    _note(api, "in later", topic="TOPIC-002", review_at=_at(-1))
    _note(api, "no topic")
    done = _note(api, "finished")
    api.post(f"{BASE}/notes/NOTE-004/finish", {"version": done["version"], "status": "done"})
    _note(api, "elsewhere", base=OTHER_BASE)


def test_the_index_has_only_short_fields_and_no_long_texts(notes_api):
    _world(notes_api)
    body = notes_api.get(INDEX).body

    assert set(body) == {"topics", "notes"}
    for note in body["notes"]:
        assert set(note) == {"project", "label", "summary", "status", "reason", "review_at", "topic", "archived"}
    for topic in body["topics"]:
        assert set(topic) == {"project", "label", "name", "parent", "path", "due_at", "due", "note_count"}
    assert "a long text" not in str(body)


def test_the_index_lists_open_notes_and_topics_of_all_projects(notes_api):
    _world(notes_api)
    body = notes_api.get(INDEX).body
    assert _labels(notes_api.get(INDEX)) == ["demo/NOTE-001", "demo/NOTE-002", "demo/NOTE-003", "other/NOTE-001"]
    by_label = {n["label"]: n for n in body["notes"] if n["project"] == "demo"}
    assert (by_label["NOTE-001"]["status"], by_label["NOTE-001"]["reason"]) == ("waiting", None)
    assert (by_label["NOTE-002"]["status"], by_label["NOTE-002"]["reason"]) == ("due", "review_expired")
    assert by_label["NOTE-002"]["topic"] == "TOPIC-002"

    topics = {t["label"]: t for t in body["topics"]}
    assert topics["TOPIC-002"]["path"] == ["Ideas", "Later"]
    assert (topics["TOPIC-002"]["parent"], topics["TOPIC-002"]["note_count"], topics["TOPIC-002"]["due"]) == (
        "TOPIC-001", 1, False)
    assert topics["TOPIC-001"]["note_count"] == 1


def test_the_index_filters_by_project(notes_api):
    _world(notes_api)
    assert _labels(notes_api.get(INDEX, project="other")) == ["other/NOTE-001"]
    assert notes_api.get(INDEX, project="other").body["topics"] == []
    assert [t["label"] for t in notes_api.get(INDEX, project="demo").body["topics"]] == ["TOPIC-001", "TOPIC-002"]
    missing = notes_api.get(INDEX, project="nope")
    assert (missing.status_code, missing.body["code"]) == (404, "source_gone")


def test_the_index_filters_by_topic_with_its_subtopics(notes_api):
    _world(notes_api)
    assert _labels(notes_api.get(INDEX, project="demo", topic="TOPIC-001")) == ["demo/NOTE-001", "demo/NOTE-002"]
    assert _labels(notes_api.get(INDEX, project="demo", topic="TOPIC-002")) == ["demo/NOTE-002"]
    narrowed = notes_api.get(INDEX, project="demo", topic="TOPIC-002").body["topics"]
    assert [t["label"] for t in narrowed] == ["TOPIC-002"]
    assert notes_api.get(INDEX, project="demo", topic="TOPIC-009").body["code"] == "topic_not_found"
    assert notes_api.get(INDEX, topic="TOPIC-001").body["code"] == "value_required"


def test_the_index_filters_by_status_and_due(notes_api):
    _world(notes_api)
    assert _labels(notes_api.get(INDEX, status="due")) == ["demo/NOTE-002"]
    assert _labels(notes_api.get(INDEX, due="true")) == ["demo/NOTE-002"]
    assert _labels(notes_api.get(INDEX, status="waiting")) == ["demo/NOTE-001", "demo/NOTE-003", "other/NOTE-001"]
    assert _labels(notes_api.get(INDEX, status="done")) == ["demo/NOTE-004"]  # a closed status reads the archive
    assert _labels(notes_api.get(INDEX, status="due", due="true")) == ["demo/NOTE-002"]
    assert _labels(notes_api.get(INDEX, status="waiting", due="true")) == []
    assert notes_api.get(INDEX, status="sleeping").status_code == 400


def test_the_index_filters_by_several_statuses_open_and_closed_together(notes_api):
    _world(notes_api)
    assert _labels(notes_api.get(INDEX, status=["waiting", "due"])) == [
        "demo/NOTE-001", "demo/NOTE-002", "demo/NOTE-003", "other/NOTE-001"]
    assert _labels(notes_api.get(INDEX, status=["due", "done"])) == ["demo/NOTE-002", "demo/NOTE-004"]
    assert _labels(notes_api.get(INDEX, status=["done", "dropped"])) == ["demo/NOTE-004"]
    assert notes_api.get(INDEX, status=["due", "sleeping"]).status_code == 400


def test_the_index_reads_the_archive_on_request(notes_api):
    _world(notes_api)
    assert _labels(notes_api.get(INDEX, archived="true")) == ["demo/NOTE-004"]
    archived = notes_api.get(INDEX, archived="true").body["notes"][0]
    assert (archived["status"], archived["archived"]) == ("done", True)


def test_the_index_leaves_out_the_trash(notes_api):
    _world(notes_api)
    notes_api.delete(f"{BASE}/notes/NOTE-003")
    notes_api.delete(f"{BASE}/topics/TOPIC-002", cascade="true")
    assert _labels(notes_api.get(INDEX, project="demo")) == ["demo/NOTE-001"]
    assert [t["label"] for t in notes_api.get(INDEX, project="demo").body["topics"]] == ["TOPIC-001"]


def test_the_index_finds_the_notes_that_point_at_an_item(notes_api):
    _world(notes_api)
    story = _story(notes_api)
    notes_api.post(f"{BASE}/notes/NOTE-001/links", {"kind": "item", "target": story})
    notes_api.post(f"{BASE}/notes/NOTE-003/triggers", {"kind": "event", "target": story,
                                                       "target_status": "Completed"})
    assert _labels(notes_api.get(INDEX, linked_item=story, linked_project="demo")) == [
        "demo/NOTE-001", "demo/NOTE-003"]
    assert _labels(notes_api.get(INDEX, linked_item=story, project="demo")) == ["demo/NOTE-001", "demo/NOTE-003"]
    assert _labels(notes_api.get(INDEX, linked_item=story, linked_project="demo", status="waiting")) == [
        "demo/NOTE-001", "demo/NOTE-003"]
    assert _labels(notes_api.get(INDEX, linked_item="STORY-099", linked_project="demo")) == []
    assert notes_api.get(INDEX, linked_item=story).body["code"] == "value_required"


def test_the_index_finds_notes_of_another_project_that_point_at_an_item(notes_api):
    story = _story(notes_api, "other")
    _note(notes_api, "from demo")
    notes_api.post(f"{BASE}/notes/NOTE-001/links", {"kind": "item", "target": story, "target_project": "other"})
    assert _labels(notes_api.get(INDEX, linked_item=story, linked_project="other")) == ["demo/NOTE-001"]
    assert _labels(notes_api.get(INDEX, linked_item=story, linked_project="other", project="other")) == []


# ---------- counter and due list ----------

def test_the_counter_counts_due_notes_of_all_projects(notes_api):
    assert notes_api.get(COUNT).body == {"count": 0, "by_project": {"demo": 0, "other": 0}}
    _world(notes_api)
    assert notes_api.get(COUNT).body == {"count": 1, "by_project": {"demo": 1, "other": 0}}
    _note(notes_api, "late", base=OTHER_BASE, review_at=_at(-2))
    assert notes_api.get(COUNT).body == {"count": 2, "by_project": {"demo": 1, "other": 1}}


def test_the_counter_follows_triggers_snoozing_finishing_and_the_trash(notes_api):
    note = _note(notes_api, "idea")
    assert notes_api.get(COUNT).body["count"] == 0

    notes_api.post(f"{BASE}/notes/NOTE-001/triggers", {"kind": "time", "at": _at(-1)})
    assert notes_api.get(COUNT).body["count"] == 1
    due = notes_api.get(f"{BASE}/notes/NOTE-001").body
    notes_api.post(f"{BASE}/notes/NOTE-001/snooze", {"version": due["version"], "review_at": _at(3)})
    assert notes_api.get(COUNT).body["count"] == 0

    notes_api.post(f"{BASE}/notes/NOTE-001/triggers", {"kind": "time", "at": _at(-1)})
    assert notes_api.get(COUNT).body["count"] == 1
    notes_api.delete(f"{BASE}/notes/NOTE-001")
    assert notes_api.get(COUNT).body["count"] == 0
    notes_api.post(f"{BASE}/notes/NOTE-001/restore", {})
    kept = notes_api.get(f"{BASE}/notes/NOTE-001").body
    assert kept["status"] == "due"
    finished = notes_api.post(f"{BASE}/notes/NOTE-001/finish", {"version": kept["version"], "status": "dropped"})
    assert finished.status_code == 200
    assert notes_api.get(COUNT).body["count"] == 0
    assert note["label"] == "NOTE-001"


def test_the_counter_follows_an_item_status_change(notes_api):
    story = _story(notes_api)
    _note(notes_api, "idea")
    notes_api.post(f"{BASE}/notes/NOTE-001/triggers", {"kind": "event", "target": story,
                                                       "target_status": "In progress"})
    assert notes_api.get(COUNT).body["count"] == 0
    source = next(s for s in notes_api.get("/api/v2/sources").body if s["project"] == "demo")
    item = notes_api.get(f"/api/v2/items/{source['id']}/{story}").body
    notes_api.patch(f"/api/v2/items/{source['id']}/{story}", {"version": item["version"],
                                                              "fields": {"status": "In progress"}})
    assert notes_api.get(COUNT).body["count"] == 1


def test_the_due_list_gives_reason_topic_path_fired_triggers_and_actions(notes_api):
    _world(notes_api)
    _note(notes_api, "late elsewhere", base=OTHER_BASE, review_at=_at(-2))
    notes_api.post(f"{BASE}/notes/NOTE-003/triggers", {"kind": "time", "at": _at(-1)})

    due = notes_api.get(DUE)
    assert due.status_code == 200
    assert [(n["project"], n["label"]) for n in due.body] == [
        ("demo", "NOTE-002"), ("demo", "NOTE-003"), ("other", "NOTE-002")]
    later, plain, elsewhere = due.body
    assert later["summary"] == "in later"
    assert (later["reason"], later["topic"], later["topic_path"]) == ("review_expired", "TOPIC-002", ["Ideas", "Later"])
    assert later["triggers"] == []
    assert (plain["reason"], plain["topic_path"], len(plain["triggers"])) == ("trigger", [], 1)
    assert plain["triggers"][0]["kind"] == "time"
    assert elsewhere["reason"] == "review_expired"
    for note in due.body:
        assert note["actions"] == ["keep", "snooze", "done", "dropped"]
        assert "body" not in note and note["status"] == "due"


def test_the_due_list_is_empty_when_nothing_is_due(notes_api):
    _note(notes_api, "idea")
    assert notes_api.get(DUE).body == []

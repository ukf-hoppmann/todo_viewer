"""The global notes options (`notes.review_days`, `notes.max_topic_depth`) through API v2."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tests.api_v2.conftest import BASE

URL = "/api/v2/notes/settings"


def test_the_defaults_are_read_when_nothing_is_configured(notes_api):
    response = notes_api.get(URL)
    assert (response.status_code, response.body) == (200, {"max_topic_depth": 3, "review_days": 30})


def test_a_change_is_saved_in_the_config_and_keeps_the_rest_of_it(notes_api, workspace):
    changed = notes_api.put(URL, {"review_days": 7})
    assert (changed.status_code, changed.body) == (200, {"max_topic_depth": 3, "review_days": 7})
    assert notes_api.get(URL).body == changed.body

    config = workspace.read_config()
    assert config["notes"] == {"max_topic_depth": 3, "review_days": 7}
    assert [s["project"] for s in config["sources"]] == ["demo", "other"]

    both = notes_api.put(URL, {"max_topic_depth": 2, "review_days": 14})
    assert both.body == {"max_topic_depth": 2, "review_days": 14}
    assert workspace.read_config()["notes"] == {"max_topic_depth": 2, "review_days": 14}


def test_the_review_days_apply_to_the_next_note_without_a_restart(notes_api):
    notes_api.put(URL, {"review_days": 7})
    note = notes_api.post(f"{BASE}/notes", {"summary": "idea"}).body
    ahead = datetime.fromisoformat(note["review_at"]) - datetime.now(UTC)
    assert timedelta(days=6) < ahead < timedelta(days=8)

    notes_api.put(URL, {"review_days": 60})
    kept = notes_api.post(f"{BASE}/notes/NOTE-001/keep", {"version": note["version"]}).body
    assert datetime.fromisoformat(kept["review_at"]) - datetime.now(UTC) > timedelta(days=59)


def test_the_topic_depth_applies_to_the_next_topic_without_a_restart(notes_api):
    notes_api.put(URL, {"max_topic_depth": 1})
    root = notes_api.post(f"{BASE}/topics", {"name": "root"})
    assert root.status_code == 201
    refused = notes_api.post(f"{BASE}/topics", {"name": "child", "parent": root.body["label"]})
    assert (refused.status_code, refused.body["code"]) == (400, "topic_too_deep")

    notes_api.put(URL, {"max_topic_depth": 5})
    assert notes_api.post(f"{BASE}/topics", {"name": "child", "parent": root.body["label"]}).status_code == 201


def test_lowering_the_depth_leaves_existing_topics_alone(notes_api):
    a = notes_api.post(f"{BASE}/topics", {"name": "a"}).body
    notes_api.post(f"{BASE}/topics", {"name": "b", "parent": a["label"]})
    notes_api.put(URL, {"max_topic_depth": 1})
    assert len(notes_api.get(f"{BASE}/topics").body) == 2


def test_values_that_are_not_positive_whole_numbers_are_refused(notes_api):
    for body in ({"review_days": 0}, {"review_days": -3}, {"max_topic_depth": 0}, {"review_days": "soon"},
                 {"review_days": 1.5}, {"review_days": True}, {"review_days": None}, {"colour": 1}, {}):
        refused = notes_api.put(URL, body)
        assert refused.status_code == 400, body
    assert notes_api.get(URL).body == {"max_topic_depth": 3, "review_days": 30}


def test_a_value_beyond_the_sane_range_is_refused_with_its_name(notes_api):
    refused = notes_api.put(URL, {"max_topic_depth": 50})
    assert (refused.status_code, refused.body["code"]) == (400, "invalid_value")
    assert refused.body["details"]["field"] == "max_topic_depth"
    assert notes_api.put(URL, {"review_days": 100000}).body["code"] == "invalid_value"

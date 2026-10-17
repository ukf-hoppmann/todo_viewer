from __future__ import annotations

from notes_api import NOTES, new_note, project
from workspace_env import Env


def test_the_index_lines_name_status_reason_and_topic_of_each_note(notes: Env) -> None:
    topic = notes.client.post(f"{NOTES}/topics", json={"project": project(notes), "name": "Ideen"}).json()
    new_note(notes, "Zukunft", topic=topic["uid"])
    new_note(notes, "Längst fällig", review_at="2020-01-01T00:00:00Z")

    response = notes.client.get(f"{NOTES}/index/lines")

    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["topic_count"], body["note_count"]) == (1, 2)
    assert body["topics"].splitlines() == ["Label | Name | Due at | Due | Notes", "TOPIC-001 | Ideen | - | 0 | 1"]
    rows = body["notes"].splitlines()
    assert rows[0] == "Label | Status | Reason | Review at | Topic | Summary"
    assert "NOTE-002 | due | review_expired | 2020-01-01 | - | Längst fällig" in rows
    assert any(row.startswith("NOTE-001 | waiting | - | ") and row.endswith("| TOPIC-001 | Zukunft") for row in rows)

from __future__ import annotations

from memos_api import NOTES, new_memo, project
from workspace_env import Env


def test_the_index_lines_name_status_reason_and_topic_of_each_memo(memos: Env) -> None:
    topic = memos.client.post(f"{NOTES}/topics", json={"project": project(memos), "name": "Ideen"}).json()
    new_memo(memos, "Zukunft", topic=topic["uid"])
    new_memo(memos, "Längst fällig", review_at="2020-01-01T00:00:00Z")

    response = memos.client.get(f"{NOTES}/index/lines")

    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["topic_count"], body["memo_count"]) == (1, 2)
    assert body["topics"].splitlines() == ["Label | Name | Due at | Due | Memos", "TOPIC-001 | Ideen | - | 0 | 1"]
    rows = body["memos"].splitlines()
    assert rows[0] == "Label | Status | Reason | Review at | Topic | Summary"
    assert "MEMO-002 | due | review_expired | 2020-01-01 | - | Längst fällig" in rows
    assert any(row.startswith("MEMO-001 | waiting | - | ") and row.endswith("| TOPIC-001 | Zukunft") for row in rows)

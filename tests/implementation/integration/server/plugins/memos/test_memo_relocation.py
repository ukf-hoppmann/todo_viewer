from __future__ import annotations

from typing import Any

from memos_api import NOTES, add_trigger, link, links, memo, new_item, new_memo, project, set_status
from workspace_env import Env


def _move(env: Env, entry: dict[str, Any], target: str, **body: Any) -> Any:
    return env.client.post(
        f"{NOTES}/memos/{entry['uid']}/move", json={"version": entry["version"], "target_project": target, **body}
    )


def _topic(env: Env, project_uid: str, name: str) -> str:
    response = env.client.post(f"{NOTES}/topics", json={"project": project_uid, "name": name})
    assert response.status_code == 200, response.text
    return str(response.json()["uid"])


def test_a_memo_moves_to_another_project_and_the_old_one_goes_to_the_trash(memos: Env) -> None:
    other = str(memos.create("Anderes")["uid"])
    entry = new_memo(memos, "Idee", body="Langtext")
    topic = _topic(memos, other, "Ziel")

    moved = _move(memos, entry, other, topic=topic)

    assert moved.status_code == 200, moved.text
    shown = moved.json()
    assert (shown["project_uid"], shown["summary"], shown["body"], shown["topic_uid"]) == (
        other,
        "Idee",
        "Langtext",
        topic,
    )
    assert shown["uid"] != entry["uid"]
    trash = memos.client.get("/api/workspace/trash").json()
    assert [t["uid"] for t in trash] == [entry["uid"]]
    assert memo(memos, entry["uid"])["deleted"] is True


def test_documents_links_and_event_triggers_move_with_the_memo(memos: Env) -> None:
    other = str(memos.create("Anderes")["uid"])
    entry = new_memo(memos, "Idee")
    target = new_item(memos)
    link(memos, entry["uid"], target["uid"])
    assert add_trigger(memos, entry, kind="event", target=target["uid"], status="In progress").status_code == 200
    put = memos.client.put(
        f"{NOTES}/memos/{entry['uid']}/documents/{entry['label']}_spec.md",
        json={"content": "# Spec\n", "version": None},
    )
    assert put.status_code == 200, put.text

    moved = _move(memos, memo(memos, entry["uid"]), other).json()

    documents = memos.client.get(f"{NOTES}/memos/{moved['uid']}/documents").json()
    assert [d["name"] for d in documents] == [f"{moved['label']}_spec.md"]
    roles = sorted(e["role"] for e in links(memos, moved["uid"])["outgoing"])
    assert roles == ["reference", "trigger"]
    assert [t["kind"] for t in moved["triggers"]] == ["event"]
    set_status(memos, target, "In progress")
    assert memo(memos, moved["uid"])["status"] == "due"


def test_a_move_needs_another_project_and_the_current_version(memos: Env) -> None:
    other = str(memos.create("Anderes")["uid"])
    entry = new_memo(memos)

    same = _move(memos, entry, project(memos))
    stale = memos.client.post(
        f"{NOTES}/memos/{entry['uid']}/move", json={"version": entry["version"] + 5, "target_project": other}
    )

    assert (same.status_code, same.json()["code"]) == (400, "same_project")
    assert (stale.status_code, stale.json()["code"]) == (409, "version_conflict")
    assert memo(memos, entry["uid"])["deleted"] is False


def test_a_topic_of_another_project_is_refused(memos: Env) -> None:
    other = str(memos.create("Anderes")["uid"])
    entry = new_memo(memos)
    wrong = _topic(memos, project(memos), "Hier")

    refused = _move(memos, entry, other, topic=wrong)

    assert refused.json()["code"] == "topic_other_project"

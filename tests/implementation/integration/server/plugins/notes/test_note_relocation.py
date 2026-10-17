from __future__ import annotations

from typing import Any

from notes_api import NOTES, add_trigger, link, links, new_item, new_note, note, project, set_status
from workspace_env import Env


def _move(env: Env, entry: dict[str, Any], target: str, **body: Any) -> Any:
    return env.client.post(
        f"{NOTES}/notes/{entry['uid']}/move", json={"version": entry["version"], "target_project": target, **body}
    )


def _topic(env: Env, project_uid: str, name: str) -> str:
    response = env.client.post(f"{NOTES}/topics", json={"project": project_uid, "name": name})
    assert response.status_code == 200, response.text
    return str(response.json()["uid"])


def test_a_note_moves_to_another_project_and_the_old_one_goes_to_the_trash(notes: Env) -> None:
    other = str(notes.create("Anderes")["uid"])
    entry = new_note(notes, "Idee", body="Langtext")
    topic = _topic(notes, other, "Ziel")

    moved = _move(notes, entry, other, topic=topic)

    assert moved.status_code == 200, moved.text
    shown = moved.json()
    assert (shown["project_uid"], shown["summary"], shown["body"], shown["topic_uid"]) == (
        other,
        "Idee",
        "Langtext",
        topic,
    )
    assert shown["uid"] != entry["uid"]
    trash = notes.client.get("/api/workspace/trash").json()
    assert [t["uid"] for t in trash] == [entry["uid"]]
    assert note(notes, entry["uid"])["deleted"] is True


def test_documents_links_and_event_triggers_move_with_the_note(notes: Env) -> None:
    other = str(notes.create("Anderes")["uid"])
    entry = new_note(notes, "Idee")
    target = new_item(notes)
    link(notes, entry["uid"], target["uid"])
    assert add_trigger(notes, entry, kind="event", target=target["uid"], status="In progress").status_code == 200
    put = notes.client.put(
        f"{NOTES}/notes/{entry['uid']}/documents/{entry['label']}_spec.md",
        json={"content": "# Spec\n", "version": None},
    )
    assert put.status_code == 200, put.text

    moved = _move(notes, note(notes, entry["uid"]), other).json()

    documents = notes.client.get(f"{NOTES}/notes/{moved['uid']}/documents").json()
    assert [d["name"] for d in documents] == [f"{moved['label']}_spec.md"]
    roles = sorted(e["role"] for e in links(notes, moved["uid"])["outgoing"])
    assert roles == ["reference", "trigger"]
    assert [t["kind"] for t in moved["triggers"]] == ["event"]
    set_status(notes, target, "In progress")
    assert note(notes, moved["uid"])["status"] == "due"


def test_a_move_needs_another_project_and_the_current_version(notes: Env) -> None:
    other = str(notes.create("Anderes")["uid"])
    entry = new_note(notes)

    same = _move(notes, entry, project(notes))
    stale = notes.client.post(
        f"{NOTES}/notes/{entry['uid']}/move", json={"version": entry["version"] + 5, "target_project": other}
    )

    assert (same.status_code, same.json()["code"]) == (400, "same_project")
    assert (stale.status_code, stale.json()["code"]) == (409, "version_conflict")
    assert note(notes, entry["uid"])["deleted"] is False


def test_a_topic_of_another_project_is_refused(notes: Env) -> None:
    other = str(notes.create("Anderes")["uid"])
    entry = new_note(notes)
    wrong = _topic(notes, project(notes), "Hier")

    refused = _move(notes, entry, other, topic=wrong)

    assert refused.json()["code"] == "topic_other_project"

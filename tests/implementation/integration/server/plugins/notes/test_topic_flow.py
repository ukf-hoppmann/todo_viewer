from __future__ import annotations

from typing import Any

from workspace_env import Env

API = "/api/notes"


def _project(env: Env) -> str:
    return str(env.general()["uid"])


def _topic(env: Env, name: str, parent: dict[str, Any] | None = None, project: str | None = None) -> dict[str, Any]:
    response = env.client.post(
        f"{API}/topics",
        json={"project": project or _project(env), "name": name, "parent": parent["uid"] if parent else None},
    )
    assert response.status_code == 200, response.text
    return _topic_in(env, response.json()["uid"])


def _topic_in(env: Env, uid: str) -> dict[str, Any]:
    return next(t for t in _index(env)["topics"] if t["uid"] == uid)


def _index(env: Env, **params: Any) -> dict[str, Any]:
    return env.client.get(f"{API}/index", params=params).json()  # type: ignore[no-any-return]


def _note(env: Env, summary: str, topic: dict[str, Any] | None = None) -> dict[str, Any]:
    fields: dict[str, Any] = {"summary": summary}
    if topic:
        fields["topic"] = topic["uid"]
    response = env.client.post(f"{API}/notes", json={"project": _project(env), "fields": fields})
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _post(env: Env, topic: dict[str, Any], action: str, **body: Any) -> Any:
    return env.client.post(f"{API}/topics/{topic['uid']}/{action}", json={"version": topic["version"], **body})


def _note_state(env: Env, note: dict[str, Any]) -> dict[str, Any]:
    return next(n for n in _index(env)["notes"] if n["uid"] == note["uid"])


def test_topics_get_labels_and_notes_hang_below_them(notes: Env) -> None:
    topic = _topic(notes, "Ideen")
    note = _note(notes, "Eine Idee", topic)
    assert topic["label"] == "TOPIC-001"
    assert notes.client.get(f"{API}/notes/{note['uid']}").json()["path"] == [
        {"uid": topic["uid"], "label": "TOPIC-001", "name": "Ideen"}
    ]
    assert _topic_in(notes, topic["uid"])["open_notes"] == 1


def test_counters_sum_open_notes_with_sub_topics_and_ignore_archived_ones(notes: Env) -> None:
    top = _topic(notes, "Oben")
    sub = _topic(notes, "Unten", top)
    _note(notes, "a", top)
    done = _note(notes, "b", sub)
    _note(notes, "c", sub)
    notes.client.post(f"{API}/notes/{done['uid']}/finish", json={"version": done["version"], "status": "done"})
    assert (_topic_in(notes, top["uid"])["open_notes"], _topic_in(notes, sub["uid"])["open_notes"]) == (2, 1)


def test_the_depth_is_limited_by_the_setting(notes: Env) -> None:
    one = _topic(notes, "1")
    two = _topic(notes, "2", one)
    three = _topic(notes, "3", two)
    refused = notes.client.post(f"{API}/topics", json={"project": _project(notes), "name": "4", "parent": three["uid"]})
    assert (refused.status_code, refused.json()["code"]) == (400, "topic_too_deep")
    notes.client.put(f"{API}/settings", json={"max_topic_depth": 4})
    assert _topic(notes, "4", three)["name"] == "4"


def test_moving_checks_loops_and_depth(notes: Env) -> None:
    a = _topic(notes, "a")
    b = _topic(notes, "b", a)
    loop = _post(notes, a, "move", parent=b["uid"])
    assert loop.json()["code"] == "topic_loop"
    moved = _post(notes, b, "move", parent=None)
    assert moved.status_code == 200
    assert _topic_in(notes, b["uid"])["parent_uid"] is None


def test_a_topic_can_be_renamed_and_get_a_due_date(notes: Env) -> None:
    topic = _topic(notes, "Alt")
    renamed = notes.client.put(
        f"{API}/topics/{topic['uid']}",
        json={"version": topic["version"], "fields": {"name": "Neu", "due_at": "2026-12-01"}},
    )
    assert renamed.status_code == 200
    changed = _topic_in(notes, topic["uid"])
    assert (changed["name"], changed["due_at"][:10]) == ("Neu", "2026-12-01")
    cleared = notes.client.put(
        f"{API}/topics/{topic['uid']}", json={"version": changed["version"], "fields": {"due_at": None}}
    )
    assert cleared.status_code == 200 and _topic_in(notes, topic["uid"])["due_at"] is None


def test_a_note_cannot_go_into_a_topic_of_another_project(notes: Env) -> None:
    other = notes.create("Anderes")
    topic = _topic(notes, "Dort", project=str(other["uid"]))
    refused = notes.client.post(
        f"{API}/notes", json={"project": _project(notes), "fields": {"summary": "x", "topic": topic["uid"]}}
    )
    assert refused.json()["code"] == "topic_other_project"


def test_an_empty_topic_is_deleted_at_once_and_comes_back_from_the_trash(notes: Env) -> None:
    topic = _topic(notes, "Leer")
    assert _post(notes, topic, "delete").json()["count"] == 1
    assert _index(notes)["topics"] == []
    restored = notes.client.post("/api/workspace/trash/restore", json={"uids": [topic["uid"]]})
    assert restored.status_code == 200
    assert [t["uid"] for t in _index(notes)["topics"]] == [topic["uid"]]


def test_deleting_a_topic_with_content_reports_the_numbers_and_changes_nothing(notes: Env) -> None:
    topic = _topic(notes, "Voll")
    _topic(notes, "Unter", topic)
    done = _note(notes, "erledigt", topic)
    _note(notes, "offen", topic)
    notes.client.post(f"{API}/notes/{done['uid']}/finish", json={"version": done["version"], "status": "done"})
    refused = _post(notes, topic, "delete")
    assert (refused.status_code, refused.json()["code"]) == (400, "topic_has_content")
    assert refused.json()["details"] == {"active": 1, "archived": 1, "topics": 1}
    content = notes.client.get(f"{API}/topics/{topic['uid']}/content").json()
    assert content == {"topics": 1, "active": 1, "archived": 1}
    assert len(_index(notes)["topics"]) == 2


def test_delete_with_keep_archived_and_move_hangs_notes_elsewhere(notes: Env) -> None:
    topic = _topic(notes, "Weg")
    target = _topic(notes, "Ziel")
    done = _note(notes, "erledigt", topic)
    active = _note(notes, "offen", topic)
    notes.client.post(f"{API}/notes/{done['uid']}/finish", json={"version": done["version"], "status": "done"})
    result = _post(notes, topic, "delete", keep_archived=True, active_notes="move", move_to=target["uid"])
    assert result.status_code == 200, result.text
    state = _index(notes)
    assert _note_state(notes, active)["topic_uid"] == target["uid"]
    archive = next(t for t in state["topics"] if t["system"])
    assert archive["name"] == "Archiviert"
    kept = _note_state(notes, done)
    assert (kept["topic_uid"], kept["status"], kept["archived"]) == (archive["uid"], "done", True)
    assert topic["uid"] not in [t["uid"] for t in state["topics"]]


def test_the_archive_topic_is_reused_and_cannot_be_deleted(notes: Env) -> None:
    for name in ("eins", "zwei"):
        topic = _topic(notes, name)
        done = _note(notes, name, topic)
        notes.client.post(f"{API}/notes/{done['uid']}/finish", json={"version": done["version"], "status": "done"})
        assert _post(notes, topic, "delete", keep_archived=True, active_notes="delete").status_code == 200
    archives = [t for t in _index(notes)["topics"] if t["system"]]
    assert len(archives) == 1
    refused = _post(notes, archives[0], "delete")
    assert refused.json()["code"] == "topic_system"


def test_unchosen_groups_go_to_the_trash_and_come_back_with_the_topic(notes: Env) -> None:
    topic = _topic(notes, "Mit Inhalt")
    sub = _topic(notes, "Unter", topic)
    inner = _note(notes, "innen", sub)
    assert _post(notes, topic, "delete", active_notes="delete").json()["count"] == 3
    assert _index(notes) == {"topics": [], "notes": []}
    blocked = notes.client.post("/api/workspace/trash/restore", json={"uids": [inner["uid"]]})
    assert blocked.status_code == 400 and blocked.json()["code"] == "topic_in_trash"
    assert notes.client.post("/api/workspace/trash/restore", json={"uids": [topic["uid"]]}).status_code == 200
    state = _index(notes)
    assert len(state["topics"]) == 2 and [n["uid"] for n in state["notes"]] == [inner["uid"]]


def test_archiving_hides_open_notes_with_the_topic_and_reactivating_brings_them_back(notes: Env) -> None:
    topic = _topic(notes, "Alt")
    sub = _topic(notes, "Sub", topic)
    open_note = _note(notes, "offen", sub)
    done = _note(notes, "erledigt", topic)
    notes.client.post(f"{API}/notes/{done['uid']}/finish", json={"version": done["version"], "status": "dropped"})
    result = _post(notes, topic, "archive", active_notes="archive")
    assert result.status_code == 200, result.text
    state = _index(notes)
    assert all(t["archived"] for t in state["topics"])
    assert _note_state(notes, open_note)["archived"] is True
    assert _topic_in(notes, topic["uid"])["open_notes"] == 0
    back = _post(notes, _topic_in(notes, topic["uid"]), "reactivate")
    assert back.status_code == 200, back.text
    assert not any(t["archived"] for t in _index(notes)["topics"])
    assert _note_state(notes, open_note)["archived"] is False
    assert _note_state(notes, done)["archived"] is True  # unabhängig archiviert, bleibt es


def test_notes_in_an_archived_topic_trigger_nothing(notes: Env) -> None:
    from datetime import timedelta

    topic = _topic(notes, "Ruhe")
    _note(notes, "schläft", topic)
    _post(notes, topic, "archive", active_notes="archive")
    notes.clock.advance(timedelta(days=60))
    assert notes.client.get(f"{API}/due").json()["count"] == 0
    assert _topic_in(notes, topic["uid"])["due_notes"] == 0


def test_archiving_can_move_the_active_notes_instead(notes: Env) -> None:
    topic = _topic(notes, "Quelle")
    other = _topic(notes, "Anderswo")
    note = _note(notes, "bleibt aktiv", topic)
    assert _post(notes, topic, "archive", active_notes="move", move_to=other["uid"]).status_code == 200
    state = _note_state(notes, note)
    assert (state["topic_uid"], state["archived"]) == (other["uid"], False)


def test_a_note_cannot_move_into_an_archived_topic(notes: Env) -> None:
    topic = _topic(notes, "Zu")
    _post(notes, topic, "archive")
    note = _note(notes, "x")
    refused = notes.client.put(
        f"{API}/notes/{note['uid']}", json={"version": note["version"], "fields": {"topic": topic["uid"]}}
    )
    assert refused.json()["code"] == "topic_archived"

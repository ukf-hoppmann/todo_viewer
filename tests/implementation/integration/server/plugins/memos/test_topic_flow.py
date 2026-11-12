from __future__ import annotations

from typing import Any

from workspace_env import Env

API = "/api/memos"


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


def _memo(env: Env, summary: str, topic: dict[str, Any] | None = None) -> dict[str, Any]:
    fields: dict[str, Any] = {"summary": summary}
    if topic:
        fields["topic"] = topic["uid"]
    response = env.client.post(f"{API}/memos", json={"project": _project(env), "fields": fields})
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _post(env: Env, topic: dict[str, Any], action: str, **body: Any) -> Any:
    return env.client.post(f"{API}/topics/{topic['uid']}/{action}", json={"version": topic["version"], **body})


def _memo_state(env: Env, memo: dict[str, Any]) -> dict[str, Any]:
    return next(n for n in _index(env)["memos"] if n["uid"] == memo["uid"])


def test_topics_get_labels_and_memos_hang_below_them(memos: Env) -> None:
    topic = _topic(memos, "Ideen")
    memo = _memo(memos, "Eine Idee", topic)
    assert topic["label"] == "TOPIC-001"
    assert memos.client.get(f"{API}/memos/{memo['uid']}").json()["path"] == [
        {"uid": topic["uid"], "label": "TOPIC-001", "name": "Ideen"}
    ]
    assert _topic_in(memos, topic["uid"])["open_memos"] == 1


def test_counters_sum_open_memos_with_sub_topics_and_ignore_archived_ones(memos: Env) -> None:
    top = _topic(memos, "Oben")
    sub = _topic(memos, "Unten", top)
    _memo(memos, "a", top)
    done = _memo(memos, "b", sub)
    _memo(memos, "c", sub)
    memos.client.post(f"{API}/memos/{done['uid']}/finish", json={"version": done["version"], "status": "done"})
    assert (_topic_in(memos, top["uid"])["open_memos"], _topic_in(memos, sub["uid"])["open_memos"]) == (2, 1)


def test_the_depth_is_limited_by_the_setting(memos: Env) -> None:
    one = _topic(memos, "1")
    two = _topic(memos, "2", one)
    three = _topic(memos, "3", two)
    refused = memos.client.post(f"{API}/topics", json={"project": _project(memos), "name": "4", "parent": three["uid"]})
    assert (refused.status_code, refused.json()["code"]) == (400, "topic_too_deep")
    memos.client.put(f"{API}/settings", json={"max_topic_depth": 4})
    assert _topic(memos, "4", three)["name"] == "4"


def test_moving_checks_loops_and_depth(memos: Env) -> None:
    a = _topic(memos, "a")
    b = _topic(memos, "b", a)
    loop = _post(memos, a, "move", parent=b["uid"])
    assert loop.json()["code"] == "topic_loop"
    moved = _post(memos, b, "move", parent=None)
    assert moved.status_code == 200
    assert _topic_in(memos, b["uid"])["parent_uid"] is None


def test_a_topic_can_be_renamed_and_get_a_due_date(memos: Env) -> None:
    topic = _topic(memos, "Alt")
    renamed = memos.client.put(
        f"{API}/topics/{topic['uid']}",
        json={"version": topic["version"], "fields": {"name": "Neu", "due_at": "2026-12-01"}},
    )
    assert renamed.status_code == 200
    changed = _topic_in(memos, topic["uid"])
    assert (changed["name"], changed["due_at"][:10]) == ("Neu", "2026-12-01")
    cleared = memos.client.put(
        f"{API}/topics/{topic['uid']}", json={"version": changed["version"], "fields": {"due_at": None}}
    )
    assert cleared.status_code == 200 and _topic_in(memos, topic["uid"])["due_at"] is None


def test_a_memo_cannot_go_into_a_topic_of_another_project(memos: Env) -> None:
    other = memos.create("Anderes")
    topic = _topic(memos, "Dort", project=str(other["uid"]))
    refused = memos.client.post(
        f"{API}/memos", json={"project": _project(memos), "fields": {"summary": "x", "topic": topic["uid"]}}
    )
    assert refused.json()["code"] == "topic_other_project"


def test_an_empty_topic_is_deleted_at_once_and_comes_back_from_the_trash(memos: Env) -> None:
    topic = _topic(memos, "Leer")
    assert _post(memos, topic, "delete").json()["count"] == 1
    assert _index(memos)["topics"] == []
    restored = memos.client.post("/api/workspace/trash/restore", json={"uids": [topic["uid"]]})
    assert restored.status_code == 200
    assert [t["uid"] for t in _index(memos)["topics"]] == [topic["uid"]]


def test_deleting_a_topic_with_content_reports_the_numbers_and_changes_nothing(memos: Env) -> None:
    topic = _topic(memos, "Voll")
    _topic(memos, "Unter", topic)
    done = _memo(memos, "erledigt", topic)
    _memo(memos, "offen", topic)
    memos.client.post(f"{API}/memos/{done['uid']}/finish", json={"version": done["version"], "status": "done"})
    refused = _post(memos, topic, "delete")
    assert (refused.status_code, refused.json()["code"]) == (400, "topic_has_content")
    assert refused.json()["details"] == {"active": 1, "archived": 1, "topics": 1}
    content = memos.client.get(f"{API}/topics/{topic['uid']}/content").json()
    assert content == {"topics": 1, "active": 1, "archived": 1}
    assert len(_index(memos)["topics"]) == 2


def test_delete_with_keep_archived_and_move_hangs_memos_elsewhere(memos: Env) -> None:
    topic = _topic(memos, "Weg")
    target = _topic(memos, "Ziel")
    done = _memo(memos, "erledigt", topic)
    active = _memo(memos, "offen", topic)
    memos.client.post(f"{API}/memos/{done['uid']}/finish", json={"version": done["version"], "status": "done"})
    result = _post(memos, topic, "delete", keep_archived=True, active_memos="move", move_to=target["uid"])
    assert result.status_code == 200, result.text
    state = _index(memos)
    assert _memo_state(memos, active)["topic_uid"] == target["uid"]
    archive = next(t for t in state["topics"] if t["system"])
    assert archive["name"] == "Archiviert"
    kept = _memo_state(memos, done)
    assert (kept["topic_uid"], kept["status"], kept["archived"]) == (archive["uid"], "done", True)
    assert topic["uid"] not in [t["uid"] for t in state["topics"]]


def test_the_archive_topic_is_reused_and_cannot_be_deleted(memos: Env) -> None:
    for name in ("eins", "zwei"):
        topic = _topic(memos, name)
        done = _memo(memos, name, topic)
        memos.client.post(f"{API}/memos/{done['uid']}/finish", json={"version": done["version"], "status": "done"})
        assert _post(memos, topic, "delete", keep_archived=True, active_memos="delete").status_code == 200
    archives = [t for t in _index(memos)["topics"] if t["system"]]
    assert len(archives) == 1
    refused = _post(memos, archives[0], "delete")
    assert refused.json()["code"] == "topic_system"


def test_unchosen_groups_go_to_the_trash_and_come_back_with_the_topic(memos: Env) -> None:
    topic = _topic(memos, "Mit Inhalt")
    sub = _topic(memos, "Unter", topic)
    inner = _memo(memos, "innen", sub)
    assert _post(memos, topic, "delete", active_memos="delete").json()["count"] == 3
    assert _index(memos) == {"topics": [], "memos": []}
    blocked = memos.client.post("/api/workspace/trash/restore", json={"uids": [inner["uid"]]})
    assert blocked.status_code == 400 and blocked.json()["code"] == "topic_in_trash"
    assert memos.client.post("/api/workspace/trash/restore", json={"uids": [topic["uid"]]}).status_code == 200
    state = _index(memos)
    assert len(state["topics"]) == 2 and [n["uid"] for n in state["memos"]] == [inner["uid"]]


def test_archiving_hides_open_memos_with_the_topic_and_reactivating_brings_them_back(memos: Env) -> None:
    topic = _topic(memos, "Alt")
    sub = _topic(memos, "Sub", topic)
    open_memo = _memo(memos, "offen", sub)
    done = _memo(memos, "erledigt", topic)
    memos.client.post(f"{API}/memos/{done['uid']}/finish", json={"version": done["version"], "status": "dropped"})
    result = _post(memos, topic, "archive", active_memos="archive")
    assert result.status_code == 200, result.text
    state = _index(memos)
    assert all(t["archived"] for t in state["topics"])
    assert _memo_state(memos, open_memo)["archived"] is True
    assert _topic_in(memos, topic["uid"])["open_memos"] == 0
    back = _post(memos, _topic_in(memos, topic["uid"]), "reactivate")
    assert back.status_code == 200, back.text
    assert not any(t["archived"] for t in _index(memos)["topics"])
    assert _memo_state(memos, open_memo)["archived"] is False
    assert _memo_state(memos, done)["archived"] is True  # unabhängig archiviert, bleibt es


def test_memos_in_an_archived_topic_trigger_nothing(memos: Env) -> None:
    from datetime import timedelta

    topic = _topic(memos, "Ruhe")
    _memo(memos, "schläft", topic)
    _post(memos, topic, "archive", active_memos="archive")
    memos.clock.advance(timedelta(days=60))
    assert memos.client.get(f"{API}/due").json()["count"] == 0
    assert _topic_in(memos, topic["uid"])["due_memos"] == 0


def test_archiving_can_move_the_active_memos_instead(memos: Env) -> None:
    topic = _topic(memos, "Quelle")
    other = _topic(memos, "Anderswo")
    memo = _memo(memos, "bleibt aktiv", topic)
    assert _post(memos, topic, "archive", active_memos="move", move_to=other["uid"]).status_code == 200
    state = _memo_state(memos, memo)
    assert (state["topic_uid"], state["archived"]) == (other["uid"], False)


def test_a_memo_cannot_move_into_an_archived_topic(memos: Env) -> None:
    topic = _topic(memos, "Zu")
    _post(memos, topic, "archive")
    memo = _memo(memos, "x")
    refused = memos.client.put(
        f"{API}/memos/{memo['uid']}", json={"version": memo["version"], "fields": {"topic": topic["uid"]}}
    )
    assert refused.json()["code"] == "topic_archived"

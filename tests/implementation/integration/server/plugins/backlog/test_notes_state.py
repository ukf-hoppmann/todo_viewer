"""Der Kopf der Item-Notes über HTTP: lesen, ersetzen, bestätigen, Einträge lesen, `append_note` mit Kopf, Hinweise."""

from __future__ import annotations

from typing import Any

from workspace_env import Env

BASE = {"title": "Ein Item", "goal": "Ziel", "completion_criteria": "Kriterien"}


def _head(goal: str, decided: str = "") -> str:
    return f"- Goal/Status: {goal}\n- Next step: weiter\n- Open: -\n- Decided:{decided or ' -'}\n- References: -"


STATE = _head("läuft")
NEW_STATE = _head("neu")


def _create(env: Env, **fields: Any) -> dict[str, Any]:
    body = {"project": str(env.general()["uid"]), "type": "Task", "fields": {**BASE, "summary": "Kurz", **fields}}
    return env.client.post("/api/backlog/items", json=body).json()  # type: ignore[no-any-return]


def _note(env: Env, item: dict[str, Any], topic: str = "Thema", **body: Any) -> Any:
    payload = {"topic": topic, "discussed": ["Besprochen"], "decided": [], "open": [], **body}
    return env.client.post(f"/api/backlog/items/{item['uid']}/notes", json=payload)


def _state(env: Env, item: dict[str, Any]) -> Any:
    return env.client.get(f"/api/backlog/items/{item['uid']}/notes/state")


def _put(env: Env, item: dict[str, Any], content: str, version: int) -> Any:
    return env.client.put(
        f"/api/backlog/items/{item['uid']}/notes/state", json={"content": content, "version": version}
    )


def _confirm(env: Env, item: dict[str, Any], version: int) -> Any:
    return env.client.post(f"/api/backlog/items/{item['uid']}/notes/state/confirm", json={"version": version})


def test_notes_without_state_are_missing_and_an_item_without_notes_has_none(backlog: Env) -> None:
    item = _create(backlog)
    assert (_state(backlog, item).status_code, _state(backlog, item).json()["code"]) == (400, "notes_not_found")
    _note(backlog, item)

    state = _state(backlog, item).json()

    assert state["state"] == "missing" and state["content"] == "" and state["stamp"] is None
    assert state["name"] == "TASK-001_notes.md" and state["version"] == 1
    assert state["last_entry"] == {"day": "2026-10-16", "topic": "Thema"}
    assert len(state["checksum"]) == 12


def test_replacing_the_state_stamps_it_and_needs_the_current_version(backlog: Env) -> None:
    item = _create(backlog)
    _note(backlog, item)

    stored = _put(backlog, item, STATE, 1).json()
    stale = _put(backlog, item, _head("alt"), 1)

    assert stored["state"] == "current" and stored["content"] == STATE and stored["version"] == 2
    assert stored["stamp"] == {"day": "2026-10-16", "topic": "Thema", "checksum": stored["checksum"]}
    assert stored["hints"] == []
    assert (stale.status_code, stale.json()["code"]) == (409, "version_conflict")
    document = backlog.client.get(f"/api/backlog/items/{item['uid']}/documents/TASK-001_notes.md").json()
    assert f"## State\n\n{STATE}\n\nState confirmed after entry 2026-10-16 — Thema (" in document["content"]


def test_a_state_without_entries_is_refused(backlog: Env) -> None:
    item = _create(backlog)
    backlog.client.put(
        f"/api/backlog/items/{item['uid']}/documents/TASK-001_notes.md", json={"content": "# T\n\nNur Vorspann.\n"}
    )

    refused = _put(backlog, item, STATE, 1)

    assert (refused.status_code, refused.json()["code"]) == (400, "notes_without_entries")


def test_confirming_keeps_the_content_and_renews_the_stamp(backlog: Env) -> None:
    item = _create(backlog)
    _note(backlog, item)
    assert (_confirm(backlog, item, 1).status_code, _confirm(backlog, item, 1).json()["code"]) == (
        400,
        "notes_state_missing",
    )
    _put(backlog, item, STATE, 1)
    appended = _note(backlog, item, "Zweites").json()
    assert appended["notes_state"] == "stale"
    assert [h["code"] for h in appended["hints"]] == ["notes_state_stale"]

    confirmed = _confirm(backlog, item, 2).json()

    assert confirmed["state"] == "current" and confirmed["content"] == STATE and confirmed["version"] == 3
    assert confirmed["stamp"]["topic"] == "Zweites"


def test_append_note_can_bring_a_new_state(backlog: Env) -> None:
    item = _create(backlog)
    first = _note(backlog, item, state=STATE).json()
    assert first["notes_state"] == "current" and first["hints"] == []
    assert "State confirmed after entry 2026-10-16 — Thema (" in first["content"]

    refused = _note(backlog, item, "Zweites", state=NEW_STATE)
    second = _note(backlog, item, "Zweites", state=NEW_STATE, state_version=1).json()

    assert (refused.status_code, refused.json()["code"]) == (422, "invalid_input")
    assert second["notes_state"] == "current"
    state = _state(backlog, item).json()
    assert state["content"] == NEW_STATE and state["stamp"]["topic"] == "Zweites"
    assert state["version"] == 2


def test_rewriting_an_older_entry_by_put_gives_a_hint(backlog: Env) -> None:
    item = _create(backlog)
    _note(backlog, item)
    _note(backlog, item, "Zweites")
    document = backlog.client.get(f"/api/backlog/items/{item['uid']}/documents/TASK-001_notes.md").json()

    replaced = backlog.client.put(
        f"/api/backlog/items/{item['uid']}/documents/TASK-001_notes.md",
        json={
            "content": document["content"].replace("- Besprochen", "- Korrigiert", 1),
            "version": document["version"],
        },
    ).json()

    assert [h["code"] for h in replaced["hints"]] == ["notes_state_stale", "notes_history_rewritten"]
    assert replaced["notes_state"] == "missing"


def test_a_long_state_gives_a_hint(backlog: Env) -> None:
    item = _create(backlog)
    _note(backlog, item)
    decided = "".join(f"  - Beschluss {n}\n" for n in range(16))

    stored = _put(backlog, item, _head("x", f"\n{decided}".rstrip("\n")), 1).json()

    assert stored["state"] == "current"
    assert [h["code"] for h in stored["hints"]] == ["notes_state_long"]


def test_the_last_entries_can_be_read_without_the_rest(backlog: Env) -> None:
    item = _create(backlog)
    _note(backlog, item)
    _note(backlog, item, "Zweites")

    every = backlog.client.get(f"/api/backlog/items/{item['uid']}/notes/entries").json()
    last = backlog.client.get(f"/api/backlog/items/{item['uid']}/notes/entries", params={"last": 1}).json()

    assert [(e["position"], e["topic"]) for e in every] == [(0, "Thema"), (1, "Zweites")]
    assert last == [every[1]]
    assert last[0]["text"].startswith("## 2026-10-16 — Zweites\n")


def test_state_changes_are_public_events_and_mcp_tools(backlog: Env) -> None:
    item = _create(backlog)
    _note(backlog, item)
    seen: list[tuple[str, str]] = []
    backlog.app.state.events.subscribe(
        "backlog.document.changed", lambda e: seen.append((e.payload["name"], e.payload["change"]))
    )

    _put(backlog, item, STATE, 1)

    assert seen == [("TASK-001_notes.md", "updated")]
    names = {
        op.name
        for p in backlog.app.state.plugin_host.plugins
        if p.definition.id == "backlog"
        for op in p.definition.operations
        if op.mcp
    }
    assert {"get_notes_state", "put_notes_state", "confirm_notes_state", "list_notes_entries"} <= names

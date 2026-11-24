from __future__ import annotations

from typing import Any

from workspace_env import Env

BASE = {"title": "Ein Item", "goal": "Ziel", "completion_criteria": "Kriterien"}


def _create(env: Env, type_: str = "Task", **fields: Any) -> dict[str, Any]:
    body = {"project": str(env.general()["uid"]), "type": type_, "fields": {**BASE, **fields}}
    return env.client.post("/api/backlog/items", json=body).json()  # type: ignore[no-any-return]


def _note(env: Env, item: dict[str, Any], **body: Any) -> Any:
    payload = {"topic": "Thema", "discussed": ["Besprochen"], "decided": [], "open": [], **body}
    return env.client.post(f"/api/backlog/items/{item['uid']}/notes", json=payload)


def _documents(env: Env, uid: str) -> list[dict[str, Any]]:
    return env.client.get(f"/api/backlog/items/{uid}/documents").json()  # type: ignore[no-any-return]


def test_the_first_note_needs_a_summary_and_creates_the_notes_document(backlog: Env) -> None:
    item = _create(backlog)

    refused = _note(backlog, item)
    created = _note(backlog, item, summary="Kurzfassung")

    assert (refused.status_code, refused.json()["code"]) == (400, "summary_required_with_notes")
    body = created.json()
    assert body["name"] == "TASK-001_notes.md" and body["kind"] == "notes" and body["version"] == 1
    assert body["content"] == ("# TASK-001 — Ein Item\n\n## 2026-10-16 — Thema\n\n### Discussed\n\n- Besprochen\n")
    detail = backlog.client.get(f"/api/backlog/items/{item['uid']}").json()
    assert (detail["summary"], detail["notes"], detail["spec"]) == ("Kurzfassung", ["TASK-001_notes.md"], [])
    assert detail["version"] == 2  # die Kurzfassung ändert das Item


def test_a_refused_first_note_leaves_nothing_behind(backlog: Env) -> None:
    item = _create(backlog)

    _note(backlog, item)

    assert _documents(backlog, item["uid"]) == []
    assert backlog.client.get(f"/api/backlog/items/{item['uid']}").json()["notes"] == []


def test_a_summary_that_is_already_there_is_enough(backlog: Env) -> None:
    item = _create(backlog, summary="Schon da")

    assert _note(backlog, item).status_code == 200


def test_further_entries_are_appended_and_raise_the_version(backlog: Env) -> None:
    item = _create(backlog, summary="Kurz")
    _note(backlog, item)

    second = _note(backlog, item, topic="Zweites", discussed=[], decided=["Entschieden"], open=["Offen"]).json()

    assert second["version"] == 2
    assert second["content"].endswith(
        "\n## 2026-10-16 — Zweites\n\n### Decided\n\n- Entschieden\n\n### Open\n\n- Offen\n"
    )
    assert second["content"].count("## 2026-10-16") == 2


def test_an_entry_needs_a_topic_and_a_bullet(backlog: Env) -> None:
    item = _create(backlog, summary="Kurz")

    assert _note(backlog, item, topic=" ").json()["code"] == "value_required"
    assert _note(backlog, item, discussed=[]).json()["code"] == "value_required"


def test_list_and_get_documents(backlog: Env) -> None:
    item = _create(backlog, summary="Kurz")
    _note(backlog, item)
    backlog.client.put(f"/api/backlog/items/{item['uid']}/documents/TASK-001_spec.md", json={"content": "# Spec\n"})

    listed = _documents(backlog, item["uid"])
    one = backlog.client.get(f"/api/backlog/items/{item['uid']}/documents/TASK-001_spec.md").json()
    missing = backlog.client.get(f"/api/backlog/items/{item['uid']}/documents/TASK-001_spec_x.md")

    assert [(d["name"], d["kind"], d["version"]) for d in listed] == [
        ("TASK-001_notes.md", "notes", 1),
        ("TASK-001_spec.md", "spec", 1),
    ]
    assert one["content"] == "# Spec\n"
    assert (missing.status_code, missing.json()["code"]) == (400, "document_not_found")


def test_put_creates_a_new_spec_and_replaces_in_the_given_version(backlog: Env) -> None:
    item = _create(backlog)
    url = f"/api/backlog/items/{item['uid']}/documents/TASK-001_spec_Server.md"

    created = backlog.client.put(url, json={"content": "# Eins\n"})
    again = backlog.client.put(url, json={"content": "# Neu\n"})
    replaced = backlog.client.put(url, json={"content": "# Zwei\n", "version": 1})
    stale = backlog.client.put(url, json={"content": "# Drei\n", "version": 1})

    assert created.json()["version"] == 1
    assert (again.status_code, again.json()["code"]) == (400, "document_exists")
    assert replaced.json()["version"] == 2
    assert (stale.status_code, stale.json()["code"]) == (409, "version_conflict")
    assert backlog.client.get(url).json()["content"] == "# Zwei\n"


def test_put_refuses_unusual_names_and_a_replacement_of_something_missing(backlog: Env) -> None:
    item = _create(backlog)
    base = f"/api/backlog/items/{item['uid']}/documents/"

    bad = backlog.client.put(base + "irgendwas.md", json={"content": "x"})
    other_label = backlog.client.put(base + "TASK-099_spec.md", json={"content": "x"})
    missing = backlog.client.put(base + "TASK-001_spec.md", json={"content": "x", "version": 1})

    assert (bad.status_code, bad.json()["code"]) == (422, "invalid_input")
    assert other_label.status_code == 422
    assert missing.json()["code"] == "document_not_found"


def test_the_notes_document_by_put_needs_a_summary_too(backlog: Env) -> None:
    item = _create(backlog)
    url = f"/api/backlog/items/{item['uid']}/documents/TASK-001_notes.md"

    refused = backlog.client.put(url, json={"content": "# Notizen\n"})
    created = backlog.client.put(url, json={"content": "# Notizen\n", "summary": "Kurz"})

    assert refused.json()["code"] == "summary_required_with_notes"
    assert created.status_code == 200


def test_the_summary_of_an_item_with_notes_cannot_be_removed(backlog: Env) -> None:
    item = _create(backlog, summary="Kurz")
    _note(backlog, item)
    current = backlog.client.get(f"/api/backlog/items/{item['uid']}").json()

    r = backlog.client.put(
        f"/api/backlog/items/{item['uid']}", json={"version": current["version"], "fields": {"summary": ""}}
    )

    assert r.json()["code"] == "summary_required_with_notes"


def test_a_type_change_renames_the_documents_and_keeps_their_content(backlog: Env) -> None:
    item = _create(backlog, "Story", summary="Kurz")
    _note(backlog, item)
    backlog.client.put(
        f"/api/backlog/items/{item['uid']}/documents/STORY-001_spec_Teil.md", json={"content": "# Teil\n"}
    )
    current = backlog.client.get(f"/api/backlog/items/{item['uid']}").json()

    r = backlog.client.post(
        f"/api/backlog/items/{item['uid']}/retype", json={"version": current["version"], "type": "Task"}
    )

    new_label = r.json()["new_label"]
    assert new_label == "TASK-001"
    names = [d["name"] for d in _documents(backlog, item["uid"])]
    assert names == [f"{new_label}_notes.md", f"{new_label}_spec_Teil.md"]
    detail = backlog.client.get(f"/api/backlog/items/{item['uid']}").json()
    assert (detail["notes"], detail["spec"]) == ([f"{new_label}_notes.md"], [f"{new_label}_spec_Teil.md"])
    first = backlog.client.get(f"/api/backlog/items/{item['uid']}/documents/{new_label}_notes.md").json()
    assert first["content"].startswith("# TASK-001 — Ein Item\n\n## 2026-10-16 — Thema\n")  # Titelzeile folgt dem Typ


def test_documents_go_with_the_item_when_it_is_purged_and_stay_in_the_trash(backlog: Env) -> None:
    item = _create(backlog, summary="Kurz")
    _note(backlog, item)

    version = backlog.client.get(f"/api/backlog/items/{item['uid']}").json()["version"]
    backlog.client.delete(f"/api/workspace/elements/{item['uid']}", params={"version": version})
    still = _documents(backlog, item["uid"])
    backlog.client.post("/api/workspace/trash/purge", json={"uids": [item["uid"]]})

    assert len(still) == 1
    with backlog.app.state.database.transaction() as tx:
        assert tx.connection.exec_driver_sql("SELECT COUNT(*) FROM backlog_documents").scalar() == 0


def test_document_changes_are_public_events(backlog: Env) -> None:
    item = _create(backlog, summary="Kurz")
    seen: list[tuple[bool, str, str]] = []
    backlog.app.state.events.subscribe(
        "backlog.document.changed", lambda e: seen.append((e.public, e.payload["name"], e.payload["change"]))
    )

    _note(backlog, item)
    _note(backlog, item, topic="Noch eins")

    assert seen == [(True, "TASK-001_notes.md", "created"), (True, "TASK-001_notes.md", "updated")]


def test_the_document_operations_are_mcp_tools(backlog: Env) -> None:
    names = {
        op.name
        for p in backlog.app.state.plugin_host.plugins
        if p.definition.id == "backlog"
        for op in p.definition.operations
        if op.mcp
    }

    assert {"list_documents", "get_document", "put_document", "append_note"} <= names


STATE = "## State\n\n- Goal/Status: läuft\n\n"


def _notes_doc(env: Env, item: dict[str, Any]) -> dict[str, Any]:
    return env.client.get(f"/api/backlog/items/{item['uid']}/documents/TASK-001_notes.md").json()  # type: ignore[no-any-return]


def _put_notes(env: Env, item: dict[str, Any], content: str, version: int) -> Any:
    return env.client.put(
        f"/api/backlog/items/{item['uid']}/documents/TASK-001_notes.md", json={"content": content, "version": version}
    )


def test_put_without_a_state_section_keeps_the_state(backlog: Env) -> None:
    item = _create(backlog, summary="Kurz")
    first = _note(backlog, item).json()
    with_state = first["content"].replace("\n\n## 2026", f"\n\n{STATE}## 2026", 1)
    assert _put_notes(backlog, item, with_state, 1).status_code == 200

    replaced = _put_notes(backlog, item, first["content"] + "\n## 2026-10-16 — Von Hand\n\n- x\n", 2).json()

    assert replaced["version"] == 3
    assert STATE in replaced["content"]
    assert replaced["content"].endswith("## 2026-10-16 — Von Hand\n\n- x\n")
    assert _notes_doc(backlog, item)["content"] == replaced["content"]


def test_a_stamp_line_in_put_is_ignored(backlog: Env) -> None:
    item = _create(backlog, summary="Kurz")
    first = _note(backlog, item).json()
    stamp = "State confirmed after entry 2026-10-16 — Thema (0123456789ab)\n\n"

    stored = _put_notes(backlog, item, first["content"].replace("\n\n## 2026", f"\n\n{STATE}{stamp}## 2026", 1), 1)

    assert STATE in stored.json()["content"]
    assert "State confirmed" not in stored.json()["content"]


def test_notes_without_state_keep_their_text_through_put(backlog: Env) -> None:
    item = _create(backlog, summary="Kurz")
    first = _note(backlog, item).json()
    text = first["content"].replace("\n\n## 2026", "\n\n## Summary\n\nAlter Vorspann.\n\n## 2026", 1)

    stored = _put_notes(backlog, item, text, 1).json()

    assert stored["content"] == text
    appended = _note(backlog, item, topic="Zweites").json()
    assert appended["version"] == 3
    assert appended["content"].startswith(text)

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from viewer.plugins.backlog.domain.model import KIND_BY_TYPE, Item
from workspace_env import Env


def _add(
    env: Env,
    project: str,
    type_: str,
    title: str,
    *,
    parent: Any = None,
    status: str = "Open",
    priority: str = "Normal",
    required: bool | None = None,
    dependencies: tuple[str, ...] = (),
) -> Item:
    database = env.backlog.repository
    registry = env.workspace.registry
    with env.app.state.database.transaction() as tx:
        element = registry.register(tx, project, KIND_BY_TYPE[type_], title)
        item = Item(
            uid=element.uid,
            project_uid=project,
            label=element.label,
            type=type_,
            title=title,
            status=status,
            priority=priority,
            parent_uid=parent.uid if parent else None,
            required_for_parent=required,
            goal="Ziel",
            completion_criteria="Kriterien",
            summary=None,
            resolution=None,
            created=date(2026, 10, 16),
            position=0,
            revision=element.revision,
            dependencies=dependencies,
        )
        database.insert(tx, item)
    return item


def _list(env: Env, **params: Any) -> list[dict[str, Any]]:
    response = env.client.get("/api/backlog/items", params=params)
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def test_items_get_register_labels_per_type(backlog: Env) -> None:
    project = str(backlog.general()["uid"])

    epic = _add(backlog, project, "Epic", "E")
    story = _add(backlog, project, "Story", "S", parent=epic)
    task = _add(backlog, project, "Task", "T", parent=story)
    task2 = _add(backlog, project, "Task", "T2", parent=story)

    assert [i.label for i in (epic, story, task, task2)] == ["EPIC-001", "STORY-001", "TASK-001", "TASK-002"]


def test_list_items_returns_a_flat_index_with_progress(backlog: Env) -> None:
    project = str(backlog.general()["uid"])
    epic = _add(backlog, project, "Epic", "E", priority="Urgent")
    story = _add(backlog, project, "Story", "S", parent=epic, status="In progress")
    _add(backlog, project, "Task", "T1", parent=story, status="Completed")
    _add(backlog, project, "Task", "T2", parent=story)

    index = {e["label"]: e for e in _list(backlog)}

    assert set(index) == {"EPIC-001", "STORY-001", "TASK-001", "TASK-002"}
    assert index["EPIC-001"]["progress"] == {"done": 1, "total": 3}
    assert index["STORY-001"]["progress"] == {"done": 1, "total": 2}
    assert index["TASK-001"]["progress"] is None
    assert index["STORY-001"]["parent_uid"] == epic.uid
    assert (index["EPIC-001"]["priority"], index["EPIC-001"]["type"]) == ("Urgent", "Epic")
    assert "area" not in index["EPIC-001"]
    assert index["EPIC-001"]["version"] == 1
    assert index["EPIC-001"]["dependencies"] == []


def test_the_index_names_the_dependencies_by_uid(backlog: Env) -> None:
    project = str(backlog.general()["uid"])
    first = _add(backlog, project, "Task", "Erst")
    _add(backlog, project, "Task", "Danach", dependencies=(first.uid,))

    index = {e["title"]: e for e in _list(backlog)}

    assert index["Danach"]["dependencies"] == [first.uid]
    assert index["Erst"]["dependencies"] == []


def test_optional_and_rejected_items_do_not_count_for_the_progress(backlog: Env) -> None:
    project = str(backlog.general()["uid"])
    epic = _add(backlog, project, "Epic", "E")
    _add(backlog, project, "Story", "optional", parent=epic, required=False)
    _add(backlog, project, "Story", "abgelehnt", parent=epic, status="Rejected")
    _add(backlog, project, "Story", "fertig", parent=epic, status="Completed")

    assert {e["label"]: e["progress"] for e in _list(backlog)}["EPIC-001"] == {"done": 1, "total": 1}


def test_filters_by_projects_status_priority_and_text_but_progress_ignores_them(backlog: Env) -> None:
    general = str(backlog.general()["uid"])
    other = str(backlog.create("Anderes")["uid"])
    epic = _add(backlog, general, "Epic", "Sync-Epic", priority="Urgent")
    _add(backlog, general, "Task", "Sync reparieren", parent=epic, status="Completed")
    _add(backlog, general, "Task", "Offen", parent=epic)
    _add(backlog, other, "Task", "Fremd", priority="Prospective")

    assert len(_list(backlog)) == 4
    assert {e["title"] for e in _list(backlog, projects=other)} == {"Fremd"}
    assert {e["title"] for e in _list(backlog, projects=f"{general},{other}", statuses="Open")} == {
        "Sync-Epic",
        "Offen",
        "Fremd",
    }
    assert {e["title"] for e in _list(backlog, priorities="Urgent,Prospective")} == {"Sync-Epic", "Fremd"}
    assert {e["title"] for e in _list(backlog, query="sync")} == {"Sync-Epic", "Sync reparieren"}
    assert _list(backlog, projects="") == []
    filtered = {e["title"]: e["progress"] for e in _list(backlog, statuses="Open")}
    assert filtered["Sync-Epic"] == {"done": 1, "total": 2}


def test_unknown_filter_values_are_refused(backlog: Env) -> None:
    for params in ({"statuses": "Kaputt"}, {"priorities": "Egal"}):
        r = backlog.client.get("/api/backlog/items", params=params)
        assert (r.status_code, r.json()["code"]) == (422, "invalid_input")


def test_items_in_the_trash_are_not_listed(backlog: Env) -> None:
    project = str(backlog.general()["uid"])
    gone = _add(backlog, project, "Task", "Weg")
    _add(backlog, project, "Task", "Da")

    backlog.client.delete(f"/api/workspace/elements/{gone.uid}", params={"version": 1})

    assert [e["title"] for e in _list(backlog)] == ["Da"]


def test_get_item_by_uid_returns_all_fields_children_and_dependencies(backlog: Env) -> None:
    project = str(backlog.general()["uid"])
    epic = _add(backlog, project, "Epic", "E")
    first = _add(backlog, project, "Task", "Erst", parent=epic)
    second = _add(backlog, project, "Task", "Danach", parent=epic, dependencies=(first.uid,))
    gone = _add(backlog, project, "Task", "Gelöscht", parent=epic)
    backlog.client.delete(f"/api/workspace/elements/{gone.uid}", params={"version": 1})

    parent = backlog.client.get(f"/api/backlog/items/{epic.uid}").json()
    child = backlog.client.get(f"/api/backlog/items/{second.uid}").json()

    assert [(c["label"], c["deleted"]) for c in parent["children"]] == [
        ("TASK-001", False),
        ("TASK-002", False),
        ("TASK-003", True),
    ]
    assert parent["progress"] == {"done": 0, "total": 2}
    assert (parent["goal"], parent["completion_criteria"], parent["created"], parent["version"]) == (
        "Ziel",
        "Kriterien",
        "2026-10-16",
        1,
    )
    assert child["parent"]["label"] == "EPIC-001"
    assert [d["label"] for d in child["dependencies"]] == ["TASK-001"]
    assert (child["status"], child["priority"], child["deleted"]) == ("Open", "Normal", False)
    assert "area" not in child


def test_get_item_by_label_needs_the_project_and_finds_earlier_labels(backlog: Env) -> None:
    project = str(backlog.general()["uid"])
    task = _add(backlog, project, "Task", "T")
    with backlog.app.state.database.transaction() as tx:
        backlog.workspace.registry.relabel(tx, task.uid, "story")

    current = backlog.client.get("/api/backlog/items/STORY-001", params={"project": project})
    earlier = backlog.client.get("/api/backlog/items/TASK-001", params={"project": project})
    no_project = backlog.client.get("/api/backlog/items/TASK-001")
    unknown = backlog.client.get("/api/backlog/items/TASK-099", params={"project": project})

    assert current.json()["uid"] == earlier.json()["uid"] == task.uid
    assert (no_project.status_code, no_project.json()["code"]) == (422, "invalid_input")
    assert (unknown.status_code, unknown.json()["code"]) == (404, "not_found")
    assert backlog.client.get(f"/api/backlog/items/{task.uid}").status_code == 200


def test_a_deleted_item_can_still_be_read_and_says_so(backlog: Env) -> None:
    task = _add(backlog, str(backlog.general()["uid"]), "Task", "T")
    backlog.client.delete(f"/api/workspace/elements/{task.uid}", params={"version": 1})

    assert backlog.client.get(f"/api/backlog/items/{task.uid}").json()["deleted"] is True


def test_there_is_no_area_table_or_column(backlog: Env) -> None:
    with backlog.app.state.database.transaction() as tx:
        tables = {r[0] for r in tx.connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type = 'table'")}
        columns = {r[1] for r in tx.connection.exec_driver_sql("PRAGMA table_info(backlog_items)")}
    assert "backlog_areas" not in tables and "area_uid" not in columns


def test_the_value_lists_are_enforced_by_the_database(backlog: Env) -> None:
    project = str(backlog.general()["uid"])

    with pytest.raises(Exception, match="FOREIGN KEY|CHECK|constraint"):
        _add(backlog, project, "Task", "Kaputt", status="Erfunden")
    with backlog.app.state.database.transaction() as tx:
        codes = [r[0] for r in tx.connection.exec_driver_sql("SELECT code FROM backlog_priorities ORDER BY rank").all()]
    assert codes == ["Urgent", "Important", "Normal", "Prospective"]


def test_the_read_operations_are_mcp_tools(backlog: Env) -> None:
    names = {
        op.name
        for p in backlog.app.state.plugin_host.plugins
        if p.definition.id == "backlog"
        for op in p.definition.operations
        if op.mcp
    }

    assert {"list_items", "get_item"} <= names


def test_trash_cascade_and_restore_rule_work_for_backlog_items(backlog: Env) -> None:
    project = str(backlog.general()["uid"])
    epic = _add(backlog, project, "Epic", "E")
    story = _add(backlog, project, "Story", "S", parent=epic)
    task = _add(backlog, project, "Task", "T", parent=story)

    asked = backlog.client.delete(f"/api/workspace/elements/{epic.uid}", params={"version": 1})
    done = backlog.client.delete(f"/api/workspace/elements/{epic.uid}", params={"version": 1, "cascade": True})
    refused = backlog.client.post("/api/workspace/trash/restore", json={"uids": [story.uid]})
    restored = backlog.client.post("/api/workspace/trash/restore", json={"uids": [epic.uid]})

    assert asked.json()["has_children"] is True and done.json()["deleted"] == 3
    assert (refused.status_code, refused.json()["code"]) == (400, "parent_in_trash")
    assert sorted(restored.json()["uids"]) == sorted([epic.uid, story.uid, task.uid])
    assert len(_list(backlog)) == 3


def test_purging_removes_the_backlog_rows_and_dependencies(backlog: Env) -> None:
    project = str(backlog.general()["uid"])
    first = _add(backlog, project, "Task", "Erst")
    second = _add(backlog, project, "Task", "Danach", dependencies=(first.uid,))
    backlog.client.delete(f"/api/workspace/elements/{first.uid}", params={"version": 1})

    purged = backlog.client.post("/api/workspace/trash/purge", json={"uids": [first.uid]})

    assert purged.status_code == 200
    assert backlog.client.get(f"/api/backlog/items/{first.uid}").status_code == 404
    assert backlog.client.get(f"/api/backlog/items/{second.uid}").json()["dependencies"] == []


def test_show_and_index_name_the_state_of_the_notes_head(backlog: Env) -> None:
    project = str(backlog.general()["uid"])
    items = {name: _add(backlog, project, "Task", name) for name in ("Ohne", "Fehlt", "Aktuell", "Veraltet")}
    for name in ("Fehlt", "Aktuell", "Veraltet"):
        uid = items[name].uid
        backlog.client.post(
            f"/api/backlog/items/{uid}/notes",
            json={"topic": "T", "discussed": ["x"], "summary": "Kurz", **({} if name == "Fehlt" else {"state": "- Z"})},
        )
    backlog.client.post(f"/api/backlog/items/{items['Veraltet'].uid}/notes", json={"topic": "Neu", "discussed": ["y"]})

    states = {
        name: backlog.client.get(f"/api/backlog/items/{i.uid}").json()["notes_state"] for name, i in items.items()
    }
    lines = backlog.client.get("/api/backlog/index", params={"projects": project}).json()["text"].splitlines()

    assert states == {"Ohne": None, "Fehlt": "missing", "Aktuell": "current", "Veraltet": "stale"}
    assert lines[0] == "ID | Type | Status | Title | Parent | Notes"
    assert {line.split(" | ")[3]: line.split(" | ")[5] for line in lines[1:]} == {
        "Ohne": "-",
        "Fehlt": "missing",
        "Aktuell": "current",
        "Veraltet": "stale",
    }

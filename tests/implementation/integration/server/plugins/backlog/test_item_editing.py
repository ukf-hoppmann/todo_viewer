from __future__ import annotations

from typing import Any

from workspace_env import Env

BASE = {"title": "Neues Item", "area": "Server", "goal": "Ziel", "completion_criteria": "Kriterien"}


def _project(env: Env) -> str:
    return str(env.general()["uid"])


def _create(env: Env, type_: str = "Task", project: str | None = None, **fields: Any) -> dict[str, Any]:
    r = env.client.post(
        "/api/backlog/items", json={"project": project or _project(env), "type": type_, "fields": {**BASE, **fields}}
    )
    assert r.status_code == 200, r.text
    return r.json()  # type: ignore[no-any-return]


def _update(
    env: Env, item: dict[str, Any], fields: dict[str, Any], resolution: str | None = None, version: int | None = None
) -> Any:
    body = {"version": version or item["version"], "fields": fields, "resolution": resolution}
    return env.client.put(f"/api/backlog/items/{item['uid']}", json=body)


def _get(env: Env, uid: str) -> dict[str, Any]:
    return env.client.get(f"/api/backlog/items/{uid}").json()  # type: ignore[no-any-return]


def _code(response: Any) -> str:
    return response.json()["code"]  # type: ignore[no-any-return]


def test_create_gives_a_register_label_status_open_and_todays_date(backlog: Env) -> None:
    epic = _create(backlog, "Epic")
    story = _create(backlog, "Story", parent=epic["uid"], required_for_parent=True, priority="Urgent")

    assert (epic["label"], epic["status"], epic["priority"], epic["created"], epic["version"]) == (
        "EPIC-001",
        "Open",
        "Normal",
        "2026-10-16",
        1,
    )
    assert (story["label"], story["parent"]["label"], story["priority"], story["required_for_parent"]) == (
        "STORY-001",
        "EPIC-001",
        "Urgent",
        True,
    )
    assert [c["label"] for c in _get(backlog, epic["uid"])["children"]] == ["STORY-001"]


def test_create_refuses_missing_required_fields_and_leaves_no_trace(backlog: Env) -> None:
    for missing in ("title", "goal", "completion_criteria"):
        fields = {k: v for k, v in BASE.items() if k != missing}
        r = backlog.client.post(
            "/api/backlog/items", json={"project": _project(backlog), "type": "Task", "fields": fields}
        )
        assert (r.status_code, _code(r)) == (400, "value_required")

    assert _create(backlog)["label"] == "TASK-001"  # keine Nummer wurde verbraucht
    assert backlog.client.get("/api/backlog/items").json()[0]["label"] == "TASK-001"


def test_create_without_area_leaves_it_empty(backlog: Env) -> None:
    fields = {k: v for k, v in BASE.items() if k != "area"}
    r = backlog.client.post(
        "/api/backlog/items", json={"project": _project(backlog), "type": "Task", "fields": fields}
    )
    assert r.status_code == 200, r.text
    assert r.json()["area"] is None
    assert _get(backlog, r.json()["uid"])["area"] is None
    assert _create(backlog, area="Server")["area"] == "Server"


def test_create_checks_the_structure_rules(backlog: Env) -> None:
    epic = _create(backlog, "Epic")
    r = backlog.client.post(
        "/api/backlog/items",
        json={
            "project": _project(backlog),
            "type": "Epic",
            "fields": {**BASE, "parent": epic["uid"], "required_for_parent": True},
        },
    )
    no_flag = backlog.client.post(
        "/api/backlog/items",
        json={"project": _project(backlog), "type": "Task", "fields": {**BASE, "parent": epic["uid"]}},
    )
    ghost = backlog.client.post(
        "/api/backlog/items",
        json={"project": _project(backlog), "type": "Task", "fields": {**BASE, "dependencies": ["gibt-es-nicht"]}},
    )
    bad_type = backlog.client.post(
        "/api/backlog/items", json={"project": _project(backlog), "type": "Bug", "fields": BASE}
    )

    assert _code(r) == "epic_with_parent"
    assert _code(no_flag) == "required_for_parent_missing"
    assert _code(ghost) == "unknown_reference"
    assert (bad_type.status_code, _code(bad_type)) == (422, "invalid_input")
    assert backlog.client.get("/api/backlog/items").json()[0]["label"] == "EPIC-001"
    assert len(backlog.client.get("/api/backlog/items").json()) == 1


def test_a_parent_must_be_in_the_same_project(backlog: Env) -> None:
    other = str(backlog.create("Anderes")["uid"])
    epic = _create(backlog, "Epic", project=other)

    r = backlog.client.post(
        "/api/backlog/items",
        json={
            "project": _project(backlog),
            "type": "Task",
            "fields": {**BASE, "parent": epic["uid"], "required_for_parent": True},
        },
    )

    assert _code(r) == "unknown_reference"


def test_update_changes_fields_bumps_the_version_and_refuses_a_stale_one(backlog: Env) -> None:
    item = _create(backlog)

    r = _update(backlog, item, {"title": "Anders", "priority": "Important", "area": "Client", "summary": "Kurz"})
    stale = _update(backlog, item, {"title": "Zu spät"})

    body = r.json()
    assert (body["title"], body["priority"], body["area"], body["summary"], body["version"]) == (
        "Anders",
        "Important",
        "Client",
        "Kurz",
        2,
    )
    assert (stale.status_code, _code(stale)) == (409, "version_conflict")
    assert _get(backlog, item["uid"])["title"] == "Anders"
    found = backlog.client.get("/api/workspace/elements", params={"query": "anders"}).json()
    assert [e["uid"] for e in found] == [item["uid"]]  # der Titel im Register folgt


def test_update_by_label_needs_the_project(backlog: Env) -> None:
    item = _create(backlog)

    r = backlog.client.put(
        f"/api/backlog/items/{item['label']}",
        json={"version": 1, "fields": {"title": "Per Label"}, "project": _project(backlog)},
    )
    no_project = backlog.client.put(
        f"/api/backlog/items/{item['label']}", json={"version": 2, "fields": {"title": "X"}}
    )

    assert r.json()["title"] == "Per Label"
    assert (no_project.status_code, _code(no_project)) == (422, "invalid_input")


def test_update_refuses_unknown_fields_values_and_deleted_items(backlog: Env) -> None:
    item = _create(backlog)

    assert _code(_update(backlog, item, {"label": "X-1"})) == "not_editable"
    assert _update(backlog, item, {"priority": "Egal"}).status_code == 422
    assert _code(_update(backlog, item, {"goal": ""})) == "value_required"
    backlog.client.delete(f"/api/workspace/elements/{item['uid']}", params={"version": 1})
    assert _code(_update(backlog, item, {"title": "Weg"})) == "item_deleted"


def test_closing_needs_a_resolution_and_reopening_clears_it(backlog: Env) -> None:
    item = _create(backlog)

    without = _update(backlog, item, {"status": "Completed"})
    closed = _update(backlog, item, {"status": "Completed"}, "Bestätigt.").json()
    reopened = _update(backlog, closed, {"status": "In progress"}).json()

    assert _code(without) == "resolution_required"
    assert (closed["status"], closed["resolution"]) == ("Completed", "Bestätigt.")
    assert (reopened["status"], reopened["resolution"]) == ("In progress", None)


def test_the_epic_lifecycle_rules(backlog: Env) -> None:
    epic = _create(backlog, "Epic")

    early = _update(backlog, epic, {"status": "In progress"})
    story = _create(backlog, "Story", parent=epic["uid"], required_for_parent=True)
    started = _update(backlog, _get(backlog, epic["uid"]), {"status": "In progress"})
    close_early = _update(backlog, started.json(), {"status": "Completed"}, "Fertig")
    _update(backlog, story, {"status": "Completed"}, "Fertig")
    closed = _update(backlog, _get(backlog, epic["uid"]), {"status": "Completed"}, "Fertig")

    assert _code(early) == "epic_without_required_child"
    assert started.status_code == 200
    assert _code(close_early) in {"children_still_active", "required_children_not_done"}
    assert closed.status_code == 200


def test_a_new_active_child_below_a_closed_parent_names_the_ancestors_and_reopen_fixes_it(backlog: Env) -> None:
    epic = _create(backlog, "Epic")
    story = _create(backlog, "Story", parent=epic["uid"], required_for_parent=True)
    _update(backlog, story, {"status": "Completed"}, "Fertig")
    story = _get(backlog, story["uid"])
    _update(backlog, _get(backlog, epic["uid"]), {"status": "Completed"}, "Fertig")

    refused = backlog.client.post(
        "/api/backlog/items",
        json={
            "project": _project(backlog),
            "type": "Task",
            "fields": {**BASE, "parent": story["uid"], "required_for_parent": True},
        },
    )
    reopened = backlog.client.post(f"/api/backlog/items/{story['uid']}/reopen", json={})
    created = backlog.client.post(
        "/api/backlog/items",
        json={
            "project": _project(backlog),
            "type": "Task",
            "fields": {**BASE, "parent": story["uid"], "required_for_parent": True},
        },
    )

    assert _code(refused) == "parent_closed"
    assert [a["label"] for a in refused.json()["details"]["ancestors"]] == ["EPIC-001", "STORY-001"]
    assert [i["label"] for i in reopened.json()["reopened"]] == ["EPIC-001", "STORY-001"]
    assert created.status_code == 200
    assert (_get(backlog, epic["uid"])["status"], _get(backlog, story["uid"])["status"]) == (
        "In progress",
        "In progress",
    )
    assert _get(backlog, epic["uid"])["resolution"] is None


def test_reopen_does_nothing_for_an_item_that_is_not_closed(backlog: Env) -> None:
    item = _create(backlog)

    r = backlog.client.post(f"/api/backlog/items/{item['uid']}/reopen", json={})

    assert r.json() == {"reopened": []}


def test_dependencies_are_edited_and_cycles_refused(backlog: Env) -> None:
    a, b = _create(backlog), _create(backlog)

    ok = _update(backlog, b, {"dependencies": [a["uid"]]})
    cycle = _update(backlog, _get(backlog, a["uid"]), {"dependencies": [b["uid"]]})
    selfref = _update(backlog, _get(backlog, a["uid"]), {"dependencies": [a["uid"]]})

    assert [d["label"] for d in ok.json()["dependencies"]] == ["TASK-001"]
    assert _code(cycle) == "dependency_cycle"
    assert _code(selfref) == "dependency_cycle"


def test_changes_publish_events_and_status_changes_a_private_one_for_notes(backlog: Env) -> None:
    item = _create(backlog)
    seen: list[tuple[str, bool, dict[str, Any]]] = []
    backlog.app.state.events.subscribe("backlog.*", lambda e: seen.append((e.topic, e.public, e.payload)))

    _update(backlog, item, {"title": "Neu"})
    _update(backlog, _get(backlog, item["uid"]), {"status": "In progress"})

    assert [(topic, public) for topic, public, _ in seen] == [
        ("backlog.item.changed", True),
        ("backlog.item.changed", True),
        ("backlog.item.status_changed", False),
    ]
    assert seen[2][2] == {
        "uid": item["uid"],
        "label": "TASK-001",
        "project_uid": _project(backlog),
        "from": "Open",
        "to": "In progress",
    }


def test_move_changes_the_parent_and_the_order(backlog: Env) -> None:
    epic = _create(backlog, "Epic")
    s1, s2, s3 = (_create(backlog, "Story", parent=epic["uid"], required_for_parent=True) for _ in range(3))

    moved = backlog.client.post(
        f"/api/backlog/items/{s3['uid']}/move", json={"version": 1, "parent": epic["uid"], "position": 0}
    )

    assert moved.status_code == 200
    assert [c["label"] for c in _get(backlog, epic["uid"])["children"]] == ["STORY-003", "STORY-001", "STORY-002"]
    assert (s1["label"], s2["label"]) == ("STORY-001", "STORY-002")


def test_move_under_a_parent_makes_the_item_required_and_to_the_root_removes_it(backlog: Env) -> None:
    epic = _create(backlog, "Epic")
    task = _create(backlog, "Task")

    under = backlog.client.post(
        f"/api/backlog/items/{task['uid']}/move", json={"version": 1, "parent": epic["uid"], "position": 0}
    ).json()
    root = backlog.client.post(
        f"/api/backlog/items/{task['uid']}/move", json={"version": 2, "parent": None, "position": 0}
    ).json()

    assert (under["parent"]["label"], under["required_for_parent"]) == ("EPIC-001", True)
    assert (root["parent"], root["required_for_parent"]) == (None, None)


def test_move_checks_the_rules_and_the_version(backlog: Env) -> None:
    epic, other_epic = _create(backlog, "Epic"), _create(backlog, "Epic")
    story = _create(backlog, "Story", parent=epic["uid"], required_for_parent=True)
    task = _create(backlog, "Task", parent=story["uid"], required_for_parent=True)

    epic_under = backlog.client.post(
        f"/api/backlog/items/{other_epic['uid']}/move", json={"version": 1, "parent": epic["uid"], "position": 0}
    )
    cycle = backlog.client.post(
        f"/api/backlog/items/{epic['uid']}/move", json={"version": 1, "parent": task["uid"], "position": 0}
    )
    stale = backlog.client.post(
        f"/api/backlog/items/{task['uid']}/move", json={"version": 99, "parent": None, "position": 0}
    )

    assert _code(epic_under) == "epic_with_parent"
    assert _code(cycle) in {"parent_cycle", "epic_with_parent"}
    assert (stale.status_code, _code(stale)) == (409, "version_conflict")


def test_retype_gives_a_new_label_keeps_the_uid_and_rewrites_references(backlog: Env) -> None:
    story = _create(backlog, "Story", title="Original")
    mention = _create(backlog, "Task", goal="Folge von STORY-001", summary="Wie STORY-001 beschrieben")

    r = backlog.client.post(f"/api/backlog/items/{story['uid']}/retype", json={"version": 1, "type": "Task"})

    body = r.json()
    assert (body["old_label"], body["new_label"], body["item"]["uid"], body["item"]["type"]) == (
        "STORY-001",
        "TASK-002",
        story["uid"],
        "Task",
    )
    assert body["notices"][0]["code"] == "external_references_may_remain"
    assert body["notices"][0]["details"] == {"old_label": "STORY-001", "new_label": "TASK-002"}
    changed = _get(backlog, mention["uid"])
    assert (changed["goal"], changed["summary"], changed["version"]) == (
        "Folge von TASK-002",
        "Wie TASK-002 beschrieben",
        2,
    )
    old = backlog.client.get("/api/backlog/items/STORY-001", params={"project": _project(backlog)})
    assert old.json()["uid"] == story["uid"]


def test_retype_refuses_the_same_type_an_unknown_type_a_stale_version_and_broken_structure(backlog: Env) -> None:
    epic = _create(backlog, "Epic")
    story = _create(backlog, "Story", parent=epic["uid"], required_for_parent=True)

    same = backlog.client.post(f"/api/backlog/items/{story['uid']}/retype", json={"version": 1, "type": "Story"})
    unknown = backlog.client.post(f"/api/backlog/items/{story['uid']}/retype", json={"version": 1, "type": "Bug"})
    stale = backlog.client.post(f"/api/backlog/items/{story['uid']}/retype", json={"version": 9, "type": "Task"})
    to_epic = backlog.client.post(f"/api/backlog/items/{story['uid']}/retype", json={"version": 1, "type": "Epic"})

    assert same.status_code == unknown.status_code == 422
    assert (stale.status_code, _code(stale)) == (409, "version_conflict")
    assert _code(to_epic) == "epic_with_parent"
    assert _get(backlog, story["uid"])["label"] == "STORY-001"  # nichts blieb halb geändert


def test_areas_come_with_the_items_of_the_project(backlog: Env) -> None:
    other = str(backlog.create("Zwei")["uid"])
    _create(backlog, area="Server")
    _create(backlog, area="Client")
    _create(backlog, project=other, area="Nur zwei")

    areas = backlog.client.get("/api/backlog/areas", params={"project": _project(backlog)}).json()

    assert areas == {"areas": ["Client", "Server"]}


def test_the_editing_operations_are_mcp_tools(backlog: Env) -> None:
    names = {
        op.name
        for p in backlog.app.state.plugin_host.plugins
        if p.definition.id == "backlog"
        for op in p.definition.operations
        if op.mcp
    }

    assert {
        "list_items",
        "get_item",
        "create_item",
        "update_item",
        "move_item",
        "retype_item",
        "reopen_ancestors",
        "list_areas",
    } <= names

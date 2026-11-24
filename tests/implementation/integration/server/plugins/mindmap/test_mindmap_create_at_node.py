"""Item oder Memo aus einem Knoten anlegen, echte Plugins `workspace`, `backlog`, `memos`, `mindmap` (`TASK-073`)."""

from __future__ import annotations

from typing import Any

from workspace_env import Env

API = "/api/mindmap"
CRITERIA = {"completion_criteria": "1. Fertig"}


def _project(env: Env) -> str:
    return str(env.general()["uid"])


def _node(
    env: Env,
    title: str = "Thema",
    text: str | None = "Der Text",
    project: str | None = None,
) -> dict[str, Any]:
    response = env.client.post(
        f"{API}/nodes",
        json={"project": project or _project(env), "title": title, "text": text},
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _create_item(
    env: Env,
    node: dict[str, Any],
    type_: str = "Task",
    fields: dict[str, Any] | None = None,
    **body: Any,
) -> Any:
    return env.client.post(
        f"{API}/nodes/{node['uid']}/create-item",
        json={"type": type_, "fields": CRITERIA if fields is None else fields, **body},
    )


def _create_memo(
    env: Env, node: dict[str, Any], fields: dict[str, Any] | None = None, **body: Any
) -> Any:
    return env.client.post(
        f"{API}/nodes/{node['uid']}/create-memo", json={"fields": fields or {}, **body}
    )


def _state(env: Env, node: dict[str, Any]) -> str:
    tree = env.client.get(f"{API}/trees/{_project(env)}").json()
    return str(next(n["state"] for n in tree["nodes"] if n["uid"] == node["uid"]))


def test_an_item_takes_title_and_goal_from_the_node_and_hangs_on_it(
    mindmap: Env,
) -> None:
    node = _node(mindmap)
    response = _create_item(mindmap, node, "Story")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["item"]["title"] == "Thema" and body["item"]["type"] == "Story"
    item = mindmap.client.get(f"/api/backlog/items/{body['item']['uid']}").json()
    assert (item["title"], item["goal"], item["type"]) == ("Thema", "Der Text", "Story")
    assert body["node"]["uid"] == node["uid"]
    effective = mindmap.client.get(f"{API}/items/{body['item']['uid']}/node").json()
    assert effective == {
        "item_uid": body["item"]["uid"],
        "node_uid": node["uid"],
        "explicit": True,
    }


def test_the_node_turns_from_idea_to_planned_with_an_item(mindmap: Env) -> None:
    node = _node(mindmap)
    assert _state(mindmap, node) == "idea"
    body = _create_item(mindmap, node).json()
    assert body["node"]["state"] == "planned"
    assert _state(mindmap, node) == "planned"


def test_given_fields_win_over_the_node(mindmap: Env) -> None:
    node = _node(mindmap)
    body = _create_item(
        mindmap,
        node,
        fields={
            **CRITERIA,
            "title": "Eigen",
            "goal": "Anders",
            "priority": "Important",
        },
    ).json()
    item = mindmap.client.get(f"/api/backlog/items/{body['item']['uid']}").json()
    assert (item["title"], item["goal"], item["priority"]) == (
        "Eigen",
        "Anders",
        "Important",
    )


def test_a_node_without_text_and_without_goal_is_rejected_by_the_backlog(
    mindmap: Env,
) -> None:
    node = _node(mindmap, text=None)
    response = _create_item(mindmap, node)
    assert response.status_code == 422 or response.status_code == 400, response.text
    assert (
        mindmap.client.get(f"{API}/trees/{_project(mindmap)}").json()["unassigned"]
        == []
    )


def test_the_completion_criteria_are_required(mindmap: Env) -> None:
    node = _node(mindmap)
    response = _create_item(mindmap, node, fields={"title": "Nur Titel"})
    assert response.status_code in (400, 422), response.text
    assert response.json()["code"] == "invalid_input"
    assert (
        mindmap.client.get(f"{API}/trees/{_project(mindmap)}").json()["unassigned"]
        == []
    )


def test_a_memo_takes_summary_and_body_from_the_node_and_keeps_the_state(
    mindmap: Env,
) -> None:
    node = _node(mindmap)
    response = _create_memo(mindmap, node)
    assert response.status_code == 200, response.text
    body = response.json()
    memo = mindmap.client.get(f"/api/memos/memos/{body['memo']['uid']}").json()
    assert (memo["summary"], memo["body"]) == ("Thema", "Der Text")
    content = mindmap.client.get(f"{API}/nodes/{node['uid']}/content").json()
    assert [m["uid"] for m in content["memos"]] == [body["memo"]["uid"]]
    assert body["node"]["state"] == "idea" and _state(mindmap, node) == "idea"


def test_a_memo_with_own_fields(mindmap: Env) -> None:
    node = _node(mindmap)
    body = _create_memo(mindmap, node, {"summary": "Erinnern", "body": "Später"}).json()
    memo = mindmap.client.get(f"/api/memos/memos/{body['memo']['uid']}").json()
    assert (memo["summary"], memo["body"]) == ("Erinnern", "Später")


def test_a_node_in_the_trash_is_rejected(mindmap: Env) -> None:
    node = _node(mindmap)
    version = mindmap.client.get(f"{API}/nodes/{node['uid']}").json()["version"]
    deleted = mindmap.client.request(
        "DELETE",
        f"/api/workspace/elements/{node['uid']}",
        params={"version": version, "cascade": True},
    )
    assert deleted.status_code == 200, deleted.text
    for response in (_create_item(mindmap, node), _create_memo(mindmap, node)):
        assert response.status_code in (400, 409, 422), response.text
        assert response.json()["code"] == "mindmap_node_deleted"
    assert (
        mindmap.client.get(
            "/api/backlog/items", params={"project": _project(mindmap)}
        ).json()
        == []
    )


def test_a_node_of_another_project_is_rejected(mindmap: Env) -> None:
    other = mindmap.create("Anderes")
    node = _node(mindmap, project=str(other["uid"]))
    for response in (
        _create_item(mindmap, node, project=_project(mindmap)),
        _create_memo(mindmap, node, project=_project(mindmap)),
    ):
        assert response.json()["code"] == "mindmap_other_project", response.text


def test_a_label_needs_its_project_and_works_with_it(mindmap: Env) -> None:
    node = _node(mindmap)
    no_project = mindmap.client.post(
        f"{API}/nodes/{node['label']}/create-item",
        json={"type": "Task", "fields": CRITERIA},
    )
    assert no_project.json()["code"] == "invalid_input"
    ok = mindmap.client.post(
        f"{API}/nodes/{node['label']}/create-item",
        json={"type": "Task", "fields": CRITERIA, "project": _project(mindmap)},
    )
    assert ok.status_code == 200, ok.text


def test_a_failing_assignment_names_the_created_item(mindmap: Env) -> None:
    node = _node(mindmap)
    # Ein Parent ohne Knoten ändert das Anhängen nicht; scheitern lässt es ein bereits an einem Knoten hängendes Item
    # nicht (das Item ist neu). Darum wird der Knoten zwischen Prüfung und Anhängen entfernt.
    services = mindmap.app.state.plugin_host.services("mindmap")
    original = services.assignments.assign_item

    def failing(*args: Any, **kwargs: Any) -> Any:
        from viewer.plugins.mindmap.domain.model import MindmapViolation

        raise MindmapViolation("mindmap_node_deleted", "weg")

    services.assignments.assign_item = failing
    try:
        response = _create_item(mindmap, node)
    finally:
        services.assignments.assign_item = original
    body = response.json()
    assert body["code"] == "mindmap_assign_failed"
    created = body["details"]["created"]
    assert created["label"].startswith("TASK-")
    unassigned = mindmap.client.get(f"{API}/trees/{_project(mindmap)}").json()[
        "unassigned"
    ]
    assert [i["label"] for i in unassigned] == [created["label"]]


def test_both_operations_are_http_routes_and_mcp_tools(mindmap: Env) -> None:
    host = mindmap.app.state.plugin_host
    for name in ("create_item_at_node", "create_memo_at_node"):
        assert host.operation("mindmap", name).mcp
    paths = mindmap.client.get("/openapi.json").json()["paths"]
    assert (
        "/api/mindmap/nodes/{node}/create-item" in paths
        and "/api/mindmap/nodes/{node}/create-memo" in paths
    )

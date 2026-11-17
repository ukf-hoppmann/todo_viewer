"""Markierungen „verworfen“ und „später“ an einem Knoten (`TASK-065`)."""

from __future__ import annotations

import dataclasses
from typing import Any

from workspace_env import Env

API = "/api/mindmap"
BASE = {"title": "Item", "area": "Server", "goal": "Ziel", "completion_criteria": "Kriterien"}


def _project(env: Env) -> str:
    return str(env.general()["uid"])


def _node(env: Env, title: str = "Thema", parent: dict[str, Any] | None = None) -> dict[str, Any]:
    body = {"project": _project(env), "title": title, **({"parent": parent["uid"]} if parent else {})}
    response = env.client.post(f"{API}/nodes", json=body)
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _mark(env: Env, node: dict[str, Any], mark: str | None, **extra: Any) -> Any:
    body = {"version": node["version"], **({} if mark is None else {"mark": mark}), **extra}
    return env.client.put(f"{API}/nodes/{node['uid']}", json=body)


def _tree(env: Env) -> dict[str, Any]:
    return env.client.get(f"{API}/trees/{_project(env)}").json()  # type: ignore[no-any-return]


def _item(env: Env, **fields: Any) -> dict[str, Any]:
    response = env.client.post(
        "/api/backlog/items", json={"project": _project(env), "type": "Task", "fields": {**BASE, **fields}}
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def test_a_new_node_carries_no_mark(mindmap: Env) -> None:
    node = _node(mindmap)

    assert node["mark"] is None
    assert _tree(mindmap)["nodes"][0]["mark"] is None


def test_a_mark_is_set_changed_and_cleared_with_the_version_token(mindmap: Env) -> None:
    node = _node(mindmap)

    later = _mark(mindmap, node, "later")
    assert later.status_code == 200 and later.json()["mark"] == "later"
    assert later.json()["version"] == node["version"] + 1
    discarded = _mark(mindmap, later.json(), "discarded")
    assert discarded.json()["mark"] == "discarded"
    cleared = _mark(mindmap, discarded.json(), "")
    assert cleared.status_code == 200 and cleared.json()["mark"] is None
    assert _tree(mindmap)["nodes"][0]["mark"] is None


def test_a_change_without_a_mark_keeps_it(mindmap: Env) -> None:
    node = _mark(mindmap, _node(mindmap), "later").json()

    renamed = mindmap.client.put(f"{API}/nodes/{node['uid']}", json={"version": node["version"], "title": "Neu"})

    assert renamed.json()["mark"] == "later" and renamed.json()["title"] == "Neu"


def test_a_mark_outside_the_fixed_values_is_refused_and_changes_nothing(mindmap: Env) -> None:
    node = _node(mindmap)

    response = _mark(mindmap, node, "verworfen")

    assert response.status_code == 400
    assert response.json()["code"] == "mindmap_mark_invalid"
    assert response.json()["details"]["allowed"] == ["discarded", "later"]
    assert _tree(mindmap)["nodes"][0]["version"] == node["version"]


def test_a_stale_version_is_refused_like_any_write(mindmap: Env) -> None:
    node = _node(mindmap)
    _mark(mindmap, node, "later")

    response = _mark(mindmap, node, "discarded")  # die Version ist veraltet

    assert response.status_code == 409
    assert response.json()["code"] == "version_conflict"


def test_a_node_in_the_trash_cannot_be_marked(mindmap: Env) -> None:
    node = _node(mindmap)
    current = mindmap.client.get(f"{API}/nodes/{node['uid']}").json()
    mindmap.client.delete(f"/api/workspace/elements/{node['uid']}", params={"version": current["version"]})
    deleted = mindmap.client.get(f"{API}/nodes/{node['uid']}").json()

    response = _mark(mindmap, deleted, "later")

    assert response.status_code == 400
    assert response.json()["code"] == "mindmap_node_deleted"


def test_the_mark_belongs_to_the_node_alone_not_to_its_children(mindmap: Env) -> None:
    top = _node(mindmap, "Oben")
    child = _node(mindmap, "Kind", parent=top)

    _mark(mindmap, top, "discarded")

    nodes = {n["uid"]: n for n in _tree(mindmap)["nodes"]}
    assert nodes[top["uid"]]["mark"] == "discarded"
    assert nodes[child["uid"]]["mark"] is None


def test_the_mark_changes_neither_the_counts_nor_the_state(mindmap: Env) -> None:
    node = _node(mindmap)
    item = _item(mindmap)
    mindmap.client.post(f"{API}/nodes/{node['uid']}/items", json={"item": item["uid"]})
    before = _tree(mindmap)["nodes"][0]
    assert (before["total"], before["state"]) == (1, "planned")

    for mark in ("discarded", "later", ""):
        current = _tree(mindmap)["nodes"][0]
        assert _mark(mindmap, current, mark).status_code == 200
        after = _tree(mindmap)["nodes"][0]
        assert (after["total"], after["done"], after["state"]) == (1, 0, "planned")
    assert [i["uid"] for i in mindmap.client.get(f"{API}/nodes/{node['uid']}/content").json()["items"]] == [item["uid"]]


def test_the_mark_survives_the_trash(mindmap: Env) -> None:
    node = _mark(mindmap, _node(mindmap), "later").json()
    mindmap.client.delete(f"/api/workspace/elements/{node['uid']}", params={"version": node["version"]})
    trashed = mindmap.client.get(f"{API}/nodes/{node['uid']}").json()
    assert trashed["mark"] == "later"

    mindmap.client.post("/api/workspace/trash/restore", json={"uids": [node["uid"]]})

    assert _tree(mindmap)["nodes"][0]["mark"] == "later"


def test_the_mark_is_part_of_the_mcp_operation(mindmap: Env) -> None:
    host = mindmap.app.state.plugin_host
    operation = host.operation("mindmap", "update_node")

    assert operation.mcp
    assert "mark" in {f.name for f in dataclasses.fields(operation.input)}

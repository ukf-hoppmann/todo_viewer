"""Die gelöschten Knoten eines Baums für die Papierkorb-Ansicht (`TASK-067`)."""

from __future__ import annotations

from typing import Any

from workspace_env import Env

API = "/api/mindmap"


def _project(env: Env) -> str:
    return str(env.general()["uid"])


def _new_map(env: Env, name: str = "Ideen") -> str:
    response = env.client.post(
        f"{API}/maps", json={"project": _project(env), "name": name}
    )
    assert response.status_code == 200, response.text
    return str(response.json()["tree_uid"])


def _node(
    env: Env, title: str, tree: str | None = None, **fields: Any
) -> dict[str, Any]:
    response = env.client.post(
        f"{API}/nodes",
        json={"project": _project(env), "title": title, "tree": tree, **fields},
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _delete(env: Env, node: dict[str, Any]) -> None:
    fresh = env.client.get(f"{API}/nodes/{node['uid']}").json()
    response = env.client.request(
        "DELETE", f"{API}/nodes/{node['uid']}", params={"version": fresh["version"]}
    )
    assert response.status_code == 200, response.text


def _trashed(env: Env, tree: str | None = None) -> list[dict[str, Any]]:
    response = env.client.get(
        f"{API}/trash/{_project(env)}", params={"tree": tree} if tree else {}
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def test_a_deleted_branch_is_listed_by_its_top_node_with_the_size_of_the_branch(
    mindmap: Env,
) -> None:
    top = _node(mindmap, "Ast")
    child = _node(mindmap, "Kind", parent=top["uid"])
    _node(mindmap, "Enkel", parent=child["uid"])
    _node(mindmap, "Bleibt")
    assert _trashed(mindmap) == []

    _delete(mindmap, top)

    listed = _trashed(mindmap)
    assert [(n["uid"], n["title"], n["nodes"]) for n in listed] == [
        (top["uid"], "Ast", 3)
    ]
    current = mindmap.client.get(f"{API}/nodes/{top['uid']}").json()
    assert (
        listed[0]["version"] == current["version"]
        and listed[0]["label"] == top["label"]
    )


def test_a_node_whose_parent_stays_is_listed_on_its_own(mindmap: Env) -> None:
    top = _node(mindmap, "Ast")
    child = _node(mindmap, "Kind", parent=top["uid"])
    _node(mindmap, "Enkel", parent=child["uid"])

    _delete(mindmap, child)

    listed = _trashed(mindmap)
    assert [(n["title"], n["parent_uid"], n["nodes"]) for n in listed] == [
        ("Kind", top["uid"], 2)
    ]


def test_only_nodes_that_stood_in_the_asked_tree_are_listed(mindmap: Env) -> None:
    ideas = _new_map(mindmap)
    in_project = _node(mindmap, "Im Projekt")
    in_map = _node(mindmap, "In der Map", tree=ideas)
    _delete(mindmap, in_project)
    _delete(mindmap, in_map)

    assert [n["title"] for n in _trashed(mindmap)] == ["Im Projekt"]
    assert [n["title"] for n in _trashed(mindmap, ideas)] == ["In der Map"]


def test_a_node_taken_out_of_one_tree_only_is_not_in_the_trash(mindmap: Env) -> None:
    ideas = _new_map(mindmap)
    top = _node(mindmap, "Ast")
    fresh = mindmap.client.get(f"{API}/nodes/{top['uid']}").json()
    mindmap.client.post(
        f"{API}/nodes/{top['uid']}/transfer",
        json={"version": fresh["version"], "target": ideas},
    )
    fresh = mindmap.client.get(
        f"{API}/nodes/{top['uid']}", params={"tree": ideas}
    ).json()
    removed = mindmap.client.post(
        f"{API}/nodes/{top['uid']}/remove",
        json={"version": fresh["version"], "tree": ideas},
    )
    assert removed.status_code == 200, removed.text

    assert _trashed(mindmap) == [] and _trashed(mindmap, ideas) == []


def test_a_restored_node_leaves_the_list(mindmap: Env) -> None:
    top = _node(mindmap, "Ast")
    _delete(mindmap, top)
    version = _trashed(mindmap)[0]["version"]

    response = mindmap.client.post(
        f"{API}/nodes/{top['uid']}/restore-move", json={"version": version}
    )
    assert response.status_code == 200, response.text

    assert _trashed(mindmap) == []


def test_a_map_in_the_trash_has_no_list(mindmap: Env) -> None:
    ideas = _new_map(mindmap)
    _node(mindmap, "In der Map", tree=ideas)
    maps = mindmap.client.get(f"{API}/maps/{_project(mindmap)}").json()
    free = next(m for m in maps if m["kind"] == "free")
    mindmap.client.request(
        "DELETE", f"{API}/maps/{ideas}", params={"version": free["version"]}
    )

    response = mindmap.client.get(
        f"{API}/trash/{_project(mindmap)}", params={"tree": ideas}
    )
    assert response.json()["code"] == "mindmap_tree_deleted"

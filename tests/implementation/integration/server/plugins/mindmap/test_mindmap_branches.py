"""Äste zwischen Bäumen umhängen und übertragen (`TASK-063`)."""

from __future__ import annotations

from typing import Any

from workspace_env import Env

API = "/api/mindmap"
BASE = {
    "title": "Item",
    "goal": "Ziel",
    "completion_criteria": "Kriterien",
}


def _project(env: Env) -> str:
    return str(env.general()["uid"])


def _new_map(env: Env, name: str = "Ideen") -> str:
    response = env.client.post(f"{API}/maps", json={"project": _project(env), "name": name})
    assert response.status_code == 200, response.text
    return str(response.json()["tree_uid"])


def _node(env: Env, title: str, tree: str | None = None, **fields: Any) -> dict[str, Any]:
    response = env.client.post(
        f"{API}/nodes",
        json={"project": _project(env), "title": title, "tree": tree, **fields},
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _get(env: Env, node: dict[str, Any], tree: str | None = None) -> dict[str, Any]:
    response = env.client.get(f"{API}/nodes/{node['uid']}", params={"tree": tree} if tree else {})
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _titles(env: Env, tree: str | None = None) -> list[tuple[str, str | None]]:
    """(Titel, Titel des Parents) der Knoten des Baums."""
    params = {"tree": tree} if tree else {}
    nodes = env.client.get(f"{API}/trees/{_project(env)}", params=params).json()["nodes"]
    by_uid = {n["uid"]: n["title"] for n in nodes}
    return [(n["title"], by_uid.get(n["parent_uid"])) for n in nodes]


def _act(env: Env, node: dict[str, Any], action: str, **body: Any) -> Any:
    fresh = _get(env, node, body.get("tree"))
    return env.client.post(
        f"{API}/nodes/{node['uid']}/{action}",
        json={"version": fresh["version"], **body},
    )


def _delete(env: Env, node: dict[str, Any]) -> Any:
    fresh = env.client.get(f"{API}/nodes/{node['uid']}", params={}).json()
    return env.client.request("DELETE", f"{API}/nodes/{node['uid']}", params={"version": fresh["version"]})


def _branch(env: Env) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Projektbaum: Ast (Kind (Enkel)) neben Anderes."""
    top = _node(env, "Ast")
    child = _node(env, "Kind", parent=top["uid"])
    _node(env, "Enkel", parent=child["uid"])
    _node(env, "Anderes")
    return top, child, _get(env, child)


def test_transferring_a_branch_puts_the_same_nodes_in_both_trees(mindmap: Env) -> None:
    ideas = _new_map(mindmap)
    top, _, _ = _branch(mindmap)

    response = _act(mindmap, top, "transfer", target=ideas)
    assert response.status_code == 200, response.text
    assert response.json()["tree_uid"] == ideas

    assert _titles(mindmap, ideas) == [
        ("Ast", None),
        ("Kind", "Ast"),
        ("Enkel", "Kind"),
    ]
    assert ("Ast", None) in _titles(mindmap) and ("Enkel", "Kind") in _titles(mindmap)
    in_ideas = {
        n["title"]: n
        for n in mindmap.client.get(f"{API}/trees/{_project(mindmap)}", params={"tree": ideas}).json()["nodes"]
    }
    in_project = {n["title"]: n for n in mindmap.client.get(f"{API}/trees/{_project(mindmap)}").json()["nodes"]}
    assert in_ideas["Kind"]["uid"] == in_project["Kind"]["uid"]  # derselbe Datensatz, nichts kopiert
    assert (in_ideas["Ast"]["tree_count"], in_project["Anderes"]["tree_count"]) == (
        2,
        1,
    )


def test_the_content_of_a_transferred_node_is_shared(mindmap: Env) -> None:
    ideas = _new_map(mindmap)
    top, _, _ = _branch(mindmap)
    _act(mindmap, top, "transfer", target=ideas)
    fresh = _get(mindmap, top, ideas)
    mindmap.client.put(
        f"{API}/nodes/{top['uid']}",
        json={"version": fresh["version"], "title": "Neu", "text": "Text"},
    )
    assert ("Neu", None) in _titles(mindmap, ideas) and ("Neu", None) in _titles(mindmap)
    assert _get(mindmap, top, ideas)["text"] == "Text"


def test_moving_a_branch_takes_it_out_of_the_source_tree(mindmap: Env) -> None:
    ideas = _new_map(mindmap)
    top, _, _ = _branch(mindmap)

    response = _act(mindmap, top, "move-to-map", target=ideas)
    assert response.status_code == 200, response.text

    assert _titles(mindmap) == [("Anderes", None)]
    assert _titles(mindmap, ideas) == [
        ("Ast", None),
        ("Kind", "Ast"),
        ("Enkel", "Kind"),
    ]


def test_a_branch_can_be_moved_back_below_the_root_of_its_own_tree(
    mindmap: Env,
) -> None:
    _top, child, _ = _branch(mindmap)
    project_tree = mindmap.client.get(f"{API}/trees/{_project(mindmap)}").json()["tree_uid"]
    response = _act(mindmap, child, "move-to-map", target=project_tree)
    assert response.status_code == 200, response.text
    assert ("Kind", None) in _titles(mindmap) and ("Enkel", "Kind") in _titles(mindmap)


def test_a_target_that_already_holds_part_of_the_branch_is_rejected_with_the_nodes(
    mindmap: Env,
) -> None:
    ideas = _new_map(mindmap)
    top, child, _ = _branch(mindmap)
    _act(mindmap, child, "transfer", target=ideas)  # Kind (mit Enkel) steht schon in "Ideen"

    for action in ("transfer", "move-to-map"):
        response = _act(mindmap, top, action, target=ideas)
        assert response.status_code >= 400
        body = response.json()
        assert body["code"] == "mindmap_target_conflict"
        assert (
            body["details"]["nodes"]
            == [child["uid"], _get(mindmap, child, ideas)["uid"]][:1] + body["details"]["nodes"][1:]
        )
        assert len(body["details"]["nodes"]) == 2  # Kind und Enkel
    assert ("Ast", None) in _titles(mindmap)  # nichts geändert


def test_transfer_into_the_same_tree_and_into_another_project_are_rejected(
    mindmap: Env,
) -> None:
    top, _, _ = _branch(mindmap)
    project_tree = mindmap.client.get(f"{API}/trees/{_project(mindmap)}").json()["tree_uid"]
    assert _act(mindmap, top, "transfer", target=project_tree).json()["code"] == "mindmap_transfer_same_tree"
    other = mindmap.create("Anderes")
    foreign = mindmap.client.post(f"{API}/maps", json={"project": str(other["uid"]), "name": "Fremd"}).json()[
        "tree_uid"
    ]
    for action in ("transfer", "move-to-map"):
        assert _act(mindmap, top, action, target=foreign).json()["code"] == "mindmap_other_project"


def test_the_root_of_a_map_a_node_in_the_trash_and_a_map_in_the_trash_are_rejected(
    mindmap: Env,
) -> None:
    ideas = _new_map(mindmap)
    top, child, _ = _branch(mindmap)
    root = mindmap.client.post(f"{API}/nodes/{ideas}/move-to-map", json={"version": 1, "target": ideas})
    assert root.json()["code"] == "mindmap_root_fixed"

    _delete(mindmap, child)
    trashed = _act(mindmap, child, "transfer", target=ideas)
    assert trashed.json()["code"] == "mindmap_node_deleted"

    mindmap.client.request("DELETE", f"{API}/maps/{ideas}", params={"version": 1})
    gone = _act(mindmap, top, "transfer", target=ideas)
    assert gone.json()["code"] == "mindmap_tree_deleted"


def test_a_new_child_appears_in_every_tree_where_its_parent_stands(
    mindmap: Env,
) -> None:
    ideas = _new_map(mindmap)
    top, _, _ = _branch(mindmap)
    _act(mindmap, top, "transfer", target=ideas)

    _node(mindmap, "Neu", parent=top["uid"])
    assert ("Neu", "Ast") in _titles(mindmap) and ("Neu", "Ast") in _titles(mindmap, ideas)


def test_restructuring_below_a_transferred_node_changes_only_the_edited_tree(
    mindmap: Env,
) -> None:
    ideas = _new_map(mindmap)
    top, child, _ = _branch(mindmap)
    _act(mindmap, top, "transfer", target=ideas)

    moved = _act(mindmap, child, "move", tree=ideas)  # Kind unter die Wurzel von "Ideen"
    assert moved.status_code == 200, moved.text
    assert ("Kind", None) in _titles(mindmap, ideas)
    assert ("Kind", "Ast") in _titles(mindmap)


def test_counts_are_computed_per_tree_and_an_item_counts_once(mindmap: Env) -> None:
    ideas = _new_map(mindmap)
    top, child, _ = _branch(mindmap)
    item = mindmap.client.post(
        "/api/backlog/items",
        json={"project": _project(mindmap), "type": "Task", "fields": BASE},
    ).json()
    mindmap.client.post(f"{API}/nodes/{child['uid']}/items", json={"item": item["uid"]})
    _act(mindmap, top, "transfer", target=ideas)
    _act(mindmap, child, "move", tree=ideas)  # in "Ideen" hängt Kind nicht mehr unter Ast

    def total(tree: str | None, title: str) -> int:
        params = {"tree": tree} if tree else {}
        nodes = mindmap.client.get(f"{API}/trees/{_project(mindmap)}", params=params).json()["nodes"]
        return int(next(n["total"] for n in nodes if n["title"] == title))

    assert (total(None, "Ast"), total(ideas, "Ast"), total(ideas, "Kind")) == (1, 0, 1)


def test_the_trees_of_a_node_are_listed_project_tree_first(mindmap: Env) -> None:
    ideas = _new_map(mindmap, "Ideen")
    top, _, _ = _branch(mindmap)
    _act(mindmap, top, "transfer", target=ideas)
    found = mindmap.client.get(f"{API}/nodes/{top['uid']}/trees").json()
    assert [(t["kind"], t["name"]) for t in found] == [
        ("project", "Allgemein"),
        ("free", "Ideen"),
    ]
    # ohne Angabe liest man einen Knoten in mehreren Bäumen im Projektbaum
    assert mindmap.client.get(f"{API}/nodes/{top['uid']}").json()["tree_uid"] == found[0]["tree_uid"]


def test_removing_here_keeps_the_branch_in_the_other_tree(mindmap: Env) -> None:
    ideas = _new_map(mindmap)
    top, _, _ = _branch(mindmap)
    _act(mindmap, top, "transfer", target=ideas)

    response = _act(mindmap, top, "remove", tree=ideas)
    assert response.status_code == 200, response.text
    assert response.json() == {
        "node_uid": top["uid"],
        "nodes_deleted": 0,
        "kept_elsewhere": 3,
    }
    assert _titles(mindmap, ideas) == []
    assert ("Enkel", "Kind") in _titles(mindmap)


def test_removing_the_last_placement_sends_the_branch_to_the_trash(
    mindmap: Env,
) -> None:
    top, _, _ = _branch(mindmap)
    response = _act(mindmap, top, "remove")
    assert response.json() == {
        "node_uid": top["uid"],
        "nodes_deleted": 3,
        "kept_elsewhere": 0,
    }
    assert _titles(mindmap) == [("Anderes", None)]
    trash = [e["label"] for e in mindmap.client.get("/api/workspace/trash").json()]
    assert len(trash) >= 3


def test_a_shared_child_stays_when_its_parent_is_removed_from_its_last_tree(
    mindmap: Env,
) -> None:
    ideas = _new_map(mindmap)
    top, child, _ = _branch(mindmap)
    _act(mindmap, child, "transfer", target=ideas)  # Kind (mit Enkel) steht auch in "Ideen"

    response = _delete(mindmap, top)
    assert response.json() == {
        "node_uid": top["uid"],
        "nodes_deleted": 1,
        "kept_elsewhere": 2,
    }
    assert _titles(mindmap) == [("Anderes", None)]
    assert _titles(mindmap, ideas) == [("Kind", None), ("Enkel", "Kind")]


def test_deleting_a_shared_node_takes_it_out_of_every_tree(mindmap: Env) -> None:
    ideas = _new_map(mindmap)
    top, _, _ = _branch(mindmap)
    _act(mindmap, top, "transfer", target=ideas)

    response = _delete(mindmap, top)
    assert response.json() == {
        "node_uid": top["uid"],
        "nodes_deleted": 3,
        "kept_elsewhere": 0,
    }
    assert _titles(mindmap) == [("Anderes", None)]
    assert _titles(mindmap, ideas) == []


def test_removing_a_shared_branch_here_leaves_it_untouched_in_the_other_tree(
    mindmap: Env,
) -> None:
    ideas = _new_map(mindmap)
    _top, child, _ = _branch(mindmap)
    _act(mindmap, child, "transfer", target=ideas)  # Kind (mit Enkel) steht im Projektbaum unter Ast und in "Ideen"
    project_tree = mindmap.client.get(f"{API}/trees/{_project(mindmap)}").json()["tree_uid"]

    response = _act(mindmap, child, "remove", tree=project_tree)
    assert response.json() == {
        "node_uid": child["uid"],
        "nodes_deleted": 0,
        "kept_elsewhere": 2,
    }
    assert [t for t in _titles(mindmap) if t[0] in ("Kind", "Enkel")] == []
    assert _titles(mindmap, ideas) == [("Kind", None), ("Enkel", "Kind")]


def test_a_deleted_map_keeps_shared_nodes_in_the_other_tree(mindmap: Env) -> None:
    ideas = _new_map(mindmap)
    top, _, _ = _branch(mindmap)
    _act(mindmap, top, "transfer", target=ideas)
    own = _node(mindmap, "Nur hier", ideas)
    maps = mindmap.client.get(f"{API}/maps/{_project(mindmap)}").json()
    free = next(m for m in maps if m["kind"] == "free")
    assert free["shared_count"] == 3

    gone = mindmap.client.request("DELETE", f"{API}/maps/{ideas}", params={"version": free["version"]})
    assert gone.json() == {"tree_uid": ideas, "nodes_deleted": 1, "kept_elsewhere": 3}
    assert ("Enkel", "Kind") in _titles(mindmap)
    assert own["title"] == "Nur hier"


def test_a_node_in_the_trash_can_be_restored_and_moved_in_one_step(
    mindmap: Env,
) -> None:
    top, child, _ = _branch(mindmap)
    other = next(
        n for n in mindmap.client.get(f"{API}/trees/{_project(mindmap)}").json()["nodes"] if n["title"] == "Anderes"
    )
    _delete(mindmap, top)
    trashed = mindmap.client.get(f"{API}/nodes/{child['uid']}").json()

    blocked = mindmap.client.post("/api/workspace/trash/restore", json={"uids": [child["uid"]]})
    assert blocked.status_code >= 400  # der Parent liegt im Papierkorb

    response = mindmap.client.post(
        f"{API}/nodes/{child['uid']}/restore-move",
        json={"version": trashed["version"], "parent": other["uid"]},
    )
    assert response.status_code == 200, response.text
    assert ("Kind", "Anderes") in _titles(mindmap) and ("Enkel", "Kind") in _titles(mindmap)
    assert ("Ast", None) not in _titles(mindmap)


def test_restore_and_move_needs_a_node_in_the_trash_and_the_current_version(
    mindmap: Env,
) -> None:
    top, _, _ = _branch(mindmap)
    live = _get(mindmap, top)
    assert (
        mindmap.client.post(f"{API}/nodes/{top['uid']}/restore-move", json={"version": live["version"]}).json()["code"]
        == "mindmap_node_not_deleted"
    )
    _delete(mindmap, top)
    stale = mindmap.client.post(f"{API}/nodes/{top['uid']}/restore-move", json={"version": 1})
    assert stale.json()["code"] == "version_conflict"


def test_events_announce_the_moved_nodes(mindmap: Env) -> None:
    seen: list[Any] = []
    ideas = _new_map(mindmap)
    top, _, _ = _branch(mindmap)
    mindmap.app.state.events.subscribe("mindmap.node.changed", seen.append)
    _act(mindmap, top, "transfer", target=ideas)
    assert {e.payload["change"] for e in seen} == {"transferred"}
    assert len(seen) == 3


def test_the_project_tree_is_a_target_even_before_it_has_a_node(mindmap: Env) -> None:
    ideas = _new_map(mindmap)
    own = _node(mindmap, "Frei", ideas)
    response = _act(mindmap, own, "move-to-map", target=_project(mindmap), tree=ideas)
    assert response.status_code == 200, response.text
    assert _titles(mindmap) == [("Frei", None)]
    assert _titles(mindmap, ideas) == []

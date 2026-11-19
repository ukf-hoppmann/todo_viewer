from __future__ import annotations

from datetime import timedelta
from typing import Any

from viewer.core.domain.events import Event
from workspace_env import Env

API = "/api/mindmap"


def _project(env: Env) -> str:
    return str(env.general()["uid"])


def _create(env: Env, title: str = "Thema", **fields: Any) -> dict[str, Any]:
    response = env.client.post(f"{API}/nodes", json={"project": _project(env), "title": title, **fields})
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _tree(env: Env) -> dict[str, Any]:
    response = env.client.get(f"{API}/trees/{_project(env)}")
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _shape(env: Env) -> list[tuple[str, str | None, int]]:
    """(Titel, Titel des Parents, Stelle) in der Reihenfolge der Antwort."""
    nodes = _tree(env)["nodes"]
    titles = {n["uid"]: n["title"] for n in nodes}
    return [(n["title"], titles.get(n["parent_uid"]), n["position"]) for n in nodes]


def _move(env: Env, node: dict[str, Any], **body: Any) -> Any:
    current = env.client.get(f"{API}/nodes/{node['uid']}").json()
    return env.client.post(f"{API}/nodes/{node['uid']}/move", json={"version": current["version"], **body})


def _events(env: Env) -> list[Event]:
    seen: list[Event] = []
    env.app.state.events.subscribe("mindmap.*", seen.append)
    return seen


def _delete(env: Env, node: dict[str, Any], cascade: bool = True) -> Any:
    version = env.client.get(f"{API}/nodes/{node['uid']}").json()["version"]
    return env.client.request(
        "DELETE", f"/api/workspace/elements/{node['uid']}", params={"version": version, "cascade": cascade}
    )


def test_a_project_without_nodes_has_an_empty_tree(mindmap: Env) -> None:
    assert _tree(mindmap) == {"project_uid": _project(mindmap), "tree_uid": None, "nodes": [], "unassigned": [], "links": []}


def test_the_first_node_creates_the_project_tree_and_gets_a_label(mindmap: Env) -> None:
    node = _create(mindmap, "  Ideen   sammeln ", text="Erste Gedanken")

    assert (node["label"], node["title"], node["text"]) == ("NODE-001", "Ideen sammeln", "Erste Gedanken")
    assert (node["parent_uid"], node["position"]) == (None, 0)
    tree = _tree(mindmap)
    assert tree["tree_uid"] == node["tree_uid"] and [n["uid"] for n in tree["nodes"]] == [node["uid"]]
    assert _create(mindmap, "Zweites")["tree_uid"] == tree["tree_uid"]  # derselbe Baum, nicht ein neuer


def test_an_empty_node_is_allowed_but_a_title_is_required(mindmap: Env) -> None:
    assert _create(mindmap, "Leer")["text"] is None
    for title in ("", "   "):
        response = mindmap.client.post(f"{API}/nodes", json={"project": _project(mindmap), "title": title})
        assert response.status_code == 422


def test_nodes_are_ordered_below_their_parents_and_by_position(mindmap: Env) -> None:
    a = _create(mindmap, "A")
    b = _create(mindmap, "B")
    _create(mindmap, "A1", parent=a["uid"])
    _create(mindmap, "A0", parent=a["uid"], position=0)
    _create(mindmap, "B1", parent=b["uid"])

    assert _shape(mindmap) == [
        ("A", None, 0), ("B", None, 1), ("A0", "A", 0), ("A1", "A", 1), ("B1", "B", 0),
    ]  # fmt: skip


def test_a_parent_may_be_given_by_label_and_must_exist(mindmap: Env) -> None:
    a = _create(mindmap, "A")
    assert _create(mindmap, "A1", parent=a["label"])["parent_uid"] == a["uid"]
    response = mindmap.client.post(
        f"{API}/nodes", json={"project": _project(mindmap), "title": "X", "parent": "unbekannt"}
    )
    assert response.status_code == 404


def test_a_node_is_changed_with_a_version_and_the_old_version_is_refused(mindmap: Env) -> None:
    node = _create(mindmap, "Alt", text="Text")

    changed = mindmap.client.put(f"{API}/nodes/{node['uid']}", json={"version": node["version"], "title": "Neu"})

    assert changed.status_code == 200
    assert (changed.json()["title"], changed.json()["text"]) == ("Neu", "Text")
    assert changed.json()["version"] > node["version"]
    stale = mindmap.client.put(f"{API}/nodes/{node['uid']}", json={"version": node["version"], "title": "Noch neuer"})
    assert stale.status_code == 409 and stale.json()["code"] == "version_conflict"
    cleared = mindmap.client.put(f"{API}/nodes/{node['uid']}", json={"version": changed.json()["version"], "text": ""})
    assert cleared.json()["text"] is None and cleared.json()["title"] == "Neu"


def test_a_change_needs_something_to_change_and_a_non_empty_title(mindmap: Env) -> None:
    node = _create(mindmap)
    for body in ({}, {"title": " "}):
        response = mindmap.client.put(f"{API}/nodes/{node['uid']}", json={"version": node["version"], **body})
        assert response.status_code == 422, body


def test_the_title_in_the_register_follows_the_node(mindmap: Env) -> None:
    node = _create(mindmap, "Alt")
    mindmap.client.put(f"{API}/nodes/{node['uid']}", json={"version": node["version"], "title": "Gefunden"})

    found = mindmap.client.get("/api/workspace/elements", params={"query": "Gefunden"}).json()

    assert [e["uid"] for e in found] == [node["uid"]]


def test_a_node_moves_with_its_branch_and_reorders_inside_its_parent(mindmap: Env) -> None:
    a = _create(mindmap, "A")
    b = _create(mindmap, "B")
    a1 = _create(mindmap, "A1", parent=a["uid"])
    _create(mindmap, "A1x", parent=a1["uid"])
    c = _create(mindmap, "C")

    assert _move(mindmap, a1, parent=b["uid"]).status_code == 200
    assert _shape(mindmap) == [("A", None, 0), ("B", None, 1), ("C", None, 2), ("A1", "B", 0), ("A1x", "A1", 0)]

    assert _move(mindmap, c, position=0).status_code == 200  # ohne Parent: unter die Wurzel, vorn
    assert _shape(mindmap)[:3] == [("C", None, 0), ("A", None, 1), ("B", None, 2)]


def test_a_node_cannot_move_below_itself_or_a_descendant(mindmap: Env) -> None:
    a = _create(mindmap, "A")
    a1 = _create(mindmap, "A1", parent=a["uid"])
    a11 = _create(mindmap, "A11", parent=a1["uid"])
    before = _shape(mindmap)

    for parent in (a["uid"], a1["uid"], a11["uid"]):
        response = _move(mindmap, a, parent=parent)
        assert response.status_code == 400 and response.json()["code"] == "mindmap_loop", parent

    assert _shape(mindmap) == before


def test_a_move_with_an_old_version_is_refused(mindmap: Env) -> None:
    a = _create(mindmap, "A")
    b = _create(mindmap, "B")
    mindmap.client.put(f"{API}/nodes/{a['uid']}", json={"version": a["version"], "title": "A2"})

    response = mindmap.client.post(f"{API}/nodes/{a['uid']}/move", json={"version": a["version"], "parent": b["uid"]})

    assert response.status_code == 409 and response.json()["code"] == "version_conflict"


def test_a_node_of_another_project_is_not_a_parent(mindmap: Env) -> None:
    other = mindmap.create("Zweites")
    foreign = mindmap.client.post(f"{API}/nodes", json={"project": other["uid"], "title": "Fremd"}).json()

    response = mindmap.client.post(
        f"{API}/nodes", json={"project": _project(mindmap), "title": "X", "parent": foreign["uid"]}
    )

    assert response.status_code == 400 and response.json()["code"] == "mindmap_parent_missing"
    assert foreign["project_uid"] == other["uid"] and _tree(mindmap)["nodes"] == []


def test_every_project_has_its_own_tree(mindmap: Env) -> None:
    other = mindmap.create("Zweites")
    one = _create(mindmap, "Eins")
    two = mindmap.client.post(f"{API}/nodes", json={"project": other["uid"], "title": "Zwei"}).json()

    assert one["tree_uid"] != two["tree_uid"] and two["label"] == "NODE-001"
    assert [n["title"] for n in _tree(mindmap)["nodes"]] == ["Eins"]


def test_an_unknown_project_or_node_is_not_found(mindmap: Env) -> None:
    assert mindmap.client.get(f"{API}/trees/unbekannt").status_code == 404
    assert mindmap.client.get(f"{API}/nodes/unbekannt").status_code == 404
    assert mindmap.client.post(f"{API}/nodes", json={"project": "unbekannt", "title": "X"}).status_code == 404


def test_a_label_needs_the_project(mindmap: Env) -> None:
    node = _create(mindmap)
    assert mindmap.client.get(f"{API}/nodes/{node['label']}").status_code == 422
    found = mindmap.client.get(f"{API}/nodes/{node['label']}", params={"project": _project(mindmap)})
    assert found.status_code == 200 and found.json()["uid"] == node["uid"]


# --- Papierkorb --------------------------------------------------------------------------------------------------


def test_a_branch_goes_to_the_trash_with_its_children_and_comes_back_with_them(mindmap: Env) -> None:
    a = _create(mindmap, "A")
    a1 = _create(mindmap, "A1", parent=a["uid"])
    _create(mindmap, "A11", parent=a1["uid"])
    _create(mindmap, "B")

    refused = _delete(mindmap, a, cascade=False)
    assert refused.json()["has_children"] is True and len(_tree(mindmap)["nodes"]) == 4

    deleted = _delete(mindmap, a)
    assert deleted.status_code == 200 and deleted.json()["deleted"] == 3
    assert _shape(mindmap) == [("B", None, 0)]

    restored = mindmap.client.post("/api/workspace/trash/restore", json={"uids": [a["uid"]]})
    assert restored.status_code == 200
    assert _shape(mindmap) == [("A", None, 0), ("B", None, 1), ("A1", "A", 0), ("A11", "A1", 0)]


def test_a_child_does_not_come_back_before_its_parent(mindmap: Env) -> None:
    a = _create(mindmap, "A")
    a1 = _create(mindmap, "A1", parent=a["uid"])
    assert _delete(mindmap, a1, cascade=False).status_code == 200  # erst das Kind
    mindmap.clock.advance(timedelta(minutes=1))  # sonst gelten beide als zusammen gelöscht
    assert _delete(mindmap, a, cascade=False).status_code == 200  # dann der Parent (das Kind ist schon draußen)

    refused = mindmap.client.post("/api/workspace/trash/restore", json={"uids": [a1["uid"]]})

    assert refused.status_code == 400 and refused.json()["code"] == "mindmap_parent_in_trash"
    assert mindmap.client.post("/api/workspace/trash/restore", json={"uids": [a["uid"]]}).status_code == 200
    assert mindmap.client.post("/api/workspace/trash/restore", json={"uids": [a1["uid"]]}).status_code == 200
    assert _shape(mindmap) == [("A", None, 0), ("A1", "A", 0)]


def test_a_node_in_the_trash_cannot_be_changed_moved_or_used_as_a_parent(mindmap: Env) -> None:
    a = _create(mindmap, "A")
    b = _create(mindmap, "B")
    assert _delete(mindmap, a).status_code == 200
    version = mindmap.client.get(f"{API}/nodes/{a['uid']}").json()["version"]

    changed = mindmap.client.put(f"{API}/nodes/{a['uid']}", json={"version": version, "title": "X"})
    moved = _move(mindmap, a, parent=b["uid"])
    below = mindmap.client.post(f"{API}/nodes", json={"project": _project(mindmap), "title": "X", "parent": a["uid"]})

    for response in (changed, moved):
        assert response.status_code == 400 and response.json()["code"] == "mindmap_node_deleted"
    assert below.status_code == 400 and below.json()["code"] == "mindmap_parent_missing"


def test_a_new_node_takes_the_place_of_a_deleted_one_without_confusing_the_order(mindmap: Env) -> None:
    a = _create(mindmap, "A")
    _create(mindmap, "B")
    assert _delete(mindmap, a).status_code == 200
    _create(mindmap, "C", position=0)

    assert [t for t, _, _ in _shape(mindmap)] == ["C", "B"]
    mindmap.client.post("/api/workspace/trash/restore", json={"uids": [a["uid"]]})
    assert {t for t, _, _ in _shape(mindmap)} == {"A", "B", "C"}


def test_purging_a_branch_removes_nodes_and_placements(mindmap: Env) -> None:
    a = _create(mindmap, "A")
    a1 = _create(mindmap, "A1", parent=a["uid"])
    _delete(mindmap, a)

    purged = mindmap.client.post("/api/workspace/trash/purge", json={"uids": [a["uid"]]})

    assert purged.status_code == 200
    assert mindmap.client.get(f"{API}/nodes/{a1['uid']}").status_code == 404
    assert _tree(mindmap)["nodes"] == []
    with mindmap.app.state.database.transaction() as tx:
        rows = tx.connection.exec_driver_sql("SELECT COUNT(*) FROM mindmap_placements").scalar_one()
    assert rows == 0


# --- Ereignisse --------------------------------------------------------------------------------------------------


def test_changes_are_announced_as_node_events(mindmap: Env) -> None:
    seen = _events(mindmap)
    a = _create(mindmap, "A")
    b = _create(mindmap, "B")
    mindmap.client.put(f"{API}/nodes/{a['uid']}", json={"version": a["version"], "title": "A2"})
    _move(mindmap, b, parent=a["uid"])
    _delete(mindmap, a)
    mindmap.client.post("/api/workspace/trash/restore", json={"uids": [a["uid"]]})

    assert all(e.topic == "mindmap.node.changed" and e.public for e in seen)
    assert [(e.payload["change"], e.payload["uid"]) for e in seen] == [
        ("created", a["uid"]),
        ("created", b["uid"]),
        ("updated", a["uid"]),
        ("moved", b["uid"]),
        ("deleted", a["uid"]),
        ("deleted", b["uid"]),
        ("restored", a["uid"]),
        ("restored", b["uid"]),
    ]
    assert seen[0].payload["project_uid"] == _project(mindmap) and seen[0].payload["tree_uid"] == a["tree_uid"]


# --- MCP ---------------------------------------------------------------------------------------------------------


def test_the_operations_are_published_as_http_routes_and_mcp_tools(mindmap: Env) -> None:
    host = mindmap.app.state.plugin_host
    names = {op.name for op in host.plugins[-1].definition.operations}
    assert names == {
        "get_tree",
        "get_node",
        "create_node",
        "update_node",
        "move_node",
        "list_node_documents",
        "get_node_document",
        "put_node_document",
        "append_node_entry",
        "assign_item",
        "unassign_item",
        "link_memo",
        "unlink_memo",
        "get_node_content",
        "get_item_node",
        "list_memo_nodes",
        "list_maps",
        "create_map",
        "rename_map",
        "delete_map",
        "move_node_to_map",
        "transfer_node_to_map",
        "remove_node_from_map",
        "delete_node",
        "restore_and_move_node",
        "list_node_trees",
    }
    assert all(host.operation("mindmap", name).mcp for name in names)
    paths = mindmap.client.get("/openapi.json").json()["paths"]
    assert {
        "/api/mindmap/trees/{project}",
        "/api/mindmap/nodes",
        "/api/mindmap/nodes/{ref}/move",
        "/api/mindmap/maps",
        "/api/mindmap/maps/{tree}",
    } <= set(paths)

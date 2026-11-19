"""Freie Maps je Projekt (`TASK-062`): anlegen, auswählen, umbenennen, in den Papierkorb legen und zurückholen."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from workspace_env import Env

API = "/api/mindmap"
BASE = {"title": "Item", "area": "Server", "goal": "Ziel", "completion_criteria": "Kriterien"}


def _project(env: Env) -> str:
    return str(env.general()["uid"])


def _maps(env: Env, project: str | None = None) -> list[dict[str, Any]]:
    response = env.client.get(f"{API}/maps/{project or _project(env)}")
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _new_map(env: Env, name: str = "Ideen", project: str | None = None) -> dict[str, Any]:
    response = env.client.post(f"{API}/maps", json={"project": project or _project(env), "name": name})
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _story(env: Env) -> dict[str, Any]:
    response = env.client.post("/api/backlog/items", json={"project": _project(env), "type": "Story", "fields": BASE})
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _node(env: Env, title: str, tree: str | None = None, **fields: Any) -> dict[str, Any]:
    body = {"project": _project(env), "title": title, "tree": tree, **fields}
    response = env.client.post(f"{API}/nodes", json=body)
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _tree(env: Env, tree: str | None = None) -> dict[str, Any]:
    params = {"tree": tree} if tree else {}
    response = env.client.get(f"{API}/trees/{_project(env)}", params=params)
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _delete(env: Env, free: dict[str, Any]) -> Any:
    return env.client.request("DELETE", f"{API}/maps/{free['tree_uid']}", params={"version": free["version"]})


def _trash(env: Env) -> list[dict[str, Any]]:
    return env.client.get("/api/workspace/trash").json()  # type: ignore[no-any-return]


def _restore(env: Env, uid: str) -> Any:
    return env.client.post("/api/workspace/trash/restore", json={"uids": [uid]})


def test_a_project_lists_its_project_tree_first_even_before_any_node(mindmap: Env) -> None:
    [only] = _maps(mindmap)
    assert (only["kind"], only["name"], only["node_count"], only["tree_uid"]) == ("project", "Allgemein", 0, None)


def test_free_maps_follow_the_project_tree_in_creation_order(mindmap: Env) -> None:
    first = _new_map(mindmap, "  Ideen  ")
    _new_map(mindmap, "Roadmap")
    assert (first["kind"], first["name"], first["node_count"]) == ("free", "Ideen", 0)
    assert [(m["kind"], m["name"]) for m in _maps(mindmap)] == [
        ("project", "Allgemein"),
        ("free", "Ideen"),
        ("free", "Roadmap"),
    ]


def test_the_project_tree_shows_its_id_and_count_after_the_first_node(mindmap: Env) -> None:
    node = _node(mindmap, "A")
    _node(mindmap, "B", parent=node["uid"])
    project_tree = _maps(mindmap)[0]
    assert (project_tree["tree_uid"], project_tree["node_count"]) == (node["tree_uid"], 2)


def test_names_must_be_present_and_unique_per_project(mindmap: Env) -> None:
    _new_map(mindmap, "Ideen")
    for name in ("", "   "):
        response = mindmap.client.post(f"{API}/maps", json={"project": _project(mindmap), "name": name})
        assert response.status_code in (400, 422)
    duplicate = mindmap.client.post(f"{API}/maps", json={"project": _project(mindmap), "name": "ideen"})
    assert duplicate.status_code == 400
    assert duplicate.json()["code"] == "mindmap_map_name_taken"
    other = mindmap.create("Anderes")
    assert _new_map(mindmap, "Ideen", str(other["uid"]))["name"] == "Ideen"  # je Projekt


def test_nodes_of_a_free_map_stay_in_that_map(mindmap: Env) -> None:
    free = _new_map(mindmap)
    _node(mindmap, "Im Projekt")
    root = _node(mindmap, "Wurzel", free["tree_uid"])
    child = _node(mindmap, "Kind", free["tree_uid"], parent=root["uid"])

    assert child["tree_uid"] == free["tree_uid"]
    shown = _tree(mindmap, free["tree_uid"])
    assert shown["tree_uid"] == free["tree_uid"]
    assert [n["title"] for n in shown["nodes"]] == ["Wurzel", "Kind"]
    assert [n["title"] for n in _tree(mindmap)["nodes"]] == ["Im Projekt"]  # ohne tree: der Projektbaum
    assert [m["node_count"] for m in _maps(mindmap)] == [1, 2]


def test_a_free_map_has_no_unassigned_page(mindmap: Env) -> None:
    free = _new_map(mindmap)
    _story(mindmap)
    assert _tree(mindmap)["unassigned"] != []
    assert _tree(mindmap, free["tree_uid"])["unassigned"] == []


def test_a_node_cannot_be_put_below_a_parent_of_another_map(mindmap: Env) -> None:
    free = _new_map(mindmap)
    in_project = _node(mindmap, "Im Projekt")
    response = mindmap.client.post(
        f"{API}/nodes",
        json={"project": _project(mindmap), "title": "X", "tree": free["tree_uid"], "parent": in_project["uid"]},
    )
    assert response.status_code >= 400
    assert response.json()["code"] == "mindmap_parent_missing"


def test_a_map_of_another_project_is_not_accepted(mindmap: Env) -> None:
    other = mindmap.create("Anderes")
    foreign = _new_map(mindmap, "Fremd", str(other["uid"]))
    response = mindmap.client.post(
        f"{API}/nodes", json={"project": _project(mindmap), "title": "X", "tree": foreign["tree_uid"]}
    )
    assert response.status_code >= 400
    assert response.json()["code"] == "mindmap_other_project"


def test_rename_checks_the_version_and_the_name(mindmap: Env) -> None:
    free = _new_map(mindmap, "Ideen")
    other = _new_map(mindmap, "Roadmap")
    renamed = mindmap.client.put(f"{API}/maps/{free['tree_uid']}", json={"version": free["version"], "name": "Plan"})
    assert renamed.status_code == 200, renamed.text
    assert (renamed.json()["name"], renamed.json()["version"]) == ("Plan", free["version"] + 1)

    stale = mindmap.client.put(f"{API}/maps/{free['tree_uid']}", json={"version": free["version"], "name": "Neu"})
    assert stale.status_code == 409 and stale.json()["code"] == "version_conflict"
    taken = mindmap.client.put(f"{API}/maps/{other['tree_uid']}", json={"version": other["version"], "name": "plan"})
    assert taken.json()["code"] == "mindmap_map_name_taken"


def test_the_project_tree_can_neither_be_renamed_nor_deleted(mindmap: Env) -> None:
    node = _node(mindmap, "A")
    project_tree = _maps(mindmap)[0]
    assert project_tree["tree_uid"] == node["tree_uid"]
    renamed = mindmap.client.put(
        f"{API}/maps/{node['tree_uid']}", json={"version": project_tree["version"], "name": "X"}
    )
    assert renamed.json()["code"] == "mindmap_project_tree_fixed"
    deleted = _delete(mindmap, project_tree)
    assert deleted.json()["code"] == "mindmap_project_tree_fixed"
    assert [n["title"] for n in _tree(mindmap)["nodes"]] == ["A"]


def test_deleting_a_map_moves_it_and_its_nodes_to_the_trash(mindmap: Env) -> None:
    free = _new_map(mindmap)
    keep = _node(mindmap, "Bleibt")
    root = _node(mindmap, "Wurzel", free["tree_uid"])
    _node(mindmap, "Kind", free["tree_uid"], parent=root["uid"])

    response = _delete(mindmap, free)
    assert response.status_code == 200, response.text
    assert response.json() == {"tree_uid": free["tree_uid"], "nodes_deleted": 2, "kept_elsewhere": 0}

    assert [m["name"] for m in _maps(mindmap)] == ["Allgemein"]
    assert [n["title"] for n in _tree(mindmap)["nodes"]] == ["Bleibt"]
    assert mindmap.client.get(f"{API}/nodes/{keep['uid']}").status_code == 200
    gone = mindmap.client.post(
        f"{API}/nodes", json={"project": _project(mindmap), "title": "X", "tree": free["tree_uid"]}
    )
    assert gone.json()["code"] == "mindmap_tree_deleted"
    entry = next(e for e in _trash(mindmap) if e["uid"] == free["tree_uid"])
    assert (entry["kind"], entry["title"]) == ("mindmap_map", "Ideen")


def test_a_deleted_map_comes_back_with_its_nodes(mindmap: Env) -> None:
    free = _new_map(mindmap)
    root = _node(mindmap, "Wurzel", free["tree_uid"])
    _node(mindmap, "Kind", free["tree_uid"], parent=root["uid"])
    _delete(mindmap, free)

    restored = _restore(mindmap, free["tree_uid"])
    assert restored.status_code == 200, restored.text
    assert [m["name"] for m in _maps(mindmap)] == ["Allgemein", "Ideen"]
    assert [(n["title"], n["parent_uid"] is None) for n in _tree(mindmap, free["tree_uid"])["nodes"]] == [
        ("Wurzel", True),
        ("Kind", False),
    ]
    assert not [e for e in _trash(mindmap) if e["uid"] == free["tree_uid"]]


def test_a_node_trashed_before_stays_in_the_trash_when_the_map_returns(mindmap: Env) -> None:
    free = _new_map(mindmap)
    early = _node(mindmap, "Früher weg", free["tree_uid"])
    _node(mindmap, "Bleibt", free["tree_uid"])
    version = mindmap.client.get(f"{API}/nodes/{early['uid']}").json()["version"]
    mindmap.client.request(
        "DELETE", f"/api/workspace/elements/{early['uid']}", params={"version": version, "cascade": True}
    )
    mindmap.clock.advance(timedelta(minutes=1))  # sonst gelten beide als zusammen gelöscht
    refreshed = next(m for m in _maps(mindmap) if m["tree_uid"] == free["tree_uid"])
    _delete(mindmap, refreshed)
    _restore(mindmap, free["tree_uid"])
    assert [n["title"] for n in _tree(mindmap, free["tree_uid"])["nodes"]] == ["Bleibt"]


def test_a_node_of_a_deleted_map_cannot_be_restored_alone(mindmap: Env) -> None:
    free = _new_map(mindmap)
    node = _node(mindmap, "Wurzel", free["tree_uid"])
    _delete(mindmap, free)
    response = _restore(mindmap, node["uid"])
    assert response.status_code >= 400
    assert response.json()["code"] == "mindmap_tree_in_trash"


def test_a_name_taken_in_the_meantime_blocks_the_restore(mindmap: Env) -> None:
    free = _new_map(mindmap, "Ideen")
    _delete(mindmap, free)
    _new_map(mindmap, "Ideen")
    response = _restore(mindmap, free["tree_uid"])
    assert response.json()["code"] == "mindmap_map_name_taken"


def test_the_name_of_a_deleted_map_is_free_again(mindmap: Env) -> None:
    free = _new_map(mindmap, "Ideen")
    _delete(mindmap, free)
    assert _new_map(mindmap, "Ideen")["tree_uid"] != free["tree_uid"]


def test_purging_a_deleted_map_removes_it_with_its_nodes(mindmap: Env) -> None:
    free = _new_map(mindmap)
    node = _node(mindmap, "Wurzel", free["tree_uid"])
    _delete(mindmap, free)
    purged = mindmap.client.post("/api/workspace/trash/purge", json={"uids": [free["tree_uid"]]})
    assert purged.status_code == 200, purged.text
    assert not [e for e in _trash(mindmap) if e["uid"] in (free["tree_uid"], node["uid"])]
    assert mindmap.client.get(f"{API}/nodes/{node['uid']}").status_code == 404


def test_items_of_nodes_in_a_deleted_map_fall_back_to_the_project_tree(mindmap: Env) -> None:
    free = _new_map(mindmap)
    top = _node(mindmap, "Oben")
    story = _story(mindmap)
    mindmap.client.post(f"{API}/nodes/{top['uid']}/items", json={"item": story["uid"], "node": top["uid"]})
    _node(mindmap, "Frei", free["tree_uid"])
    _delete(mindmap, free)
    assert mindmap.client.get(f"{API}/items/{story['uid']}/node").json()["node_uid"] == top["uid"]


def test_events_announce_map_changes(mindmap: Env) -> None:
    seen: list[Any] = []
    mindmap.app.state.events.subscribe("mindmap.*", seen.append)
    free = _new_map(mindmap)
    _delete(mindmap, free)
    _restore(mindmap, free["tree_uid"])
    changes = [(e.topic, e.payload["change"]) for e in seen if e.topic == "mindmap.map.changed"]
    assert changes == [
        ("mindmap.map.changed", "created"),
        ("mindmap.map.changed", "deleted"),
        ("mindmap.map.changed", "restored"),
    ]

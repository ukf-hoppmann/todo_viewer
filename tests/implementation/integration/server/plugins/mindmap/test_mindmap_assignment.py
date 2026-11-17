"""Items und Memos an Knoten hängen: Zuordnen und Lösen, Vererbung, Zahlen, Zustand, Papierkorb (`TASK-056`)."""

from __future__ import annotations

from typing import Any

from viewer.core.domain.events import Event
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


def _item(env: Env, type_: str = "Task", parent: dict[str, Any] | None = None, **fields: Any) -> dict[str, Any]:
    extra = {"parent": parent["uid"], "required_for_parent": True} if parent else {}
    response = env.client.post(
        "/api/backlog/items",
        json={"project": _project(env), "type": type_, "fields": {**BASE, **extra, **fields}},
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _status(env: Env, item: dict[str, Any], status: str) -> dict[str, Any]:
    current = env.client.get(f"/api/backlog/items/{item['uid']}").json()
    resolution = "Erledigt" if status in ("Completed", "Rejected") else None
    response = env.client.put(
        f"/api/backlog/items/{item['uid']}",
        json={"version": current["version"], "fields": {"status": status}, "resolution": resolution},
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _memo(env: Env) -> dict[str, Any]:
    response = env.client.post("/api/memos/memos", json={"project": _project(env), "fields": {"summary": "Idee"}})
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _assign(env: Env, node: dict[str, Any], item: dict[str, Any], **body: Any) -> Any:
    return env.client.post(f"{API}/nodes/{node['uid']}/items", json={"item": item["uid"], **body})


def _tree(env: Env, statuses: str | None = None) -> dict[str, Any]:
    params = {"statuses": statuses} if statuses else {}
    response = env.client.get(f"{API}/trees/{_project(env)}", params=params)
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _stats(env: Env, statuses: str | None = None) -> dict[str, tuple[int, int, str]]:
    return {n["title"]: (n["total"], n["done"], n["state"]) for n in _tree(env, statuses)["nodes"]}


def _unassigned(env: Env, statuses: str | None = None) -> list[str]:
    return [i["label"] for i in _tree(env, statuses)["unassigned"]]


def _delete(env: Env, element: dict[str, Any]) -> Any:
    current = env.client.get(f"{API}/nodes/{element['uid']}").json()
    return env.client.request(
        "DELETE",
        f"/api/workspace/elements/{element['uid']}",
        params={"version": current["version"], "cascade": True},
    )


def _restore(env: Env, element: dict[str, Any]) -> Any:
    return env.client.post("/api/workspace/trash/restore", json={"uids": [element["uid"]]})


def _item_node(env: Env, item: dict[str, Any]) -> dict[str, Any]:
    response = env.client.get(f"{API}/items/{item['uid']}/node")
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


# --- Zuordnen und Lösen -------------------------------------------------------------------------------------------


def test_an_item_is_assigned_to_a_node_and_counts_there(mindmap: Env) -> None:
    node = _node(mindmap)
    task = _item(mindmap)

    response = _assign(mindmap, node, task)

    assert response.status_code == 200, response.text
    assert response.json()["uid"] == node["uid"]
    assert _stats(mindmap) == {"Thema": (1, 0, "planned")}
    assert _item_node(mindmap, task) == {"item_uid": task["uid"], "node_uid": node["uid"], "explicit": True}


def test_a_label_works_as_reference_when_the_project_is_given(mindmap: Env) -> None:
    node = _node(mindmap)
    task = _item(mindmap)

    response = mindmap.client.post(
        f"{API}/nodes/{node['label']}/items", json={"item": task["label"], "project": _project(mindmap)}
    )

    assert response.status_code == 200, response.text
    assert _stats(mindmap)["Thema"][0] == 1


def test_a_second_node_for_the_same_item_is_refused(mindmap: Env) -> None:
    first, second = _node(mindmap, "Eins"), _node(mindmap, "Zwei")
    task = _item(mindmap)
    _assign(mindmap, first, task)

    refused = _assign(mindmap, second, task)

    assert refused.status_code == 422 or refused.status_code == 409 or refused.status_code == 400
    assert refused.json()["code"] == "mindmap_item_assigned"
    assert _stats(mindmap) == {"Eins": (1, 0, "planned"), "Zwei": (0, 0, "idea")}


def test_an_item_can_replace_its_node_explicitly(mindmap: Env) -> None:
    first, second = _node(mindmap, "Eins"), _node(mindmap, "Zwei")
    task = _item(mindmap)
    _assign(mindmap, first, task)

    replaced = _assign(mindmap, second, task, replace=True)

    assert replaced.status_code == 200, replaced.text
    assert _stats(mindmap) == {"Eins": (0, 0, "idea"), "Zwei": (1, 0, "planned")}


def test_assigning_to_the_same_node_again_changes_nothing(mindmap: Env) -> None:
    node = _node(mindmap)
    task = _item(mindmap)
    _assign(mindmap, node, task)

    assert _assign(mindmap, node, task).status_code == 200
    assert _stats(mindmap) == {"Thema": (1, 0, "planned")}


def test_unassigning_puts_the_item_back_to_unassigned(mindmap: Env) -> None:
    node = _node(mindmap)
    task = _item(mindmap)
    _assign(mindmap, node, task)

    response = mindmap.client.delete(f"{API}/items/{task['uid']}/node")

    assert response.status_code == 200, response.text
    assert _stats(mindmap) == {"Thema": (0, 0, "idea")}
    assert _unassigned(mindmap) == [task["label"]]
    assert mindmap.client.delete(f"{API}/items/{task['uid']}/node").status_code == 404  # nichts mehr zu lösen


def test_only_items_and_living_nodes_can_be_assigned(mindmap: Env) -> None:
    node = _node(mindmap)
    other = _node(mindmap, "Anderes")
    memo = _memo(mindmap)
    task = _item(mindmap)

    assert _assign(mindmap, node, other).status_code == 422  # ein Knoten ist kein Item
    assert _assign(mindmap, node, memo).status_code == 422  # ein Memo geht über link_memo
    _delete(mindmap, node)
    assert _assign(mindmap, node, task).json()["code"] == "mindmap_node_deleted"


def test_a_trashed_item_cannot_be_assigned(mindmap: Env) -> None:
    node = _node(mindmap)
    task = _item(mindmap)
    mindmap.client.request(
        "DELETE", f"/api/workspace/elements/{task['uid']}", params={"version": task["version"], "cascade": True}
    )

    assert _assign(mindmap, node, task).json()["code"] == "mindmap_item_deleted"


def test_assigning_and_unassigning_are_announced(mindmap: Env) -> None:
    seen: list[Event] = []
    mindmap.app.state.events.subscribe("mindmap.*", seen.append)
    node = _node(mindmap)
    task = _item(mindmap)
    seen.clear()

    _assign(mindmap, node, task)
    mindmap.client.delete(f"{API}/items/{task['uid']}/node")

    assert [(e.topic, e.payload["uid"], e.payload["change"]) for e in seen] == [
        ("mindmap.node.changed", node["uid"], "assigned"),
        ("mindmap.node.changed", node["uid"], "unassigned"),
    ]


def test_the_generic_link_operations_do_not_touch_node_assignments(mindmap: Env) -> None:
    node = _node(mindmap)
    task = _item(mindmap)
    _assign(mindmap, node, task)
    links = mindmap.client.get(f"/api/workspace/elements/{task['uid']}/links").json()
    [link] = [e for e in links["incoming"] if e["role"] == "node"]

    assert mindmap.client.delete(f"/api/workspace/links/{link['link_uid']}").json()["code"] == "node_link_reserved"
    assert _stats(mindmap)["Thema"][0] == 1


# --- Vererbung ----------------------------------------------------------------------------------------------------


def test_children_inherit_the_node_of_their_parent_unless_attached_on_their_own(mindmap: Env) -> None:
    topic, other = _node(mindmap, "Oben"), _node(mindmap, "Daneben")
    epic = _item(mindmap, "Epic")
    story = _item(mindmap, "Story", parent=epic)
    task = _item(mindmap, "Task", parent=story)
    sibling = _item(mindmap, "Story", parent=epic)
    _assign(mindmap, topic, epic)
    _assign(mindmap, other, story)

    assert _stats(mindmap) == {"Oben": (2, 0, "planned"), "Daneben": (2, 0, "planned")}
    assert _item_node(mindmap, task) == {"item_uid": task["uid"], "node_uid": other["uid"], "explicit": False}
    assert _item_node(mindmap, sibling)["node_uid"] == topic["uid"]
    assert _item_node(mindmap, epic)["explicit"] is True
    assert _unassigned(mindmap) == []


def test_items_without_a_node_up_the_chain_are_unassigned(mindmap: Env) -> None:
    epic = _item(mindmap, "Epic")
    story = _item(mindmap, "Story", parent=epic)

    assert _unassigned(mindmap) == [epic["label"], story["label"]]
    assert _item_node(mindmap, story) == {"item_uid": story["uid"], "node_uid": None, "explicit": False}


# --- Summen und Zustand -------------------------------------------------------------------------------------------


def test_sums_run_up_over_empty_nodes_and_each_item_counts_once(mindmap: Env) -> None:
    top = _node(mindmap, "Oben")
    middle = _node(mindmap, "Mitte", parent=top)
    leaf = _node(mindmap, "Blatt", parent=middle)
    _node(mindmap, "Leer", parent=middle)
    epic = _item(mindmap, "Epic")
    story = _item(mindmap, "Story", parent=epic)
    _assign(mindmap, leaf, epic)

    assert _stats(mindmap) == {
        "Oben": (2, 0, "planned"),
        "Mitte": (2, 0, "planned"),
        "Blatt": (2, 0, "planned"),
        "Leer": (0, 0, "idea"),
    }
    assert story["uid"] != epic["uid"]


def test_the_state_follows_the_items_and_progress_counts_the_completed(mindmap: Env) -> None:
    node = _node(mindmap)
    a, b = _item(mindmap), _item(mindmap)
    _assign(mindmap, node, a)
    _assign(mindmap, node, b)
    assert _stats(mindmap)["Thema"] == (2, 0, "planned")

    _status(mindmap, a, "In progress")
    assert _stats(mindmap)["Thema"] == (2, 0, "in_progress")

    _status(mindmap, a, "Completed")
    assert _stats(mindmap)["Thema"] == (2, 1, "in_progress")  # Completed gemischt mit Open

    _status(mindmap, b, "Completed")
    assert _stats(mindmap)["Thema"] == (2, 2, "done")


def test_rejected_items_do_not_decide_the_state(mindmap: Env) -> None:
    node = _node(mindmap)
    only = _item(mindmap)
    _assign(mindmap, node, only)
    _status(mindmap, only, "Rejected")

    assert _stats(mindmap)["Thema"][2] == "idea"


def test_the_status_filter_changes_the_numbers_but_not_the_state(mindmap: Env) -> None:
    node = _node(mindmap)
    done, todo = _item(mindmap), _item(mindmap)
    _assign(mindmap, node, done)
    _assign(mindmap, node, todo)
    _status(mindmap, done, "Completed")

    assert _stats(mindmap)["Thema"] == (2, 1, "in_progress")
    assert _stats(mindmap, "Open")["Thema"] == (1, 0, "in_progress")
    assert _stats(mindmap, "Open,In progress")["Thema"][0] == 1
    assert mindmap.client.get(f"{API}/trees/{_project(mindmap)}", params={"statuses": "Nope"}).status_code == 422


def test_the_filter_also_applies_to_the_unassigned_items(mindmap: Env) -> None:
    done, todo = _item(mindmap), _item(mindmap)
    _status(mindmap, done, "Completed")

    assert _unassigned(mindmap) == [done["label"], todo["label"]]
    assert _unassigned(mindmap, "Open") == [todo["label"]]


def test_trashed_items_never_count(mindmap: Env) -> None:
    node = _node(mindmap)
    kept, gone = _item(mindmap), _item(mindmap)
    _assign(mindmap, node, kept)
    _assign(mindmap, node, gone)

    mindmap.client.request(
        "DELETE", f"/api/workspace/elements/{gone['uid']}", params={"version": gone["version"], "cascade": True}
    )

    assert _stats(mindmap)["Thema"][0] == 1
    assert [i["label"] for i in mindmap.client.get(f"{API}/nodes/{node['uid']}/content").json()["items"]] == [
        kept["label"]
    ]
    assert _unassigned(mindmap) == []


def test_a_project_without_nodes_lists_all_its_items_as_unassigned(mindmap: Env) -> None:
    task = _item(mindmap)

    assert _tree(mindmap) == {
        "project_uid": _project(mindmap),
        "tree_uid": None,
        "nodes": [],
        "unassigned": [{"uid": task["uid"], "label": task["label"], "type": "Task", "title": "Item", "status": "Open"}],
    }


# --- Knoten löschen und wiederherstellen ---------------------------------------------------------------------------


def test_items_of_a_deleted_node_fall_back_to_the_parent_node(mindmap: Env) -> None:
    top = _node(mindmap, "Oben")
    child = _node(mindmap, "Kind", parent=top)
    task = _item(mindmap)
    _assign(mindmap, child, task)

    assert _delete(mindmap, child).status_code == 200

    assert _stats(mindmap) == {"Oben": (1, 0, "planned")}
    assert _item_node(mindmap, task) == {"item_uid": task["uid"], "node_uid": top["uid"], "explicit": False}


def test_items_of_a_deleted_top_node_become_unassigned(mindmap: Env) -> None:
    node = _node(mindmap)
    task = _item(mindmap)
    _assign(mindmap, node, task)

    _delete(mindmap, node)

    assert _tree(mindmap)["nodes"] == []
    assert _unassigned(mindmap) == [task["label"]]


def test_a_deleted_node_gives_its_item_back_to_the_node_of_the_item_parent(mindmap: Env) -> None:
    top, other = _node(mindmap, "Oben"), _node(mindmap, "Anderes")
    epic = _item(mindmap, "Epic")
    story = _item(mindmap, "Story", parent=epic)
    _assign(mindmap, top, epic)
    _assign(mindmap, other, story)

    _delete(mindmap, other)

    assert _item_node(mindmap, story)["node_uid"] == top["uid"]  # als wäre die Zuordnung nie da gewesen


def test_restoring_the_node_restores_the_assignment(mindmap: Env) -> None:
    top = _node(mindmap, "Oben")
    child = _node(mindmap, "Kind", parent=top)
    task = _item(mindmap)
    _assign(mindmap, child, task)
    _delete(mindmap, child)

    restored = _restore(mindmap, child)

    assert restored.status_code == 200, restored.text
    assert _stats(mindmap) == {"Oben": (1, 0, "planned"), "Kind": (1, 0, "planned")}
    assert _item_node(mindmap, task) == {"item_uid": task["uid"], "node_uid": child["uid"], "explicit": True}


def test_a_branch_with_its_items_goes_to_the_trash_and_comes_back_together(mindmap: Env) -> None:
    top = _node(mindmap, "Oben")
    child = _node(mindmap, "Kind", parent=top)
    task = _item(mindmap)
    _assign(mindmap, child, task)
    _delete(mindmap, top)

    assert _unassigned(mindmap) == [task["label"]]
    _restore(mindmap, top)
    assert _unassigned(mindmap) == []
    assert _stats(mindmap)["Oben"][0] == 1


# --- Memos --------------------------------------------------------------------------------------------------------


def test_a_memo_can_be_linked_to_several_nodes_and_does_not_count(mindmap: Env) -> None:
    one, two = _node(mindmap, "Eins"), _node(mindmap, "Zwei")
    memo = _memo(mindmap)

    for node in (one, two):
        response = mindmap.client.post(f"{API}/nodes/{node['uid']}/memos", json={"memo": memo["uid"]})
        assert response.status_code == 200, response.text

    assert _stats(mindmap) == {"Eins": (0, 0, "idea"), "Zwei": (0, 0, "idea")}
    for node in (one, two):
        content = mindmap.client.get(f"{API}/nodes/{node['uid']}/content").json()
        assert [m["label"] for m in content["memos"]] == [memo["label"]]
    nodes = mindmap.client.get(f"{API}/memos/{memo['uid']}/nodes").json()
    assert sorted(n["title"] for n in nodes) == ["Eins", "Zwei"]


def test_linking_a_memo_twice_changes_nothing_and_it_can_be_unlinked(mindmap: Env) -> None:
    node = _node(mindmap)
    memo = _memo(mindmap)
    url = f"{API}/nodes/{node['uid']}/memos"
    mindmap.client.post(url, json={"memo": memo["uid"]})
    assert mindmap.client.post(url, json={"memo": memo["uid"]}).status_code == 200

    assert mindmap.client.delete(f"{url}/{memo['uid']}").status_code == 200

    assert mindmap.client.get(f"{API}/nodes/{node['uid']}/content").json()["memos"] == []
    assert mindmap.client.delete(f"{url}/{memo['uid']}").status_code == 404


def test_a_memo_link_rests_in_the_trash_with_the_node_and_returns_with_it(mindmap: Env) -> None:
    node = _node(mindmap)
    memo = _memo(mindmap)
    mindmap.client.post(f"{API}/nodes/{node['uid']}/memos", json={"memo": memo["uid"]})

    _delete(mindmap, node)
    assert mindmap.client.get(f"{API}/memos/{memo['uid']}/nodes").json() == []
    assert mindmap.client.get(f"/api/memos/memos/{memo['uid']}").json()["summary"] == "Idee"  # das Memo bleibt

    _restore(mindmap, node)
    assert [n["uid"] for n in mindmap.client.get(f"{API}/memos/{memo['uid']}/nodes").json()] == [node["uid"]]


def test_an_item_cannot_be_linked_as_a_memo(mindmap: Env) -> None:
    node = _node(mindmap)
    task = _item(mindmap)

    response = mindmap.client.post(f"{API}/nodes/{node['uid']}/memos", json={"memo": task["uid"]})

    assert response.status_code == 422


def test_the_content_of_a_node_lists_only_its_own_items_by_the_status_filter(mindmap: Env) -> None:
    top = _node(mindmap, "Oben")
    child = _node(mindmap, "Kind", parent=top)
    a, b, deeper = _item(mindmap), _item(mindmap), _item(mindmap)
    _assign(mindmap, top, a)
    _assign(mindmap, top, b)
    _assign(mindmap, child, deeper)
    _status(mindmap, b, "Completed")

    def labels(statuses: str | None = None) -> list[str]:
        params = {"statuses": statuses} if statuses else {}
        body = mindmap.client.get(f"{API}/nodes/{top['uid']}/content", params=params).json()
        return [i["label"] for i in body["items"]]

    assert labels() == [a["label"], b["label"]]
    assert labels("Open") == [a["label"]]

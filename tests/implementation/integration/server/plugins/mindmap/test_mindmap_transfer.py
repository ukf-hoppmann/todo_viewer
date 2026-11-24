"""Einen Ast ins Backlog überführen, echte Plugins `workspace`, `backlog`, `memos`, `mindmap` (`TASK-074`)."""

from __future__ import annotations

from typing import Any

from workspace_env import Env

API = "/api/mindmap"
CRIT = "1. Fertig"


def _project(env: Env) -> str:
    return str(env.general()["uid"])


def _node(env: Env, title: str, parent: dict[str, Any] | None = None, text: str | None = "Ziel") -> dict[str, Any]:
    body = {"project": _project(env), "title": title, "text": text, "parent": parent["uid"] if parent else None}
    response = env.client.post(f"{API}/nodes", json=body)
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _chain(env: Env, depth: int) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for level in range(depth):
        nodes.append(_node(env, f"Ebene {level + 1}", nodes[-1] if nodes else None, text=f"Text {level + 1}"))
    return nodes


def _entry(node: dict[str, Any], type_: str | None = "Task", kind: str = "item", **rest: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"node": node["uid"], "kind": kind, "type": type_}
    if kind == "item":
        base["completion_criteria"] = CRIT
    return {**base, **rest}


def _post(env: Env, route: str, root: dict[str, Any], entries: list[dict[str, Any]], **rest: Any) -> Any:
    return env.client.post(f"{API}/nodes/{root['uid']}/{route}", json={"entries": entries, **rest})


def _items(env: Env) -> list[dict[str, Any]]:
    return env.client.get("/api/backlog/items", params={"project": _project(env)}).json()  # type: ignore[no-any-return]


def _item(env: Env, uid: str) -> dict[str, Any]:
    return env.client.get(f"/api/backlog/items/{uid}").json()  # type: ignore[no-any-return]


def test_a_branch_becomes_epic_story_and_task_with_parents_and_nodes(mindmap: Env) -> None:
    a, b, c = _chain(mindmap, 3)
    entries = [_entry(c, "Task", parent=b["uid"]), _entry(b, "Story", parent=a["uid"]), _entry(a, "Epic")]
    preview = _post(mindmap, "preview-branch-transfer", a, entries).json()
    assert preview["ok"] and preview["order"] == [a["uid"], b["uid"], c["uid"]]
    assert _items(mindmap) == []  # die Vorschau schreibt nichts

    result = _post(mindmap, "transfer-branch", a, entries)
    assert result.status_code == 200, result.text
    created = {e["node"]: e for e in result.json()["entries"]}
    assert {e["status"] for e in created.values()} == {"created"}
    epic = _item(mindmap, created[a["uid"]]["created"]["uid"])
    story = _item(mindmap, created[b["uid"]]["created"]["uid"])
    task = _item(mindmap, created[c["uid"]]["created"]["uid"])
    assert (epic["type"], story["type"], task["type"]) == ("Epic", "Story", "Task")
    assert story["parent"]["uid"] == epic["uid"] and task["parent"]["uid"] == story["uid"]
    assert (task["title"], task["goal"], task["required_for_parent"]) == ("Ebene 3", "Text 3", True)
    on_node = mindmap.client.get(f"{API}/items/{task['uid']}/node").json()
    assert on_node["node_uid"] == c["uid"] and on_node["explicit"]
    tree = mindmap.client.get(f"{API}/trees/{_project(mindmap)}").json()
    assert {n["uid"]: n["state"] for n in tree["nodes"]}[a["uid"]] == "planned"


def test_a_node_in_depth_five_can_be_an_epic_of_its_own(mindmap: Env) -> None:
    nodes = _chain(mindmap, 5)
    entries = [_entry(nodes[0], "Epic"), _entry(nodes[1], "Story", parent=nodes[0]["uid"]), _entry(nodes[4], "Epic")]
    result = _post(mindmap, "transfer-branch", nodes[0], entries).json()
    status = {e["node"]: e["status"] for e in result["entries"]}
    assert status[nodes[4]["uid"]] == "created" and status[nodes[2]["uid"]] == "skipped"
    deep = next(i for i in _items(mindmap) if i["title"] == "Ebene 5")
    assert deep["type"] == "Epic" and _item(mindmap, deep["uid"])["parent"] is None


def test_a_dependency_instead_of_a_parent(mindmap: Env) -> None:
    root = _node(mindmap, "Wurzel")
    first = _node(mindmap, "Zuerst", root)
    second = _node(mindmap, "Danach", root)
    entries = [_entry(second, "Task", depends_on=[first["uid"]]), _entry(first, "Task")]
    result = _post(mindmap, "transfer-branch", root, entries).json()
    by_node = {e["node"]: e["created"]["uid"] for e in result["entries"] if e["created"]}
    later = _item(mindmap, by_node[second["uid"]])
    assert later["parent"] is None
    assert [d["uid"] for d in later["dependencies"]] == [by_node[first["uid"]]]


def test_a_memo_in_the_plan_is_linked_to_its_node(mindmap: Env) -> None:
    root = _node(mindmap, "Wurzel")
    idea = _node(mindmap, "Später klären", root, text="Frage")
    result = _post(mindmap, "transfer-branch", root, [_entry(root, "Task"), _entry(idea, None, "memo")]).json()
    memo = next(e for e in result["entries"] if e["node"] == idea["uid"])["created"]
    content = mindmap.client.get(f"{API}/nodes/{idea['uid']}/content").json()
    assert [m["uid"] for m in content["memos"]] == [memo["uid"]]
    memo_doc = mindmap.client.get(f"/api/memos/memos/{memo['uid']}").json()
    assert (memo_doc["summary"], memo_doc["body"]) == ("Später klären", "Frage")


def test_an_epic_below_a_task_is_reported_and_nothing_is_created(mindmap: Env) -> None:
    a, b = _chain(mindmap, 2)
    entries = [_entry(a, "Task"), _entry(b, "Epic", parent=a["uid"])]
    preview = _post(mindmap, "preview-branch-transfer", a, entries).json()
    assert not preview["ok"]
    problems = {e["node"]: [p["code"] for p in e["problems"]] for e in preview["entries"]}
    assert problems[b["uid"]] == ["parent_type_not_allowed"] and problems[a["uid"]] == []
    blocked = _post(mindmap, "transfer-branch", a, entries)
    assert blocked.status_code in (400, 409, 422), blocked.text
    assert blocked.json()["code"] == "transfer_blocked"
    assert _items(mindmap) == []


def test_missing_fields_cycles_and_existing_parents_are_reported(mindmap: Env) -> None:
    root = _node(mindmap, "Wurzel")
    one = _node(mindmap, "Eins", root)
    two = _node(mindmap, "Zwei", root)
    entries = [
        {"node": one["uid"], "kind": "item", "type": "Task"},
        _entry(two, "Task", depends_on=[root["uid"]]),
        _entry(root, "Task", depends_on=[two["uid"]]),
    ]
    preview = _post(mindmap, "preview-branch-transfer", root, entries, project=_project(mindmap)).json()
    problems = {e["node"]: {p["code"] for p in e["problems"]} for e in preview["entries"]}
    assert "criteria_missing" in problems[one["uid"]]
    assert "dependency_cycle" in problems[two["uid"]]
    assert "dependency_cycle" in problems[root["uid"]]
    assert any(p["code"] == "dependency_cycle" for p in preview["problems"])


def test_a_node_outside_the_branch_and_a_duplicate_are_reported(mindmap: Env) -> None:
    root = _node(mindmap, "Wurzel")
    inside = _node(mindmap, "Innen", root)
    outside = _node(mindmap, "Außen")
    entries = [_entry(inside), _entry(inside), _entry(outside)]
    preview = _post(mindmap, "preview-branch-transfer", root, entries).json()
    codes = [[p["code"] for p in e["problems"]] for e in preview["entries"]]
    assert codes == [[], ["node_duplicate"], ["node_not_in_branch"]]


def test_an_unknown_existing_parent_is_reported(mindmap: Env) -> None:
    root = _node(mindmap, "Wurzel")
    preview = _post(
        mindmap, "preview-branch-transfer", root, [_entry(root, "Task", parent="STORY-999")], project=_project(mindmap)
    ).json()
    assert [p["code"] for p in preview["entries"][0]["problems"]] == ["parent_not_found"]


def test_an_existing_item_can_be_the_parent_and_a_closed_one_is_reported(mindmap: Env) -> None:
    root = _node(mindmap, "Wurzel")
    story = mindmap.client.post(
        "/api/backlog/items",
        json={
            "project": _project(mindmap),
            "type": "Story",
            "fields": {"title": "Alt", "goal": "g", "completion_criteria": "1. x"},
        },
    ).json()
    ok = _post(mindmap, "transfer-branch", root, [_entry(root, "Task", parent=story["uid"])])
    assert ok.status_code == 200, ok.text
    created = ok.json()["entries"][0]["created"]
    assert _item(mindmap, created["uid"])["parent"]["uid"] == story["uid"]
    closed = mindmap.client.patch(
        f"/api/backlog/items/{story['uid']}",
        json={
            "version": _item(mindmap, story["uid"])["version"],
            "fields": {"status": "Rejected"},
            "resolution": "nein",
        },
    )
    if closed.status_code == 200:
        again = _post(mindmap, "preview-branch-transfer", root, [_entry(root, "Task", parent=story["uid"])]).json()
        assert not again["ok"]


def test_a_failing_entry_keeps_what_was_created_and_stops_its_followers(mindmap: Env) -> None:
    a, b, c = _chain(mindmap, 3)
    entries = [_entry(a, "Epic"), _entry(b, "Story", parent=a["uid"]), _entry(c, "Task", parent=b["uid"])]
    services = mindmap.app.state.plugin_host.services("mindmap")
    original = services.creation.create_item

    def flaky(node: str, type_: str, fields: dict[str, Any], project: str | None) -> Any:
        if node == b["uid"]:
            from viewer.core.domain.errors import DomainError

            raise DomainError("kaputt", code="backlog_broken")
        return original(node, type_, fields, project)

    services.creation.create_item = flaky
    result = _post(mindmap, "transfer-branch", a, entries).json()
    status = {e["node"]: e["status"] for e in result["entries"]}
    assert status == {a["uid"]: "created", b["uid"]: "failed", c["uid"]: "not_attempted"}
    assert next(e for e in result["entries"] if e["status"] == "failed")["error"]["code"] == "backlog_broken"
    assert [i["type"] for i in _items(mindmap)] == ["Epic"]


def test_the_same_plan_twice_creates_duplicates(mindmap: Env) -> None:
    root = _node(mindmap, "Wurzel")
    entries = [_entry(root, "Task")]
    for _ in range(2):
        assert _post(mindmap, "transfer-branch", root, entries).status_code == 200
    assert len(_items(mindmap)) == 2

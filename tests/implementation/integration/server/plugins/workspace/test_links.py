from __future__ import annotations

from typing import Any

import pytest
from viewer.core.domain.errors import NotFound
from viewer.plugins.workspace.domain.model import LinkExists, NodeLinkReserved, TriggerLinkReserved
from workspace_env import Env


def _element(env: Env, project: str, kind: str = "task", title: str = "") -> Any:
    return env.kinds.run(lambda registry, tx: registry.register(tx, project, kind, title))


def _link(env: Env, a: str, b: str, role: str = "reference") -> Any:
    return env.client.post("/api/workspace/links", json={"from_uid": a, "to_uid": b, "role": role})


def _links(env: Env, uid: str) -> dict[str, Any]:
    return env.client.get(f"/api/workspace/elements/{uid}/links").json()  # type: ignore[no-any-return]


def test_add_and_list_links_in_both_directions(env: Env) -> None:
    project = str(env.general()["uid"])
    note = _element(env, project, "story", "Idee")
    task = _element(env, project, "task", "Umsetzen")

    added = _link(env, note.uid, task.uid, "origin")

    assert added.status_code == 200
    assert (added.json()["uid"], added.json()["label"], added.json()["role"], added.json()["title"]) == (
        task.uid,
        "TASK-001",
        "origin",
        "Umsetzen",
    )
    out = _links(env, note.uid)
    assert [(e["label"], e["role"]) for e in out["outgoing"]] == [("TASK-001", "origin")]
    assert out["incoming"] == []
    back = _links(env, task.uid)
    assert [(e["label"], e["role"]) for e in back["incoming"]] == [("STORY-001", "origin")]
    assert back["outgoing"] == []


def test_links_cross_projects_and_allow_every_role_once_per_pair(env: Env) -> None:
    a = _element(env, str(env.create("A")["uid"]))
    b = _element(env, str(env.create("B")["uid"]))

    assert _link(env, a.uid, b.uid, "reference").status_code == 200
    assert _link(env, a.uid, b.uid, "origin").status_code == 200
    again = _link(env, a.uid, b.uid, "reference")

    assert (again.status_code, again.json()["code"]) == (400, "link_exists")
    assert len(_links(env, a.uid)["outgoing"]) == 2
    assert _link(env, b.uid, a.uid, "reference").status_code == 200  # die Gegenrichtung ist eine eigene Verknüpfung


def test_refuses_unknown_role_self_link_and_unknown_elements(env: Env) -> None:
    a = _element(env, str(env.general()["uid"]))

    assert _link(env, a.uid, a.uid).json()["code"] == "invalid_link"
    assert _link(env, a.uid, "gibt-es-nicht").status_code == 404
    assert _link(env, "gibt-es-nicht", a.uid).status_code == 404
    unknown = env.client.post("/api/workspace/links", json={"from_uid": a.uid, "to_uid": "x", "role": "kaputt"})
    assert unknown.status_code == 422


def test_the_trigger_role_is_reserved_for_the_port(env: Env) -> None:
    project = str(env.general()["uid"])
    a, b = _element(env, project), _element(env, project)

    refused = _link(env, a.uid, b.uid, "trigger")
    link = env.kinds.run_links(lambda links, tx: links.add(tx, a.uid, b.uid, "trigger"))
    remove = env.client.delete(f"/api/workspace/links/{link.uid}")

    assert (refused.status_code, refused.json()["code"]) == (400, "trigger_link_reserved")
    assert (remove.status_code, remove.json()["code"]) == (400, "trigger_link_reserved")
    assert [e["role"] for e in _links(env, a.uid)["outgoing"]] == ["trigger"]
    env.kinds.run_links(lambda links, tx: links.remove(tx, link.uid))
    assert _links(env, a.uid)["outgoing"] == []


def test_remove_a_link(env: Env) -> None:
    project = str(env.general()["uid"])
    a, b = _element(env, project), _element(env, project)
    link_uid = _link(env, a.uid, b.uid).json()["link_uid"]

    removed = env.client.delete(f"/api/workspace/links/{link_uid}")
    missing = env.client.delete(f"/api/workspace/links/{link_uid}")

    assert removed.json() == {"removed": True}
    assert missing.status_code == 404
    assert _links(env, a.uid)["outgoing"] == []


def test_links_survive_a_kind_change_and_follow_the_new_label(env: Env) -> None:
    project = str(env.general()["uid"])
    a, b = _element(env, project, "task"), _element(env, project, "task")
    _link(env, a.uid, b.uid)

    env.kinds.run(lambda registry, tx: registry.relabel(tx, b.uid, "story"))

    assert [(e["uid"], e["label"], e["kind"]) for e in _links(env, a.uid)["outgoing"]] == [
        (b.uid, "STORY-001", "story")
    ]


def test_a_link_to_an_element_in_the_trash_stays_and_is_marked(env: Env) -> None:
    project = str(env.general()["uid"])
    a, b = _element(env, project), _element(env, project)
    _link(env, a.uid, b.uid)

    env.kinds.run(lambda registry, tx: registry.mark_deleted(tx, b.uid))
    marked = _links(env, a.uid)["outgoing"]
    env.kinds.run(lambda registry, tx: registry.restore(tx, b.uid))

    assert [e["deleted"] for e in marked] == [True]
    assert [e["deleted"] for e in _links(env, a.uid)["outgoing"]] == [False]


def test_purging_an_element_removes_its_links(env: Env) -> None:
    project = str(env.general()["uid"])
    a, b = _element(env, project), _element(env, project)
    _link(env, a.uid, b.uid)

    env.kinds.run(lambda registry, tx: registry.purge(tx, b.uid))

    assert _links(env, a.uid)["outgoing"] == []
    assert env.client.get(f"/api/workspace/elements/{b.uid}/links").status_code == 404


def test_link_changes_are_public_events(env: Env) -> None:
    project = str(env.general()["uid"])
    a, b = _element(env, project), _element(env, project)
    seen: list[tuple[str, bool, str, str]] = []
    env.app.state.events.subscribe(
        "workspace.links.changed", lambda e: seen.append((e.topic, e.public, e.payload["change"], e.payload["role"]))
    )

    link_uid = _link(env, a.uid, b.uid).json()["link_uid"]
    env.client.delete(f"/api/workspace/links/{link_uid}")

    assert seen == [
        ("workspace.links.changed", True, "added", "reference"),
        ("workspace.links.changed", True, "removed", "reference"),
    ]


def test_search_finds_elements_of_all_projects_by_label_and_title_but_not_deleted_ones(env: Env) -> None:
    one = _element(env, str(env.create("A")["uid"]), "task", "Sync im Hintergrund")
    two = _element(env, str(env.create("B")["uid"]), "story", "Unrelated")
    gone = _element(env, str(env.general()["uid"]), "task", "Sync alt")
    env.kinds.run(lambda registry, tx: registry.mark_deleted(tx, gone.uid))

    def search(query: str) -> list[str]:
        r = env.client.get("/api/workspace/elements", params={"query": query})
        return [e["uid"] for e in r.json()]

    assert search("sync") == [one.uid]
    assert search("story-001") == [two.uid]
    assert search("TASK") == [one.uid]
    assert search("") == []
    assert search("100%") == []
    env.kinds.run(lambda registry, tx: registry.set_title(tx, two.uid, "Jetzt mit Sync"))
    assert sorted(search("sync")) == sorted([one.uid, two.uid])


def test_the_port_rejects_unknown_ends(env: Env) -> None:
    a = _element(env, str(env.general()["uid"]))

    with pytest.raises(NotFound):
        env.kinds.run_links(lambda links, tx: links.add(tx, a.uid, "nope", "reference"))
    with pytest.raises(LinkExists):
        b = _element(env, str(env.general()["uid"]))
        env.kinds.run_links(lambda links, tx: links.add(tx, a.uid, b.uid, "reference"))
        env.kinds.run_links(lambda links, tx: links.add(tx, a.uid, b.uid, "reference"))
    with pytest.raises(TriggerLinkReserved):
        env.services_links().add_link(a.uid, "x", "trigger")


def test_the_role_node_belongs_to_the_mindmap_and_is_neither_added_nor_removed_by_hand(env: Env) -> None:
    a = _element(env, str(env.general()["uid"]))
    b = _element(env, str(env.general()["uid"]))
    link = env.kinds.run_links(lambda links, tx: links.add(tx, a.uid, b.uid, "node"))

    with pytest.raises(NodeLinkReserved):
        env.services_links().add_link(a.uid, b.uid, "node")
    with pytest.raises(NodeLinkReserved):
        env.services_links().remove_link(link.uid)
    assert _link(env, a.uid, b.uid, "node").json()["code"] == "node_link_reserved"
    assert [(e["role"], e["label"]) for e in _links(env, a.uid)["outgoing"]] == [("node", "TASK-002")]


def test_link_tools_are_available_to_mcp(env: Env) -> None:
    names = {
        op.name
        for p in env.app.state.plugin_host.plugins
        if p.definition.id == "workspace"
        for op in p.definition.operations
        if op.mcp
    }

    assert {"add_link", "remove_link", "list_links", "search_elements"} <= names

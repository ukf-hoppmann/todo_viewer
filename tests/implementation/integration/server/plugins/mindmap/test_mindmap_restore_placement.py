"""Entfernte Platzierungen merken und wieder einsetzen (`TASK-066`)."""

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


def _node(env: Env, title: str, **fields: Any) -> dict[str, Any]:
    response = env.client.post(
        f"{API}/nodes", json={"project": _project(env), "title": title, **fields}
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _get(env: Env, node: dict[str, Any], tree: str | None = None) -> dict[str, Any]:
    response = env.client.get(
        f"{API}/nodes/{node['uid']}", params={"tree": tree} if tree else {}
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _titles(env: Env, tree: str | None = None) -> list[tuple[str, str | None, int]]:
    """(Titel, Titel des Parents, Stelle) der Knoten des Baums."""
    params = {"tree": tree} if tree else {}
    nodes = env.client.get(f"{API}/trees/{_project(env)}", params=params).json()[
        "nodes"
    ]
    by_uid = {n["uid"]: n["title"] for n in nodes}
    return [(n["title"], by_uid.get(n["parent_uid"]), n["position"]) for n in nodes]


def _act(env: Env, node: dict[str, Any], action: str, **body: Any) -> Any:
    fresh = _get(env, node)  # die Version gehört dem Knoten, nicht dem Baum
    return env.client.post(
        f"{API}/nodes/{node['uid']}/{action}",
        json={"version": fresh["version"], **body},
    )


def _removed(env: Env, node: dict[str, Any]) -> list[dict[str, Any]]:
    response = env.client.get(f"{API}/nodes/{node['uid']}/removed")
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _project_tree(env: Env) -> str:
    return str(env.client.get(f"{API}/trees/{_project(env)}").json()["tree_uid"])


def _shared(env: Env) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    """Ast (Kind (Enkel)) neben Anderes, in "Ideen" und im Projektbaum."""
    ideas = _new_map(env)
    top = _node(env, "Ast")
    kid = _node(env, "Kind", parent=top["uid"])
    _node(env, "Enkel", parent=kid["uid"])
    _node(env, "Anderes")
    assert _act(env, top, "transfer", target=ideas).status_code == 200
    return top, kid, _get(env, kid, ideas), ideas


def test_a_removed_branch_returns_as_a_group_to_its_old_place(mindmap: Env) -> None:
    top, _, _, ideas = _shared(mindmap)
    before = _titles(mindmap, ideas)

    assert _act(mindmap, top, "remove", tree=ideas).status_code == 200
    assert _titles(mindmap, ideas) == []
    assert _titles(mindmap)  # im Projektbaum bleibt er

    found = _removed(mindmap, top)
    assert [(f["tree_uid"], f["parent_available"], f["nodes"]) for f in found] == [
        (ideas, True, 3)
    ]

    response = _act(mindmap, top, "restore-placement", tree=ideas)
    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["nodes_restored"], body["fell_back_to_root"]) == (3, False)
    assert _titles(mindmap, ideas) == before
    assert _removed(mindmap, top) == []


def test_removed_placements_are_ignored_by_counts_and_queries(mindmap: Env) -> None:
    top, _, _, ideas = _shared(mindmap)
    _act(mindmap, top, "remove", tree=ideas)

    in_project = {
        n["title"]: n
        for n in mindmap.client.get(f"{API}/trees/{_project(mindmap)}").json()["nodes"]
    }
    assert in_project["Ast"]["tree_count"] == 1  # die entfernte Platzierung zählt nicht
    trees = mindmap.client.get(f"{API}/nodes/{top['uid']}/trees").json()
    assert [t["tree_uid"] for t in trees] != [] and ideas not in [
        t["tree_uid"] for t in trees
    ]
    maps = mindmap.client.get(f"{API}/maps/{_project(mindmap)}").json()
    assert next(m for m in maps if m["tree_uid"] == ideas)["node_count"] == 0

    # „höchstens einmal je Baum“ gilt nur für gültige Platzierungen: derselbe Ast darf wieder in den Baum
    assert _act(mindmap, top, "transfer", target=ideas).status_code == 200
    assert len(_titles(mindmap, ideas)) == 3


def test_a_missing_old_parent_puts_the_branch_under_the_root_and_says_so(
    mindmap: Env,
) -> None:
    top, _, kid, ideas = _shared(mindmap)
    _act(mindmap, kid, "remove", tree=ideas)
    _act(
        mindmap, top, "remove", tree=ideas
    )  # der alte Parent von Kind ist selbst entfernt

    assert [f["parent_available"] for f in _removed(mindmap, kid)] == [False]
    response = _act(mindmap, kid, "restore-placement", tree=ideas)
    assert response.status_code == 200, response.text
    assert response.json()["fell_back_to_root"] is True
    assert [(t, p) for t, p, _ in _titles(mindmap, ideas)] == [
        ("Kind", None),
        ("Enkel", "Kind"),
    ]


def test_a_node_that_stands_in_the_tree_again_is_not_restored(mindmap: Env) -> None:
    top, _, _, ideas = _shared(mindmap)
    _act(mindmap, top, "remove", tree=ideas)
    _act(mindmap, top, "transfer", target=ideas)

    response = _act(mindmap, top, "restore-placement", tree=ideas)
    assert response.status_code >= 400
    assert response.json()["code"] == "mindmap_node_in_tree"
    assert _removed(mindmap, top) == []
    assert len(_titles(mindmap, ideas)) == 3


def test_nothing_to_restore_and_a_map_in_the_trash_are_rejected(mindmap: Env) -> None:
    top, _, _, ideas = _shared(mindmap)
    assert (
        _act(mindmap, top, "restore-placement", tree=ideas).json()["code"]
        == "mindmap_node_in_tree"
    )
    other = _new_map(mindmap, "Andere")
    assert (
        _act(mindmap, top, "restore-placement", tree=other).json()["code"]
        == "mindmap_nothing_to_restore"
    )

    _act(mindmap, top, "remove", tree=ideas)
    mindmap.client.request("DELETE", f"{API}/maps/{ideas}", params={"version": 1})
    assert (
        _act(mindmap, top, "restore-placement", tree=ideas).json()["code"]
        == "mindmap_tree_deleted"
    )
    assert _removed(mindmap, top) == []  # Maps im Papierkorb bieten nichts an


def test_a_tree_is_needed_when_the_node_was_removed_from_several(mindmap: Env) -> None:
    top, _, _, ideas = _shared(mindmap)
    more = _new_map(mindmap, "Mehr")
    _act(mindmap, top, "transfer", target=more, tree=_project_tree(mindmap))
    _act(mindmap, top, "remove", tree=ideas)
    r = _act(mindmap, top, "remove", tree=more)
    assert r.status_code == 200, r.text
    # steht nur noch im Projektbaum; beide Entfernungen sind gemerkt
    assert _act(mindmap, top, "restore-placement").json()["code"] == "invalid_input"
    assert _act(mindmap, top, "restore-placement", tree=more).status_code == 200
    assert (
        _act(mindmap, top, "restore-placement").status_code == 200
    )  # nun bleibt genau eine


def test_a_restore_needs_the_current_version(mindmap: Env) -> None:
    top, _, _, ideas = _shared(mindmap)
    _act(mindmap, top, "remove", tree=ideas)
    stale = mindmap.client.post(
        f"{API}/nodes/{top['uid']}/restore-placement",
        json={"version": 1, "tree": ideas},
    )
    assert stale.status_code == 409
    assert _titles(mindmap, ideas) == []


def test_a_member_in_the_trash_stays_removed_while_the_rest_returns(
    mindmap: Env,
) -> None:
    top, _, kid, ideas = _shared(mindmap)
    _act(mindmap, top, "remove", tree=ideas)
    # Kind liegt nun nur noch im Projektbaum unter Ast; ganz löschen (mit Enkel) und Ast wieder einsetzen
    fresh = _get(mindmap, kid)
    assert (
        mindmap.client.request(
            "DELETE", f"{API}/nodes/{kid['uid']}", params={"version": fresh["version"]}
        ).status_code
        == 200
    )

    response = _act(mindmap, top, "restore-placement", tree=ideas)
    assert response.status_code == 200, response.text
    assert (response.json()["nodes_restored"], response.json()["nodes_skipped"]) == (
        1,
        2,
    )
    assert [t for t, _, _ in _titles(mindmap, ideas)] == ["Ast"]

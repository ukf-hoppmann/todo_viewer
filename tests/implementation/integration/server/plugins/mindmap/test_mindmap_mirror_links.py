"""Die Mindmap im Spiegel (Zuordnungen, Dokumente, entfernte Platzierungen, Papierkorb): echter Sync, echte Dateien."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from mindmap_mirror_env import API, BASE, MAP_UID, NODE_UIDS, Mirror, example_files, map_file, node_file, project_file
from viewer.core.domain.settings import Settings
from workspace_env import Env, mindmap_env

ELSE = "Anderes"


def _item(mirror: Mirror, kind: str = "Task", project: str | None = None) -> dict[str, Any]:
    response = mirror.env.client.post(
        "/api/backlog/items", json={"project": project or mirror.project, "type": kind, "fields": BASE}
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _memo(mirror: Mirror, project: str | None = None) -> dict[str, Any]:
    response = mirror.env.client.post(
        "/api/memos/memos", json={"project": project or mirror.project, "fields": {"summary": "Idee"}}
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _assign(mirror: Mirror, node: str, item: dict[str, Any]) -> None:
    response = mirror.env.client.post(f"{API}/nodes/{node}/items", json={"item": item["uid"]})
    assert response.status_code == 200, response.text


def _link(mirror: Mirror, node: str, memo: dict[str, Any]) -> None:
    response = mirror.env.client.post(f"{API}/nodes/{node}/memos", json={"memo": memo["uid"]})
    assert response.status_code == 200, response.text


def _item_node(mirror: Mirror, item: dict[str, Any]) -> dict[str, Any]:
    return mirror.env.client.get(f"{API}/items/{item['uid']}/node").json()  # type: ignore[no-any-return]


def _memo_nodes(mirror: Mirror, memo: dict[str, Any]) -> list[str]:
    return [n["uid"] for n in mirror.env.client.get(f"{API}/memos/{memo['uid']}/nodes").json()]


def _other_project(mirror: Mirror) -> str:
    response = mirror.env.client.post("/api/workspace/projects", json={"name": ELSE})
    assert response.status_code == 200, response.text
    return str(response.json()["uid"])


def _with_links(mirror: Mirror, label: str, title: str, items: Sequence[str] = (), memos: Sequence[str] = ()) -> None:
    """Die Datei des Knotens mit den Zuordnungen im Kopf."""
    text = mirror.text(f"mindmap/{label}.md")
    head, _, body = text.partition("\n\n")
    head = head.rstrip("\n")
    head = "\n".join(line for line in head.split("\n") if not line.startswith(("- ", "Items:", "Memos:")))
    if items:
        head += "\nItems:\n" + "\n".join(f"- {t}" for t in items)
    if memos:
        head += "\nMemos:\n" + "\n".join(f"- {t}" for t in memos)
    mirror.write(f"mindmap/{label}.md", head + ("\n\n" + body if body else "\n"))


# --- Zuordnungen -----------------------------------------------------------------------------------------------------


def test_assignments_of_the_database_are_written_on_the_node(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    node = mirror.node("Ast")
    item, memo = _item(mirror), _memo(mirror)
    _assign(mirror, node["uid"], item)
    _link(mirror, node["uid"], memo)

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert f"Items:\n- Beispiel:{item['label']}\nMemos:\n- Beispiel:{memo['label']}\n" in mirror.text(
        "mindmap/NODE-001.md"
    )
    assert mirror.status()["state"] == "in_sync"


def test_assignments_in_the_files_reach_the_database_and_leave_the_items_alone(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.sync()
    item, memo = _item(mirror), _memo(mirror)
    second = _memo(mirror)
    mirror.env.client.get(f"/api/backlog/items/{item['uid']}")
    version = mirror.env.client.get(f"/api/backlog/items/{item['uid']}").json()["version"]
    _with_links(mirror, "NODE-001", "A", items=[item["label"]], memos=[f"Beispiel:{memo['label']}", second["label"]])
    _with_links(mirror, "NODE-002", "B", memos=[memo["label"]])

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert _item_node(mirror, item)["node_uid"] == NODE_UIDS[0]
    assert _item_node(mirror, item)["explicit"] is True
    assert sorted(_memo_nodes(mirror, memo)) == sorted([NODE_UIDS[0], NODE_UIDS[1]])
    assert _memo_nodes(mirror, second) == [NODE_UIDS[0]]
    assert mirror.env.client.get(f"/api/backlog/items/{item['uid']}").json()["version"] == version
    assert mirror.status()["state"] == "in_sync"


def test_an_assignment_removed_in_the_files_is_dissolved_but_the_item_stays(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.sync()
    item, memo = _item(mirror), _memo(mirror)
    _assign(mirror, NODE_UIDS[0], item)
    _link(mirror, NODE_UIDS[0], memo)
    mirror.sync()
    _with_links(mirror, "NODE-001", "A")

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert _item_node(mirror, item)["node_uid"] is None
    assert _memo_nodes(mirror, memo) == []
    assert mirror.env.client.get(f"/api/backlog/items/{item['uid']}").status_code == 200
    assert "Items:" not in mirror.text("mindmap/NODE-001.md")


def test_an_item_moved_between_nodes_in_the_files_is_reassigned_in_one_sync(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.sync()
    item = _item(mirror)
    _assign(mirror, NODE_UIDS[0], item)
    mirror.sync()
    _with_links(mirror, "NODE-001", "A")
    _with_links(mirror, "NODE-002", "B", items=[item["label"]])

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert _item_node(mirror, item)["node_uid"] == NODE_UIDS[1]


def test_an_item_at_two_nodes_in_the_files_is_refused_naming_both_files(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.sync()
    item = _item(mirror)
    _with_links(mirror, "NODE-001", "A", items=[item["label"]])
    _with_links(mirror, "NODE-002", "B", items=[item["label"]])

    result = mirror.sync()

    assert result.status_code == 422, result.text
    body = result.json()
    assert body["code"] == "rule_violation"
    assert "NODE-001.md" in body["message"] + str(body["details"]) and "NODE-002.md" in body["message"] + str(
        body["details"]
    )
    assert _item_node(mirror, item)["node_uid"] is None


def test_an_unknown_item_or_memo_is_refused_with_file_and_line(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.sync()
    _with_links(mirror, "NODE-001", "A", items=["TASK-099"])

    first = mirror.sync()

    assert first.status_code == 422, first.text
    assert first.json()["code"] == "unknown_reference" and "TASK-099" in first.json()["message"]
    assert "NODE-001.md" in str(first.json()) and ":" in str(first.json()["details"])
    _with_links(mirror, "NODE-001", "A", memos=["MEMO-099"])
    assert mirror.sync().json()["code"] == "unknown_reference"
    _with_links(mirror, "NODE-001", "A", items=["Nirgendwo:TASK-001"])
    assert mirror.sync().json()["code"] == "unknown_reference"


def test_an_item_of_another_project_is_known_but_not_assignable(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.sync()
    other = _other_project(mirror)
    foreign = _item(mirror, project=other)
    _with_links(mirror, "NODE-001", "A", items=[f"{ELSE}:{foreign['label']}"])

    result = mirror.sync()

    assert result.status_code == 422, result.text
    assert result.json()["code"] == "rule_violation" and "NODE-001.md" in str(result.json())
    assert _item_node(mirror, foreign)["node_uid"] is None


def test_new_nodes_from_the_files_bring_their_assignments(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    item, memo = _item(mirror), _memo(mirror)
    mirror.write("mindmap/new-wurzel.md", node_file(None, None, "Neue Wurzel"))
    mirror.write("mindmap/project.md", project_file("- new-wurzel\n"))
    mirror.sync()
    node = mirror.nodes()["Neue Wurzel"]
    _with_links(mirror, "NODE-001", "Neue Wurzel", items=[item["label"]], memos=[memo["label"]])
    mirror.write("mindmap/new-kind.md", node_file(None, None, "Kind"))
    mirror.write("mindmap/project.md", project_file("- NODE-001\n  - new-kind\n"))

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert _item_node(mirror, item)["node_uid"] == node["uid"]
    assert _memo_nodes(mirror, memo) == [node["uid"]]


def test_both_sides_changing_the_assignments_of_a_node_is_a_conflict(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.sync()
    first, second = _item(mirror), _item(mirror)
    _assign(mirror, NODE_UIDS[0], first)
    _with_links(mirror, "NODE-001", "A", items=[second["label"]])

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert [c["conflict"] for c in result.json()["conflicts_left"]] == ["both_changed"]
    assert _item_node(mirror, first)["node_uid"] == NODE_UIDS[0]
    assert _item_node(mirror, second)["node_uid"] is None


# --- Dokumente -------------------------------------------------------------------------------------------------------


def test_a_document_deleted_in_the_files_is_a_conflict_and_goes_only_on_decision(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.write("mindmap/NODE-001_notes.md", "# NODE-001 — Notizen\n")
    mirror.sync()
    (mirror.folder / "mindmap/NODE-001_notes.md").unlink()

    kept = mirror.sync()

    assert kept.status_code == 200, kept.text
    assert [c["conflict"] for c in kept.json()["conflicts_left"]] == ["deleted_in_files"]
    documents = f"{API}/nodes/NODE-001/documents"
    assert [d["name"] for d in mindmap.client.get(documents, params={"project": mirror.project}).json()] == [
        "NODE-001_notes.md"
    ]
    conflict = kept.json()["conflicts_left"][0]["key"]

    done = mirror.sync(decisions=[{"uid": conflict, "choice": "files"}], delete_missing=True)

    assert done.status_code == 200, done.text
    assert mindmap.client.get(documents, params={"project": mirror.project}).json() == []
    assert mirror.status()["state"] == "in_sync"


def test_purging_a_node_from_the_trash_removes_its_files_and_documents(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.write("mindmap/NODE-004_notes.md", "# NODE-004 — Notizen\n")
    mirror.sync()
    node = mirror.nodes()["D"]
    assert mindmap.client.delete(f"{API}/nodes/{node['uid']}", params={"version": node["version"]}).status_code == 200
    mirror.sync()
    purged = mindmap.client.post("/api/workspace/trash/purge", json={"uids": [node["uid"]]})
    assert purged.status_code == 200, purged.text

    assert not (mirror.folder / "mindmap/NODE-004.md").exists()
    assert not (mirror.folder / "mindmap/NODE-004_notes.md").exists()
    assert mirror.sync().json()["conflicts_left"] == []
    assert mirror.status()["state"] == "in_sync"


def test_a_changed_document_is_not_removed_when_its_node_is_purged(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.write("mindmap/NODE-004_notes.md", "# NODE-004 — Notizen\n")
    mirror.sync()
    node = mirror.nodes()["D"]
    mindmap.client.delete(f"{API}/nodes/{node['uid']}", params={"version": node["version"]})
    mirror.sync()
    mirror.write("mindmap/NODE-004_notes.md", "# NODE-004 — Notizen\n\nVon Hand geändert.\n")
    mindmap.client.post("/api/workspace/trash/purge", json={"uids": [node["uid"]]})

    assert (mirror.folder / "mindmap/NODE-004_notes.md").exists()


# --- Entfernte Platzierungen -----------------------------------------------------------------------------------------


def _remove(mirror: Mirror, node: str, tree: str | None) -> None:
    current = mirror.env.client.get(f"{API}/nodes/{node}").json()
    response = mirror.env.client.post(f"{API}/nodes/{node}/remove", json={"version": current["version"], "tree": tree})
    assert response.status_code == 200, response.text


def test_removed_placements_are_written_as_removed_rows(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.write("mindmap/maps/ideen.md", map_file("Ideen", "- NODE-001\n  - NODE-002\n  - NODE-003\n- NODE-004\n"))
    mirror.sync()
    _remove(mirror, NODE_UIDS[0], MAP_UID)  # NODE-001 mit Kindern aus der Map

    result = mirror.sync()

    assert result.status_code == 200, result.text
    text = mirror.text("mindmap/maps/ideen.md")
    assert "\n- NODE-004\n\nRemoved:\n" in text
    rows = text.rpartition("Removed:\n")[2].strip().split("\n")
    assert sorted(r.split(" ")[1] for r in rows) == ["NODE-001", "NODE-002", "NODE-003"]
    assert all(r.endswith("group NODE-001") for r in rows)
    assert mirror.status()["state"] == "in_sync"


def test_removed_rows_in_the_files_reach_the_database_and_a_branch_can_be_restored(
    mindmap: Env, tmp_path: Path
) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.write("mindmap/maps/ideen.md", map_file("Ideen", "- NODE-001\n  - NODE-002\n  - NODE-003\n- NODE-004\n"))
    mirror.sync()
    mirror.write(
        "mindmap/maps/ideen.md",
        map_file(
            "Ideen",
            "- NODE-004\n\nRemoved:\n- NODE-001 parent - position 0 group NODE-001\n"
            "- NODE-002 parent NODE-001 position 0 group NODE-001\n"
            "- NODE-003 parent NODE-001 position 1 group NODE-001\n",
        ),
    )

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert mirror.tree(MAP_UID) == [("D", None)]
    removed = mindmap.client.get(f"{API}/nodes/{NODE_UIDS[0]}/removed", params={"project": mirror.project}).json()
    assert [r["tree_uid"] for r in removed] == [MAP_UID]
    node = mirror.nodes()["A"]
    restored = mindmap.client.post(
        f"{API}/nodes/{NODE_UIDS[0]}/restore-placement", json={"version": node["version"], "tree": MAP_UID}
    )
    assert restored.status_code == 200, restored.text
    assert mirror.tree(MAP_UID) == [("A", None), ("D", None), ("B", "A"), ("C", "A")]


def test_a_removed_row_that_disappears_from_the_files_is_forgotten(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.write("mindmap/maps/ideen.md", map_file("Ideen", "- NODE-001\n  - NODE-002\n  - NODE-003\n- NODE-004\n"))
    mirror.sync()
    _remove(mirror, NODE_UIDS[1], MAP_UID)
    mirror.sync()
    text = mirror.text("mindmap/maps/ideen.md").partition("\nRemoved:")[0]
    mirror.write("mindmap/maps/ideen.md", text)

    result = mirror.sync()

    assert result.status_code == 200, result.text
    removed = mindmap.client.get(f"{API}/nodes/{NODE_UIDS[1]}/removed", params={"project": mirror.project}).json()
    assert removed == []
    assert mirror.status()["state"] == "in_sync"


def test_a_child_left_under_a_removed_parent_is_refused(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.write("mindmap/maps/ideen.md", map_file("Ideen", "- NODE-001\n  - NODE-002\n- NODE-004\n"))
    mirror.sync()
    mirror.write(
        "mindmap/maps/ideen.md",
        map_file("Ideen", "- NODE-004\n\nRemoved:\n- NODE-001 parent - position 0 group NODE-001\n"),
    )

    result = mirror.sync()

    assert result.status_code == 422, result.text
    assert result.json()["code"] == "rule_violation" and "ideen.md" in str(result.json())
    assert mirror.tree(MAP_UID) == [("A", None), ("D", None), ("B", "A")]


# --- Papierkorb der Maps ---------------------------------------------------------------------------------------------


def test_a_deleted_map_is_written_with_its_deletion_and_its_nodes(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    ideas = mirror.new_map("Ideen")
    node = mirror.node("Idee", tree=ideas)
    maps = mindmap.client.get(f"{API}/maps/{mirror.project}").json()
    version = next(m["version"] for m in maps if m["tree_uid"] == ideas)
    assert mindmap.client.delete(f"{API}/maps/{ideas}", params={"version": version}).status_code == 200

    result = mirror.sync()

    assert result.status_code == 200, result.text
    text = mirror.text("mindmap/maps/ideen.md")
    assert "Deleted: 20" in text and text.endswith("- NODE-001\n")
    assert "Deleted: 20" in mirror.text("mindmap/NODE-001.md")
    assert node["uid"] in mirror.text("mindmap/NODE-001.md")
    assert mirror.status()["state"] == "in_sync"


def test_a_map_in_the_trash_in_the_files_goes_to_the_trash_not_to_deletion(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.sync()
    text = mirror.text("mindmap/maps/ideen.md").replace("Deleted:\n", "Deleted: 2026-11-10T08:00:00Z\n")
    mirror.write("mindmap/maps/ideen.md", text)

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert [m["name"] for m in mirror.maps() if m["kind"] == "free"] == []
    listed = mindmap.client.get("/api/workspace/trash").json()
    assert any(e["kind"] == "mindmap_map" for e in listed)
    assert mirror.nodes()["C"]["uid"] == NODE_UIDS[2]  # C steht auch im Projektbaum
    assert mirror.status()["state"] == "in_sync"


def test_a_map_restored_in_the_files_comes_back_with_the_nodes_that_went_with_it(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    ideas = mirror.new_map("Ideen")
    mirror.node("Idee", tree=ideas)
    _delete_map(mirror, ideas)
    mirror.sync()
    for path in ("mindmap/maps/ideen.md", "mindmap/NODE-001.md"):
        mirror.write(path, re.sub(r"^Deleted: \S+$", "Deleted:", mirror.text(path), flags=re.MULTILINE))

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert [m["name"] for m in mirror.maps() if m["kind"] == "free"] == ["Ideen"]
    assert mirror.tree(ideas) == [("Idee", None)]
    assert mirror.status()["state"] == "in_sync"


# --- Rundlauf --------------------------------------------------------------------------------------------------------


def _delete_map(mirror: Mirror, tree: str) -> None:
    version = next(m["version"] for m in mirror.maps() if m["tree_uid"] == tree)
    response = mirror.env.client.delete(f"{API}/maps/{tree}", params={"version": version})
    assert response.status_code == 200, response.text


def _view(mirror: Mirror) -> dict[str, Any]:
    """Alles, was die Mindmap eines Projekts ausmacht, ohne Uids der Items und Memos (sie sind je Datenbank anders)."""
    client = mirror.env.client
    maps = mirror.maps()
    trees = {m["name"]: mirror.tree(m["tree_uid"]) for m in maps if m["tree_uid"]}
    nodes: dict[str, Any] = {}
    for node in {
        n["label"]: n
        for tree in [None, *[m["tree_uid"] for m in maps if m["kind"] == "free"]]
        for n in client.get(f"{API}/trees/{mirror.project}", params={"tree": tree} if tree else {}).json()["nodes"]
    }.values():
        documents = client.get(f"{API}/nodes/{node['label']}/documents", params={"project": mirror.project}).json()
        removed = client.get(f"{API}/nodes/{node['label']}/removed", params={"project": mirror.project}).json()
        nodes[node["label"]] = {
            "title": node["title"],
            "text": node["text"],
            "mark": node["mark"],
            "documents": [d["name"] for d in documents],
            "removed": sorted((r["name"], r["nodes"], r["parent_available"]) for r in removed),
        }
    trash = sorted(
        e["title"] for e in client.get("/api/workspace/trash").json() if e["kind"] in ("mindmap_map", "mindmap_node")
    )
    return {"trees": trees, "nodes": nodes, "trash": trash}


def _assignments(mirror: Mirror, items: list[dict[str, Any]], memos: list[dict[str, Any]]) -> dict[str, Any]:
    labels = {n["uid"]: n["label"] for n in mirror.env.client.get(f"{API}/trees/{mirror.project}").json()["nodes"]}
    return {
        **{i["label"]: labels.get(_item_node(mirror, i)["node_uid"]) for i in items},
        **{m["label"]: sorted(labels.get(u, u) for u in _memo_nodes(mirror, m)) for m in memos},
    }


def test_a_full_round_trip_gives_the_same_mindmap(mindmap: Env, tmp_path: Path, settings: Settings) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.write("mindmap/maps/ideen.md", map_file("Ideen", "- NODE-001\n  - NODE-002\n  - NODE-003\n- NODE-004\n"))
    mirror.write("mindmap/NODE-001_notes.md", "# NODE-001 — Notizen\n\nText.\n")
    mirror.sync()
    item, memo = _item(mirror), _memo(mirror)
    _assign(mirror, NODE_UIDS[0], item)
    _link(mirror, NODE_UIDS[0], memo)
    _link(mirror, NODE_UIDS[3], memo)
    _remove(mirror, NODE_UIDS[3], MAP_UID)
    other = mirror.new_map("Zweite")
    mirror.node("Idee", tree=other)
    _delete_map(mirror, other)
    assert mirror.sync().status_code == 200
    expected = (_view(mirror), _assignments(mirror, [item], [memo]))

    fresh_folder = tmp_path / "fresh-env"
    fresh_folder.mkdir()
    fresh_settings = replace(
        settings,
        db_path=str(fresh_folder / "viewer.db"),
        backup_dir=str(fresh_folder / "b"),
        log_dir=str(fresh_folder / "l"),
    )
    environment = mindmap_env(fresh_folder, fresh_settings)
    with environment.client:
        _round_trip_into(environment, fresh_folder, mirror, item, memo, expected)


def _round_trip_into(
    environment: Env, fresh_folder: Path, mirror: Mirror, item: dict[str, Any], memo: dict[str, Any], expected: Any
) -> None:
    fresh = Mirror(environment, fresh_folder)
    for source in sorted((mirror.folder / "mindmap").rglob("*.md")):
        fresh.write(str(source.relative_to(mirror.folder)), source.read_text(encoding="utf-8"))
    fresh_item, fresh_memo = _item(fresh), _memo(fresh)
    assert (fresh_item["label"], fresh_memo["label"]) == (item["label"], memo["label"])

    imported = fresh.sync()

    assert imported.status_code == 200, imported.text
    assert (_view(fresh), _assignments(fresh, [fresh_item], [fresh_memo])) == expected
    again = fresh.sync()
    assert (again.json()["to_database"], again.json()["to_files"]) == (0, 0)
    assert {p: fresh.text(p) for p in _files(fresh)} == {p: mirror.text(p) for p in _files(mirror)}


def _files(mirror: Mirror) -> list[str]:
    return sorted(str(p.relative_to(mirror.folder)) for p in (mirror.folder / "mindmap").rglob("*.md"))

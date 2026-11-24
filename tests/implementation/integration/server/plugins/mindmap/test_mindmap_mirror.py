"""Die Mindmap im Spiegel (Knoten und Bäume): Sync-Dienst mit echter SQLite-Datei, echtem Ordner und echtem Codec."""

from __future__ import annotations

from pathlib import Path

from mindmap_mirror_env import (
    API,
    BASE,
    MAP_UID,
    NODE_UIDS,
    Mirror,
    example_files,
    map_file,
    node_file,
    project_file,
)
from workspace_env import Env


def test_nodes_and_trees_of_the_database_are_written_as_files(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    top = mirror.node("Ast", text="Ein Text")
    mirror.node("Kind", parent=top["uid"])
    mirror.node("Zweiter Ast")
    ideas = mirror.new_map("Ideen")
    mirror.node("Idee", tree=ideas)

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert mirror.text("mindmap/NODE-001.md").endswith("Title: Ast\nMark:\nDeleted:\n\nEin Text\n")
    assert mirror.text("mindmap/NODE-001.md").startswith(f"# NODE-001\nUid: {top['uid']}\n")
    assert mirror.text("mindmap/project.md").endswith("Kind: project\n\n- NODE-001\n  - NODE-002\n- NODE-003\n")
    assert "Name: Ideen\n" in mirror.text("mindmap/maps/ideen.md")
    assert mirror.text("mindmap/maps/ideen.md").endswith("\n- NODE-004\n")
    assert mirror.status()["state"] == "in_sync"


def test_files_with_uids_are_imported_into_the_database(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert mirror.tree() == [("A", None), ("D", None), ("B", "A"), ("C", "A")]
    assert mirror.nodes()["A"]["uid"] == NODE_UIDS[0] and mirror.nodes()["A"]["label"] == "NODE-001"
    maps = [m for m in mirror.maps() if m["kind"] == "free"]
    assert [(m["name"], m["tree_uid"]) for m in maps] == [("Ideen", MAP_UID)]
    assert mirror.tree(MAP_UID) == [("C", None)]
    assert mirror.status()["state"] == "in_sync"


def test_a_second_sync_without_changes_leaves_both_sides_alone(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.sync()
    before = {p: mirror.text(p) for p in ("mindmap/project.md", "mindmap/NODE-001.md", "mindmap/maps/ideen.md")}

    result = mirror.sync()

    assert result.status_code == 200 and (result.json()["to_database"], result.json()["to_files"]) == (0, 0)
    assert before == {p: mirror.text(p) for p in before}
    assert mirror.status()["state"] == "in_sync"


def test_mark_text_and_trash_state_of_a_node_are_carried(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.sync()
    mirror.write("mindmap/NODE-004.md", node_file("NODE-004", NODE_UIDS[3], "D neu", "Neuer Text", "later"))
    mirror.write("mindmap/NODE-002.md", node_file("NODE-002", NODE_UIDS[1], "B", deleted="2026-11-10T08:00:00Z"))

    result = mirror.sync()

    assert result.status_code == 200, result.text
    nodes = mirror.nodes()
    assert nodes["D neu"]["mark"] == "later" and nodes["D neu"]["text"] == "Neuer Text"
    assert "B" not in nodes  # liegt im Papierkorb
    assert mirror.status()["state"] == "in_sync"


def test_new_nodes_and_new_maps_from_the_files_get_uid_and_label_and_references_follow(
    mindmap: Env, tmp_path: Path
) -> None:
    mirror = Mirror(mindmap, tmp_path)
    mirror.write("mindmap/new-wurzel.md", node_file(None, None, "Neue Wurzel", "Aus der Cloud"))
    mirror.write("mindmap/new-kind.md", node_file(None, None, "Neues Kind"))
    mirror.write("mindmap/project.md", project_file("- new-wurzel\n  - new-kind\n"))
    mirror.write("mindmap/maps/new-entwurf.md", map_file("Entwurf", "- new-kind\n", uid=None))

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert sorted(result.json()["created"]) == ["NODE-001", "NODE-002", "new-entwurf"]
    assert mirror.tree() == [("Neue Wurzel", None), ("Neues Kind", "Neue Wurzel")]
    maps = [m for m in mirror.maps() if m["kind"] == "free"]
    assert [m["name"] for m in maps] == ["Entwurf"]
    assert mirror.tree(maps[0]["tree_uid"]) == [("Neues Kind", None)]
    assert not (mirror.folder / "mindmap/new-wurzel.md").exists()
    assert mirror.text("mindmap/project.md").endswith("Kind: project\n\n- NODE-002\n  - NODE-001\n")
    assert "Uid: " in mirror.text("mindmap/NODE-001.md") and "Title: Neues Kind\n" in mirror.text("mindmap/NODE-001.md")
    assert "- NODE-001\n" in mirror.text("mindmap/maps/entwurf.md")
    assert (mirror.folder / "mindmap/maps/entwurf.md").exists() and "Uid: " in mirror.text("mindmap/maps/entwurf.md")
    assert mirror.status()["state"] == "in_sync"


def test_a_moved_branch_in_the_files_changes_the_placements_without_copying(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.sync()
    before = {title: node["uid"] for title, node in mirror.nodes().items()}
    # A (B, C), D  →  D (A (B, C))
    mirror.write("mindmap/project.md", project_file("- NODE-004\n  - NODE-001\n    - NODE-003\n    - NODE-002\n"))

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert mirror.tree() == [("D", None), ("A", "D"), ("C", "A"), ("B", "A")]
    assert {title: node["uid"] for title, node in mirror.nodes().items()} == before
    assert mirror.status()["state"] == "in_sync"


def test_a_branch_transferred_in_the_files_stands_in_both_trees_with_the_same_nodes(
    mindmap: Env, tmp_path: Path
) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.sync()
    mirror.write("mindmap/maps/ideen.md", map_file("Ideen", "- NODE-001\n  - NODE-002\n  - NODE-003\n"))

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert mirror.tree(MAP_UID) == [("A", None), ("B", "A"), ("C", "A")]
    assert mirror.tree()[:2] == [("A", None), ("D", None)]  # der Projektbaum bleibt
    shared = mirror.nodes(MAP_UID)
    assert shared["A"]["uid"] == NODE_UIDS[0] and shared["A"]["tree_count"] == 2


def test_a_move_in_the_database_is_written_to_the_tree_file(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.sync()
    node = mirror.nodes()["B"]
    moved = mindmap.client.post(
        f"{API}/nodes/{node['uid']}/move", json={"version": node["version"], "parent": NODE_UIDS[3], "tree": None}
    )
    assert moved.status_code == 200, moved.text

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert mirror.text("mindmap/project.md").endswith("\n- NODE-001\n  - NODE-003\n- NODE-004\n  - NODE-002\n")


def test_both_sides_changing_a_node_or_a_tree_is_a_conflict(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.sync()
    node = mirror.nodes()["A"]
    mindmap.client.put(f"{API}/nodes/{node['uid']}", json={"version": node["version"], "title": "A Datenbank"})
    mirror.write("mindmap/NODE-001.md", node_file("NODE-001", NODE_UIDS[0], "A Datei", "Text A"))
    d = mirror.nodes()["D"]
    mindmap.client.post(
        f"{API}/nodes/{d['uid']}/move", json={"version": d["version"], "parent": NODE_UIDS[1], "tree": None}
    )
    mirror.write("mindmap/project.md", project_file("- NODE-004\n  - NODE-001\n    - NODE-002\n    - NODE-003\n"))

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert sorted(c["conflict"] for c in result.json()["conflicts_left"]) == ["both_changed", "both_changed"]
    assert "A Datenbank" in mirror.nodes() and ("D", "B") in mirror.tree()  # nichts überschrieben
    assert mirror.status()["state"] == "conflicts"


def test_a_tree_listing_an_unknown_node_is_refused_with_file_and_line_and_changes_nothing(
    mindmap: Env, tmp_path: Path
) -> None:
    mirror = Mirror(mindmap, tmp_path)
    example_files(mirror)
    mirror.sync()
    mirror.write("mindmap/maps/ideen.md", map_file("Ideen", "- NODE-003\n- NODE-099\n"))

    result = mirror.sync()

    assert result.status_code == 422, result.text
    assert result.json()["code"] == "unknown_reference" and "NODE-099" in result.json()["message"]
    assert mirror.tree(MAP_UID) == [("C", None)]


def test_items_and_documents_assigned_in_the_database_survive_a_sync(mindmap: Env, tmp_path: Path) -> None:
    mirror = Mirror(mindmap, tmp_path)
    node = mirror.node("Ast")
    item = mindmap.client.post(
        "/api/backlog/items", json={"project": mirror.project, "type": "Task", "fields": BASE}
    ).json()
    assigned = mindmap.client.post(f"{API}/nodes/{node['uid']}/items", json={"item": item["uid"]})
    assert assigned.status_code == 200, assigned.text
    mirror.sync()
    mirror.write("mindmap/NODE-001.md", mirror.text("mindmap/NODE-001.md").replace("Title: Ast", "Title: Ast neu"))

    result = mirror.sync()

    assert result.status_code == 200, result.text
    shown = mindmap.client.get(f"{API}/items/{item['uid']}/node")
    assert shown.status_code == 200 and shown.json()["node_uid"] == node["uid"]


def test_documents_of_a_new_node_follow_its_label_and_changed_documents_reach_the_database(
    mindmap: Env, tmp_path: Path
) -> None:
    mirror = Mirror(mindmap, tmp_path)
    mirror.write("mindmap/new-wurzel.md", node_file(None, None, "Neue Wurzel"))
    mirror.write("mindmap/new-wurzel_notes.md", "# NODE — Notizen\n")
    mirror.write("mindmap/project.md", project_file("- new-wurzel\n"))

    first = mirror.sync()

    assert first.status_code == 200, first.text
    assert (mirror.folder / "mindmap/NODE-001_notes.md").exists()
    assert not (mirror.folder / "mindmap/new-wurzel_notes.md").exists()
    documents = mindmap.client.get(f"{API}/nodes/NODE-001/documents", params={"project": mirror.project}).json()
    assert [d["name"] for d in documents] == ["NODE-001_notes.md"]
    mirror.write("mindmap/NODE-001_notes.md", "# NODE-001 — Notizen\n\nNeu.\n")

    second = mirror.sync()

    assert second.status_code == 200, second.text
    shown = mindmap.client.get(
        f"{API}/nodes/NODE-001/documents/NODE-001_notes.md", params={"project": mirror.project}
    ).json()
    assert shown["content"].endswith("Neu.\n")
    assert mirror.status()["state"] == "in_sync"

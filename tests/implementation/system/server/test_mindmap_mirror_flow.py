"""Eine Cloud-Sitzung arbeitet nur mit den Dateien der Mindmap, der Viewer übernimmt sie (TASK-082, STORY-105).

Der Ablauf bildet nach, was eine Sitzung im Datei-Modus tut: den Spiegel-Ordner lesen, Textdateien bearbeiten, danach
läuft ein Sync. Als Maßstab dienen die gleichen Schritte über MCP (wie die API sie ausführt) in einem zweiten Projekt:
beide Projekte müssen am Ende dieselbe Mindmap zeigen. Format: `docs/techdocs/interfaces.md`, „Mindmap-Dateien“.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

import httpx
from mcp import Client
from mcp_viewer import Harness, running_viewer
from running_server import RunningServer

ITEM = {"title": "Ansicht bauen", "goal": "Anzeigen", "completion_criteria": "Tests grün"}


async def _sync(h: Harness, project: str, **decisions: Any) -> dict[str, Any]:
    preview = await h.call("core_sync_preview", project=project)
    result: dict[str, Any] = await h.call("core_sync_execute", project=project, token=preview["token"], **decisions)
    return result


async def _node(h: Harness, project: str, ref: str, tree: str | None = None) -> dict[str, Any]:
    node: dict[str, Any] = await h.call(
        "mindmap_get_node", ref=ref, project=project, **({"tree": tree} if tree else {})
    )
    return node


async def _start(h: Harness, base_url: str, name: str, folder: Path | None) -> dict[str, Any]:
    """Das Ausgangsprojekt: Projektbaum A (B, C (E)), D; freie Maps „Ideen“ (leer) und „Archiv“ (leer); ein Item."""
    fields: dict[str, Any] = {"name": name}
    if folder is not None:
        folder.mkdir()
        fields |= {"mirror_folder": str(folder), "mirror_enabled": True}
    # Projekte anlegen ist kein MCP-Tool (Einstellung des Owners): über HTTP, wie es die Oberfläche tut
    created = httpx.post(f"{base_url}/api/workspace/projects", json=fields)
    assert created.status_code == 200, created.text
    project = created.json()["uid"]
    nodes: dict[str, Any] = {}
    for title, parent in [("A", None), ("B", "A"), ("C", "A"), ("D", None), ("E", "C")]:
        parent_uid = nodes[parent]["uid"] if parent else None
        nodes[title] = await h.call("mindmap_create_node", project=project, title=title, parent=parent_uid)
    maps = {n: (await h.call("mindmap_create_map", project=project, name=n))["tree_uid"] for n in ("Ideen", "Archiv")}
    item = await h.call("backlog_create_item", project=project, type="Task", fields=ITEM)
    return {"project": project, "nodes": nodes, "maps": maps, "item": item["label"]}


async def _view(h: Harness, project: str, item: str) -> dict[str, Any]:
    """Alles, was der Owner sieht: je Baum Titel mit Parent in Reihenfolge, je Knoten Items und Anzahl der Bäume."""
    trees: dict[str, Any] = {}
    for tree in await h.call("mindmap_list_maps", project=project):
        listing = await h.call(
            "mindmap_get_tree", project=project, **({"tree": tree["tree_uid"]} if tree["tree_uid"] else {})
        )
        titles = {n["uid"]: n["title"] for n in listing["nodes"]}
        trees["Projekt" if tree["kind"] == "project" else tree["name"]] = [
            (n["title"], titles.get(n["parent_uid"]), n["tree_count"]) for n in listing["nodes"]
        ]
    assigned = await h.call("mindmap_get_item_node", item=item, project=project)
    holder = await _node(h, project, assigned["node_uid"]) if assigned["node_uid"] else None
    return {"trees": trees, "item_at": holder["title"] if holder else None}


# --- dieselben Schritte über die API (MCP) ---------------------------------------------------------------------


async def _by_api(h: Harness, start: dict[str, Any]) -> None:
    project, maps = start["project"], start["maps"]
    await h.call("mindmap_create_node", project=project, title="Skizze", tree=maps["Ideen"])
    b = await _node(h, project, start["nodes"]["B"]["uid"])
    d = await _node(h, project, start["nodes"]["D"]["uid"])
    await h.call(
        "mindmap_move_node", ref=b["uid"], version=b["version"], parent=d["uid"], tree=await _project_tree(h, project)
    )
    c = await _node(h, project, start["nodes"]["C"]["uid"])
    await h.call(
        "mindmap_transfer_node_to_map", ref=c["uid"], version=c["version"], target=maps["Archiv"], project=project
    )
    await h.call("mindmap_assign_item", node=d["uid"], item=start["item"], project=project)


async def _project_tree(h: Harness, project: str) -> str:
    maps = await h.call("mindmap_list_maps", project=project)
    return str(next(m for m in maps if m["kind"] == "project")["tree_uid"])


# --- die Schritte einer Cloud-Sitzung in den Dateien -------------------------------------------------------------


def _label_of(folder: Path, title: str) -> str:
    """Das Label des Knotens mit diesem Titel: die Sitzung liest es in den Knotendateien nach."""
    for path in sorted((folder / "mindmap").glob("NODE-???.md")):
        if re.search(rf"^Title: {re.escape(title)}$", path.read_text(encoding="utf-8"), re.MULTILINE):
            return path.stem
    raise AssertionError(f"kein Knoten {title!r} in den Dateien")


def _edit(path: Path, change: Any) -> None:
    path.write_text(change(path.read_text(encoding="utf-8")), encoding="utf-8")


def _append_listing(text: str, lines: str) -> str:
    """Zeilen an die Liste einer Baumdatei hängen; eine leere Map hat nach dem Kopf noch keine Leerzeile."""
    head, _, rest = text.partition("\n\n")
    return f"{head}\n\n{rest}{lines}" if rest or "\n\n" in text else f"{text.rstrip(chr(10))}\n\n{lines}"


def _by_files(folder: Path, item: str) -> None:
    mindmap = folder / "mindmap"
    label = {title: _label_of(folder, title) for title in "ABCDE"}

    # 1. freie Map füllen: neuer Knoten mit Platzhalter, in der Baumdatei der Map genannt
    (mindmap / "new-skizze.md").write_text("# NEW\nTitle: Skizze\nMark:\nDeleted:\n", encoding="utf-8")
    _edit(mindmap / "maps" / "ideen.md", lambda text: _append_listing(text, "- new-skizze\n"))

    # 2. einen Ast umhängen: die Zeile von B im Projektbaum unter D schreiben (verschieben, nicht kopieren)
    def hang(text: str) -> str:
        text = text.replace(f"  - {label['B']}\n", "", 1)
        return text.replace(f"- {label['D']}\n", f"- {label['D']}\n  - {label['B']}\n", 1)

    _edit(mindmap / "project.md", hang)

    # 3. einen Ast in die Baumdatei einer anderen Map übertragen: Verweise auf C und E statt Kopien der Knoten
    _edit(mindmap / "maps" / "archiv.md", lambda text: _append_listing(text, f"- {label['C']}\n  - {label['E']}\n"))

    # 4. ein Item einem Knoten zuordnen: in `Items:` des Knotens eintragen
    _edit(mindmap / f"{label['D']}.md", lambda text: text.replace("Deleted:\n", f"Deleted:\nItems:\n- {item}\n", 1))


# --- die Szenarien -------------------------------------------------------------------------------------------------


async def _session(viewer: RunningServer, tmp_path: Path) -> None:
    async with Client(viewer.base_url + "/mcp") as client:
        h = Harness(client)
        cloud = await _start(h, viewer.base_url, "Cloud", tmp_path / "mirror")
        reference = await _start(h, viewer.base_url, "Referenz", None)
        folder = tmp_path / "mirror"

        # die Ausgangslage kommt in die Dateien: Knoten, Projektbaum, beide Maps
        first = await _sync(h, cloud["project"])
        assert first["conflicts_left"] == []
        names = sorted(p.name for p in (folder / "mindmap").rglob("*.md"))
        assert names == [
            "NODE-001.md",
            "NODE-002.md",
            "NODE-003.md",
            "NODE-004.md",
            "NODE-005.md",
            "archiv.md",
            "ideen.md",
            "project.md",
        ]
        assert await _view(h, cloud["project"], cloud["item"]) == await _view(
            h, reference["project"], reference["item"]
        )

        # die Cloud-Sitzung bearbeitet nur Dateien; die Referenz geht über die API
        _by_files(folder, cloud["item"])
        await _by_api(h, reference)
        done = await _sync(h, cloud["project"])
        assert done["conflicts_left"] == [] and len(done["created"]) == 1  # NODE-006 für den Platzhalter

        cloud_view = await _view(h, cloud["project"], cloud["item"])
        assert cloud_view == await _view(h, reference["project"], reference["item"])
        assert cloud_view["trees"]["Ideen"] == [("Skizze", None, 1)]
        # C und E stehen jetzt in zwei Bäumen (Verweis statt Kopie), B hängt unter D
        assert cloud_view["trees"]["Projekt"] == [
            ("A", None, 1),
            ("D", None, 1),
            ("C", "A", 2),
            ("B", "D", 1),
            ("E", "C", 2),
        ]
        assert cloud_view["trees"]["Archiv"] == [("C", None, 2), ("E", "C", 2)]
        assert cloud_view["item_at"] == "D"
        assert (folder / "mindmap" / "NODE-006.md").exists() and not (folder / "mindmap" / "new-skizze.md").exists()

        # derselbe Knoten auf beiden Seiten geändert: Konflikt, nichts wird überschrieben
        a = await _node(h, cloud["project"], cloud["nodes"]["A"]["uid"])
        await h.call(
            "mindmap_update_node",
            ref=a["uid"],
            version=a["version"],
            title="A in der Datenbank",
            project=cloud["project"],
        )
        _edit(folder / "mindmap" / "NODE-001.md", lambda text: text.replace("Title: A", "Title: A in der Datei", 1))
        preview = await h.call("core_sync_preview", project=cloud["project"])
        assert [(c["kind"], c["label"], c["conflict"]) for c in preview["conflicts"]] == [
            ("mindmap.node", "NODE-001", "both_changed")
        ]
        left = await _sync(h, cloud["project"])
        assert [c["label"] for c in left["conflicts_left"]] == ["NODE-001"]
        assert (await _node(h, cloud["project"], "NODE-001"))["title"] == "A in der Datenbank"
        assert "Title: A in der Datei" in (folder / "mindmap" / "NODE-001.md").read_text(encoding="utf-8")


def test_a_cloud_session_that_only_edits_files_gets_the_same_mindmap_as_the_api(tmp_path: Path) -> None:
    with running_viewer(tmp_path) as viewer:
        asyncio.run(_session(viewer, tmp_path))

#!/usr/bin/env python3
"""Legt den vorgeschlagenen Themenbaum für die aktiven Items an (einmalig, über die HTTP-API).

Aufruf:  python3 mindmap_seed.py [--project todo_viewer] [--url http://localhost:5411] [--apply]
Ohne --apply wird nur angezeigt, was passieren würde. Bereits vorhandene Knoten
(gleicher Titel unter gleichem Parent) werden wiederverwendet, nicht doppelt angelegt.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

# (Titel, Text, [Unterknoten], [Item-Uids, die dem Knoten eigens zugeordnet werden])
TREE = [
    ("Mindmap", "Der Themenbaum selbst: Darstellung, Bedienung, Ideen ins Backlog.", [
        ("Mehrere Maps und Äste", "Freie Maps, Äste umhängen/übertragen, entfernte Platzierungen, Papierkorb.", [],
         ["5e2233a4-bac0-482b-8890-66e0855fa8e0"]),  # STORY-102 (+ TASK-062, -063, -066, Papierkorb-Ansicht erben)
        ("Von der Idee zum Item", "Aus einem Ideen-Knoten direkt ein Backlog-Item machen.", [],
         ["688f456a-295f-453d-a6cd-39d7bb6c6aa8"]),  # STORY-103
        ("Themen statt Area", "Die Mindmap ersetzt das Feld Area als Einordnung.", [],
         ["2583a192-6eb8-481d-8637-86eb8408fa9a"]),  # STORY-106
    ], ["039478f4-0b3b-4807-8fd3-36fec9a4d372"]),  # EPIC-008
    ("Backlog-Baum", "Bedienung der Baumansicht des Backlogs.", [
        ("Ziehen und Umwandeln", "Beim Ziehen an eine unpassende Stelle den Typ umwandeln.", [],
         ["9ccc4f8d-f897-4fdd-bc8d-a67da5569d3f"]),  # STORY-086
    ], []),
    ("KI-Schnittstelle", "Was Agenten über MCP und API können und wie fehlerarm das ist.", [
        ("MCP für Agenten", "Projektbindung, Labels statt uids, typisierte Felder.", [],
         ["203401d1-c591-4737-9d56-60aea47a3fec"]),  # STORY-092
        ("KI ordnet der Mindmap zu", "Neue Items einsortieren, Knoten vorschlagen.", [],
         ["5b8e795e-adf2-49e3-9cb8-6a2de4a49101"]),  # STORY-104
    ], []),
    ("Spiegel und Sync", "Markdown-Spiegel, Git, Cloud-Sitzungen.", [
        ("Mindmap im Spiegel", "Dateiformat und Sync für den Themenbaum.", [],
         ["fad60a4f-0990-4d9f-8036-b123bb43a596"]),  # STORY-105
    ], []),
]


def call(base: str, method: str, path: str, body: dict | None = None) -> dict | list:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as err:
        sys.exit(f"{method} {path}: {err.code} {err.read().decode()}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="todo_viewer")
    ap.add_argument("--url", default="http://localhost:5411")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    base = args.url.rstrip("/") + "/api"

    projects = [p for p in call(base, "GET", "/workspace/projects") if args.project in (p["name"], p["uid"])]
    if len(projects) != 1:
        sys.exit(f"Projekt '{args.project}' nicht eindeutig gefunden.")
    project = projects[0]["uid"]

    tree = call(base, "GET", f"/mindmap/trees/{project}")
    existing = {(n.get("parent_uid") or "", n["title"]): n["uid"] for n in tree.get("nodes", [])}

    def walk(nodes: list, parent: str, depth: int) -> None:
        for title, text, children, items in nodes:
            uid = existing.get((parent, title))
            mark = "vorhanden" if uid else "neu"
            print(f"{'  ' * depth}- {title} ({mark})")
            if not uid and args.apply:
                body = {"project": project, "title": title, "text": text, **({"parent": parent} if parent else {})}
                uid = call(base, "POST", "/mindmap/nodes", body)["uid"]
            for item in items:
                print(f"{'  ' * depth}    ↳ Item {item}")
                if args.apply:
                    call(base, "POST", f"/mindmap/nodes/{uid}/items", {"item": item, "replace": False, "project": project})
            walk(children, uid or f"<neu:{title}>", depth + 1)

    walk(TREE, "", 0)
    print("\nAngelegt." if args.apply else "\nNur Vorschau. Mit --apply ausführen.")


if __name__ == "__main__":
    main()

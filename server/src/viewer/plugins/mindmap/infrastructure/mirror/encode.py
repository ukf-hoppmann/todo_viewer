"""Einträge → Dateien für `mindmap/`: Knoten, Bäume und Dokumente als ganze Dateien."""

from __future__ import annotations

import re
from collections.abc import Sequence

from viewer.core.domain.files import Change, DeleteFile, FileSet, RenameFile, WriteFile
from viewer.core.domain.sync import MirrorEntry
from viewer.plugins.mindmap.domain.model import TREE_PROJECT
from viewer.plugins.mindmap.infrastructure.mirror.syntax import (
    FORMAT_LINE,
    KIND_DOCUMENT,
    KIND_NODE,
    KIND_TREE,
    MAPS_DIR,
    MINDMAP_DIR,
    PROJECT_FILE,
    UID_LINE,
    display_target,
    map_path,
    slug,
)


def node_path(entry: MirrorEntry) -> str:
    return f"{MINDMAP_DIR}/{entry.label or entry.placeholder}.md"


def render_node(entry: MirrorEntry, project: str) -> str:
    """Die Datei eines Knotens: Kopf, Zuordnungen, Text."""
    f, refs = entry.fields, entry.refs
    lines = [f"# {entry.label or 'NEW'}"]
    if entry.uid is not None:
        lines.append(f"Uid: {entry.uid}")
    lines += [
        f"Title: {f['title']}",
        f"Mark: {f['mark'] or ''}".rstrip(),
        f"Deleted: {f['deleted_at'] or ''}".rstrip(),
    ]
    for role, heading in (("items", "Items"), ("memos", "Memos")):
        if refs.get(role):
            lines.append(f"{heading}:")
            lines += [f"- {display_target(token, project)}" for token in sorted(refs[role])]
    text = "\n".join(lines) + "\n"
    if f["text"]:
        text += "\n" + f["text"] + "\n"
    return text


def render_tree(entry: MirrorEntry) -> str:
    """Die Datei eines Baums: Kopf, Liste der Platzierungen, entfernte Platzierungen."""
    f, refs = entry.fields, entry.refs
    is_project = f["tree_kind"] == TREE_PROJECT
    title = "NEW" if entry.uid is None else ("Projekt" if is_project else f["name"])
    lines = [f"# {title}", f"Format: {FORMAT_LINE}"]
    if entry.uid is not None:
        lines.append(f"Uid: {entry.uid}")
    lines.append(f"Kind: {f['tree_kind']}")
    if not is_project:
        lines += [f"Name: {f['name']}", f"Deleted: {f['deleted_at'] or ''}".rstrip()]
    text = "\n".join(lines) + "\n"
    listed = ["  " * depth + f"- {token}" for depth, token in zip(f["depths"], refs.get("nodes", ()), strict=True)]
    if listed:
        text += "\n" + "\n".join(listed) + "\n"
    if f["removed"]:
        parents = iter(refs.get("removed_parents", ()))
        rows = [
            f"- {node} parent {next(parents) if row['has_parent'] else '-'} position {row['position']} group {group}"
            for row, node, group in zip(f["removed"], refs["removed_nodes"], refs["removed_groups"], strict=True)
        ]
        text += "\nRemoved:\n" + "\n".join(rows) + "\n"
    return text


def _tree_files(current: FileSet) -> dict[str, str]:
    """Pfad der Baumdatei je `Uid` in den vorhandenen Dateien."""
    found: dict[str, str] = {}
    for path, entry in current.files.items():
        is_map = path.startswith(MAPS_DIR + "/") and "/" not in path[len(MAPS_DIR) + 1 :]
        if path == PROJECT_FILE or (is_map and path.endswith(".md")):
            match = UID_LINE.search(entry.text.split("\n\n", 1)[0])
            if match is not None:
                found[match.group("uid")] = path
    return found


def _tree_path(entry: MirrorEntry, existing: dict[str, str], current: FileSet, taken: set[str]) -> str:
    """Der Pfad einer Baumdatei: der Projektbaum fest, eine neue Map nach ihrem Platzhalter, eine vorhandene Map
    behält ihren Pfad, solange er zum Namen passt (`<slug>` oder `<slug>-<n>`), sonst bekommt sie den ersten freien."""
    if entry.fields["tree_kind"] == TREE_PROJECT:
        return PROJECT_FILE
    if entry.uid is None:
        return map_path(str(entry.placeholder))
    base = slug(str(entry.fields["name"]))
    own = existing.get(entry.uid)
    if own is not None and re.fullmatch(rf"{re.escape(MAPS_DIR)}/{re.escape(base)}(-\d+)?\.md", own):
        return own
    candidate, number = map_path(base), 2
    while (candidate in current.files and candidate != own) or candidate in taken:
        candidate = map_path(f"{base}-{number}")
        number += 1
    return candidate


def encode(
    upserts: Sequence[MirrorEntry], removed: Sequence[MirrorEntry], current: FileSet, project: str
) -> list[Change]:
    changes: list[Change] = []
    for entry in (e for e in upserts if e.kind == KIND_NODE):
        path = node_path(entry)
        _write(changes, current, path, render_node(entry, project))
        old = f"{MINDMAP_DIR}/{entry.placeholder}.md" if entry.placeholder and entry.label else None
        if old is not None and old != path and old in current.files:
            changes.append(DeleteFile(old))
    for entry in (e for e in removed if e.kind == KIND_NODE):
        if node_path(entry) in current.files:
            changes.append(DeleteFile(node_path(entry)))
    changes.extend(_document_changes([e for e in upserts if e.kind == KIND_DOCUMENT], removed, current))
    changes.extend(_tree_changes([e for e in upserts if e.kind == KIND_TREE], removed, current))
    return changes


def _write(changes: list[Change], current: FileSet, path: str, text: str) -> None:
    existing = current.files.get(path)
    if existing is None or existing.text != text:
        changes.append(WriteFile(path, text))


def _tree_changes(upserts: Sequence[MirrorEntry], removed: Sequence[MirrorEntry], current: FileSet) -> list[Change]:
    changes: list[Change] = []
    existing = _tree_files(current)
    taken: set[str] = set()
    for entry in upserts:
        path = _tree_path(entry, existing, current, taken)
        taken.add(path)
        _write(changes, current, path, render_tree(entry))
        stale = {map_path(entry.placeholder)} if entry.placeholder and entry.uid is not None else set()
        if entry.uid is not None and entry.uid in existing:
            stale.add(existing[entry.uid])
        for old in sorted(stale - {path}):
            if old in current.files:
                changes.append(DeleteFile(old))
    for entry in removed:
        gone = existing.get(entry.uid) if entry.uid is not None else None
        if gone is None and entry.placeholder is not None:
            gone = map_path(entry.placeholder)
        if gone is not None and gone in current.files and gone not in taken:
            changes.append(DeleteFile(gone))
    return changes


def _document_changes(upserts: Sequence[MirrorEntry], removed: Sequence[MirrorEntry], current: FileSet) -> list[Change]:
    changes: list[Change] = []
    for entry in upserts:
        path = f"{MINDMAP_DIR}/{entry.label}"
        content = entry.fields["content"]
        if entry.placeholder:
            stem, suffix = entry.placeholder.split("/", 1)
            old = f"{MINDMAP_DIR}/{stem}_{suffix}.md"
            if old in current.files and old != path:
                changes.append(RenameFile(old, path))
                if current.files[old].text != content:
                    changes.append(WriteFile(path, content))
                continue
        _write(changes, current, path, content)
    for entry in removed:
        path = f"{MINDMAP_DIR}/{entry.label}"
        if entry.kind == KIND_DOCUMENT and path in current.files:
            changes.append(DeleteFile(path))
    return changes

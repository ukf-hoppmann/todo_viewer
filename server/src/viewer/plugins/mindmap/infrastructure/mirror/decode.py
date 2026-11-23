"""Dateien → Einträge für `mindmap/`: Knoten, Dokumente und Bäume (Format Version 1)."""

from __future__ import annotations

import re
from typing import NoReturn

from viewer.core.domain.errors import DomainError
from viewer.core.domain.files import FileSet, has_merge_markers
from viewer.core.domain.sync import MirrorEntry, MirrorFormatError
from viewer.plugins.mindmap.domain.model import MARK_DISCARDED, MARK_LATER, TREE_FREE, TREE_PROJECT
from viewer.plugins.mindmap.domain.tree import clean_map_name
from viewer.plugins.mindmap.infrastructure.mirror.syntax import (
    DOCUMENT_FILE,
    FORMAT_LINE,
    KIND_DOCUMENT,
    KIND_NODE,
    KIND_TREE,
    MAPS_DIR,
    MINDMAP_DIR,
    NODE_FILE,
    NODE_KEYS,
    NODE_SECTIONS,
    NODE_TOKEN,
    PLACEHOLDER,
    PROJECT_FILE,
    REMOVED_ROW,
    TREE_KEYS,
    TREE_ROW,
    normalize_target,
    parse_time,
)

_MARKS = ("", MARK_LATER, MARK_DISCARDED)


def _fail(code: str, message: str, path: str, line: int) -> NoReturn:
    raise MirrorFormatError(code, message, file=path, line=line)


def decode(files: FileSet, project: str) -> list[MirrorEntry]:
    """Alle Einträge: erst die Bäume, dann die Knoten, dann ihre Dokumente."""
    for path in sorted(files.files):
        if path.startswith(MINDMAP_DIR + "/") and path.endswith(".md") and has_merge_markers(files.files[path].text):
            _fail("merge_markers", "Konflikt aus einem Git-Merge", path, _marker_line(files.files[path].text))
    trees = _trees(files)
    nodes = _nodes(files, project)
    documents = _documents(files, nodes)
    _check_unique(trees, nodes)
    _check_map_names(trees)
    _check_items(nodes)
    return [*trees, *nodes, *documents]


def _marker_line(text: str) -> int:
    for index, line in enumerate(text.split("\n")):
        if re.match(r"<{7}( |$)", line):
            return index + 1
    return 1


def _name(path: str) -> str:
    return path.rsplit("/", 1)[-1]


# --- Kopf ----------------------------------------------------------------------------------------------------------


def _header(
    lines: list[str], path: str, keys: tuple[str, ...], sections: tuple[str, ...]
) -> tuple[dict[str, tuple[str, int]], dict[str, list[tuple[str, int]]], int]:
    """Liest den Kopf bis zur ersten Leerzeile: Werte je Kopfzeile, Zeilen je Abschnitt, Index der Leerzeile."""
    values: dict[str, tuple[str, int]] = {}
    listed: dict[str, list[tuple[str, int]]] = {}
    section: str | None = None
    index = 1
    while index < len(lines) and lines[index].strip():
        raw, line = lines[index], index + 1
        index += 1
        if raw.startswith("- "):
            if section is None:
                _fail("invalid_value", f"Zeile ohne Abschnitt: `{raw}`", path, line)
            target = raw[2:].strip()
            if not target or " " in target:
                _fail("invalid_value", f"Kein gültiges Ziel: `{raw}`", path, line)
            listed[section].append((target, line))
            continue
        key, separator, value = raw.partition(":")
        key = key.strip()
        if not separator:
            _fail("invalid_value", f"Keine Kopfzeile: `{raw}`", path, line)
        if key in sections:
            if value.strip():
                _fail("invalid_value", f"`{key}:` steht allein in der Zeile", path, line)
            if key in listed:
                _fail("invalid_value", f"`{key}` steht zweimal im Kopf", path, line)
            section = key
            listed[key] = []
            continue
        if key not in keys:
            _fail("unknown_field", f"Unbekannte Kopfzeile `{key}`", path, line)
        if key in values:
            _fail("invalid_value", f"`{key}` steht zweimal im Kopf", path, line)
        section = None
        values[key] = (value.strip(), line)
    return values, listed, index


def _moment(values: dict[str, tuple[str, int]], key: str, path: str) -> str | None:
    text, line = values.get(key, ("", 1))
    if not text:
        return None
    try:
        return parse_time(text)
    except ValueError:
        _fail("invalid_value", f"{key} `{text}` ist kein Zeitpunkt", path, line)


# --- Knoten --------------------------------------------------------------------------------------------------------


def _nodes(files: FileSet, project: str) -> list[MirrorEntry]:
    nodes: list[MirrorEntry] = []
    for path in sorted(files.files):
        match = NODE_FILE.match(_name(path))
        if match is None or path != f"{MINDMAP_DIR}/{_name(path)}":
            continue
        nodes.append(_node(path, files.files[path].text, match.group("stem"), project))
    return nodes


def _node(path: str, text: str, stem: str, project: str) -> MirrorEntry:
    lines = text.split("\n")
    is_new = stem.startswith("new-")
    expected = "# NEW" if is_new else f"# {stem}"
    if lines[0].rstrip() != expected:
        shown = lines[0].strip() or "(leer)"
        _fail("file_label_mismatch", f"Datei `{_name(path)}` enthält `{shown.removeprefix('# ')}`", path, 1)
    if is_new and not PLACEHOLDER.match(stem):
        _fail("invalid_placeholder", "Der Kurzname besteht aus `a-z`, `0-9` und `-`", path, 1)
    values, listed, index = _header(lines, path, NODE_KEYS, NODE_SECTIONS)
    uid = values.get("Uid", ("", 1))[0] or None
    if is_new and "Uid" in values:
        _fail("invalid_value", "Ein neuer Knoten hat keine `Uid`", path, values["Uid"][1])
    if not is_new and uid is None:
        _fail("missing_field", f"`{stem}` ohne `Uid`", path, 1)
    title = values.get("Title", ("", 1))[0]
    if not title:
        _fail("missing_field", f"`{stem}` ohne `Title`", path, 1)
    mark = values.get("Mark", ("", 1))[0]
    if mark not in _MARKS:
        _fail("invalid_value", f"Mark `{mark}` ist `later` oder `discarded`", path, values["Mark"][1])
    refs: dict[str, tuple[str, ...]] = {}
    source_lines: dict[str, int] = {}
    for section, role in (("Items", "items"), ("Memos", "memos")):
        tokens: list[str] = []
        for target, line in listed.get(section, []):
            token = normalize_target(target, project)
            source_lines.setdefault(f"{role}:{token}", line)
            tokens.append(token)
        if tokens:
            refs[role] = tuple(sorted(set(tokens)))
    if uid is not None:
        source_lines["uid"] = values["Uid"][1]
    body = "\n".join(lines[index + 1 :]).removesuffix("\n") if index < len(lines) else ""
    fields = {
        "title": title,
        "text": body or None,
        "mark": mark or None,
        "deleted_at": _moment(values, "Deleted", path),
    }
    return MirrorEntry(
        KIND_NODE,
        None if is_new else stem,
        fields,
        refs,
        uid,
        stem if is_new else None,
        source=(path, 1),
        source_lines=source_lines,
    )


# --- Bäume ---------------------------------------------------------------------------------------------------------


def _trees(files: FileSet) -> list[MirrorEntry]:
    trees: list[MirrorEntry] = []
    for path in sorted(files.files):
        if path == PROJECT_FILE:
            trees.append(_tree(path, files.files[path].text, TREE_PROJECT, None))
        elif path.startswith(MAPS_DIR + "/") and "/" not in path[len(MAPS_DIR) + 1 :] and path.endswith(".md"):
            trees.append(_tree(path, files.files[path].text, TREE_FREE, _name(path).removesuffix(".md")))
    return trees


def _tree(path: str, text: str, expected_kind: str, stem: str | None) -> MirrorEntry:
    lines = text.split("\n")
    is_new = stem is not None and stem.startswith("new-")
    if is_new:
        assert stem is not None
        if lines[0].rstrip() != "# NEW":
            _fail("file_label_mismatch", f"Datei `{_name(path)}` enthält `{lines[0].strip() or '(leer)'}`", path, 1)
        if not PLACEHOLDER.match(stem):
            _fail("invalid_placeholder", "Der Kurzname besteht aus `a-z`, `0-9` und `-`", path, 1)
    values, _, index = _header(lines, path, TREE_KEYS, ())
    if values.get("Format", ("", 1))[0] != FORMAT_LINE:
        found = values.get("Format", ("fehlt", 1))
        _fail("format_version", f"Erwartet `Format: {FORMAT_LINE}`, gefunden: {found[0]}", path, found[1])
    uid = values.get("Uid", ("", 1))[0] or None
    if is_new and "Uid" in values:
        _fail("invalid_value", "Eine neue Map hat keine `Uid`", path, values["Uid"][1])
    if not is_new and uid is None:
        _fail("missing_field", "Baum ohne `Uid`", path, 1)
    if "Kind" not in values:
        _fail("missing_field", "Baum ohne `Kind`", path, 1)
    kind, kind_line = values["Kind"]
    if kind != expected_kind:
        shown = "der Projektbaum (`project`)" if expected_kind == TREE_PROJECT else "eine freie Map (`free`)"
        _fail("invalid_value", f"Diese Datei ist {shown}, `Kind` ist `{kind}`", path, kind_line)
    name: str | None = None
    deleted: str | None = None
    if expected_kind == TREE_FREE:
        if not values.get("Name", ("", 1))[0]:
            _fail("missing_field", "Map ohne `Name`", path, 1)
        try:
            name = clean_map_name(values["Name"][0])
        except DomainError as error:
            _fail("invalid_value", str(error), path, values["Name"][1])
        deleted = _moment(values, "Deleted", path)
    else:
        for key in ("Name", "Deleted"):
            if key in values:
                _fail("invalid_value", f"Der Projektbaum hat kein `{key}`", path, values[key][1])
    nodes, depths, removed_rows = _tree_body(lines, index, path)
    refs: dict[str, tuple[str, ...]] = {}
    if nodes:
        refs["nodes"] = tuple(nodes)
    removed: list[dict[str, object]] = []
    if removed_rows:
        refs["removed_nodes"] = tuple(row[0] for row in removed_rows)
        refs["removed_groups"] = tuple(row[3] for row in removed_rows)
        parents = tuple(row[1] for row in removed_rows if row[1] is not None)
        if parents:
            refs["removed_parents"] = parents
        removed = [{"position": row[2], "has_parent": row[1] is not None} for row in removed_rows]
    fields = {"tree_kind": expected_kind, "name": name, "deleted_at": deleted, "depths": depths, "removed": removed}
    source_lines = {"uid": values["Uid"][1]} if uid is not None else {}
    if name is not None:
        source_lines["name"] = values["Name"][1]
    return MirrorEntry(
        KIND_TREE,
        None,
        fields,
        refs,
        uid,
        stem if is_new else None,
        source=(path, 1),
        source_lines=source_lines,
    )


def _tree_body(
    lines: list[str], start: int, path: str
) -> tuple[list[str], list[int], list[tuple[str, str | None, int, str]]]:
    """Die Platzierungen (Knoten und Tiefen in Tiefensuche) und die entfernten Platzierungen (Knoten, Parent oder
    `None`, Stelle, Gruppe)."""
    nodes: list[str] = []
    depths: list[int] = []
    removed: list[tuple[str, str | None, int, str]] = []
    removed_lines: list[int] = []
    seen: set[str] = set()
    in_removed = False
    for index in range(start, len(lines)):
        raw, line = lines[index], index + 1
        if not raw.strip():
            continue
        if raw.rstrip() == "Removed:":
            if in_removed:
                _fail("invalid_value", "`Removed:` steht zweimal", path, line)
            in_removed = True
            continue
        if not in_removed:
            match = TREE_ROW.match(raw)
            if match is None:
                _fail("invalid_value", f"Keine Zeile der Baumliste (`- NODE-001`): `{raw}`", path, line)
            indent = len(match.group("indent"))
            if indent % 2:
                _fail("invalid_value", "Die Einrückung ist ein Vielfaches von zwei Leerzeichen", path, line)
            depth = indent // 2
            if depth > (depths[-1] + 1 if depths else 0):
                _fail("invalid_value", "Die Einrückung springt über eine Ebene", path, line)
            token = match.group("token")
            if not NODE_TOKEN.match(token):
                _fail("invalid_value", f"`{token}` ist weder ein Label (`NODE-001`) noch ein Platzhalter", path, line)
            if token in seen:
                _fail("duplicate_node_in_tree", f"`{token}` steht schon in diesem Baum", path, line)
            seen.add(token)
            nodes.append(token)
            depths.append(depth)
            continue
        row = REMOVED_ROW.match(raw)
        if row is None:
            _fail(
                "invalid_value",
                f"Keine entfernte Platzierung (`- NODE-001 parent … position … group …`): `{raw}`",
                path,
                line,
            )
        parent = row.group("parent")
        for shown in (row.group("node"), row.group("group"), *([] if parent == "-" else [parent])):
            if not NODE_TOKEN.match(shown):
                _fail("invalid_value", f"`{shown}` ist weder ein Label (`NODE-001`) noch ein Platzhalter", path, line)
        node = row.group("node")
        if node in seen:
            _fail("duplicate_node_in_tree", f"`{node}` steht schon in diesem Baum", path, line)
        seen.add(node)
        removed.append((node, None if parent == "-" else parent, int(row.group("position")), row.group("group")))
        removed_lines.append(line)
    _check_cycles(removed, removed_lines, path)
    return nodes, depths, removed


def _check_cycles(removed: list[tuple[str, str | None, int, str]], lines: list[int], path: str) -> None:
    parent_of = {row[0]: row[1] for row in removed}
    for row, line in zip(removed, lines, strict=True):
        seen = {row[0]}
        current = row[1]
        while current is not None and current in parent_of:
            if current in seen:
                _fail("tree_cycle", f"Die früheren Parents von `{row[0]}` bilden einen Kreis", path, line)
            seen.add(current)
            current = parent_of[current]
        if row[1] == row[0]:
            _fail("tree_cycle", f"`{row[0]}` ist sein eigener früherer Parent", path, line)


# --- Dokumente -----------------------------------------------------------------------------------------------------


def _documents(files: FileSet, nodes: list[MirrorEntry]) -> list[MirrorEntry]:
    by_stem = {str(n.label or n.placeholder): n for n in nodes}
    documents: list[MirrorEntry] = []
    for path in sorted(files.files):
        name = _name(path)
        match = DOCUMENT_FILE.match(name)
        if match is None or path != f"{MINDMAP_DIR}/{name}":
            continue
        node = by_stem.get(match.group("stem"))
        if node is None:
            _fail("file_label_mismatch", f"Das Dokument gehört zu keinem Knoten (`{match.group('stem')}`)", path, 1)
        suffix = match.group("suffix")
        fields = {"content": files.files[path].text, "kind": "notes" if suffix == "notes" else "spec"}
        refs = {"node": (match.group("stem"),)}
        if node.uid is not None:
            documents.append(MirrorEntry(KIND_DOCUMENT, name, fields, refs, f"{node.uid}/{suffix}", source=(path, 1)))
        else:
            placeholder = f"{match.group('stem')}/{suffix}"
            documents.append(MirrorEntry(KIND_DOCUMENT, None, fields, refs, None, placeholder, source=(path, 1)))
    return documents


# --- Eindeutigkeit und Regeln über Dateien -------------------------------------------------------------------------


def _shown(entry: MirrorEntry) -> str:
    return str(entry.label or entry.placeholder or (entry.fields.get("name") or "Baum"))


def _check_unique(trees: list[MirrorEntry], nodes: list[MirrorEntry]) -> None:
    uids: dict[str, MirrorEntry] = {}
    for entry in [*trees, *nodes]:
        if entry.uid is None:
            continue
        path, _ = entry.source or ("", 1)
        if entry.uid in uids:
            other = uids[entry.uid]
            _fail(
                "duplicate_uid",
                f"`{_shown(entry)}` trägt die Uid von `{_shown(other)}` ({(other.source or ('', 1))[0]})",
                path,
                entry.source_lines.get("uid", 1),
            )
        uids[entry.uid] = entry


def _check_map_names(trees: list[MirrorEntry]) -> None:
    """Die freien Maps eines Projekts, die nicht im Papierkorb liegen, heißen verschieden (ohne Groß/Klein)."""
    names: dict[str, MirrorEntry] = {}
    for tree in trees:
        if tree.fields["tree_kind"] != TREE_FREE or tree.fields["deleted_at"] is not None:
            continue
        key = str(tree.fields["name"]).casefold()
        if key in names:
            path, _ = tree.source or ("", 1)
            _fail(
                "duplicate_label", f"Die Map `{tree.fields['name']}` kommt zweimal vor", path, tree.source_lines["name"]
            )
        names[key] = tree


def _check_items(nodes: list[MirrorEntry]) -> None:
    """Ein Item steht bei höchstens einem Knoten (nur aus den Dateien zu entscheiden)."""
    holders: dict[str, MirrorEntry] = {}
    for node in nodes:
        path, _ = node.source or ("", 1)
        for token in node.refs.get("items", ()):
            if token in holders:
                other = holders[token]
                _fail(
                    "rule_violation",
                    f"Das Item `{token}` steht schon bei `{_shown(other)}` ({(other.source or ('', 1))[0]})",
                    path,
                    node.source_lines.get(f"items:{token}", 1),
                )
            holders[token] = node

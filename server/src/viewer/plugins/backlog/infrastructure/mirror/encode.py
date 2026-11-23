"""Einträge → Dateien: schreibt nur, was sich ändert. Felder werden einzeln ersetzt, ein Eintrag wechselt nur die Datei,
wenn sich seine Lage ändert, ein Platzhalter-Eintrag wird an seiner Stelle ersetzt, Dokumente werden umbenannt."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from viewer.core.domain.files import Change, DeleteFile, FileSet, RenameFile, WriteFile
from viewer.core.domain.sync import MirrorEntry
from viewer.plugins.backlog.infrastructure.mirror.decode import DOCUMENT_KIND, DOCUMENT_NAME
from viewer.plugins.backlog.infrastructure.mirror.syntax import (
    ARCHIVE_FILE,
    FIELD_ORDER,
    FREE_TEXT,
    IGNORED_FIELDS,
    NO_ENTRIES,
    REFERENCE_FIELDS,
    TODO_FILE,
    WORK_ITEMS,
    Block,
    clean,
    field_lines,
    parse_blocks,
    reference_text,
    references,
    same_text,
    upgrade_format_line,
    with_period,
)

_TEMPLATES = {
    TODO_FILE: (
        "# Project Backlog\n\n"
        "Active project work: open, in progress, or awaiting a project-owner decision.\n"
        "Completed and rejected items are moved to `archive.md`; per-item notes and\n"
        "specs live in `items/<ID>/`.\n\n"
        "Format: Claude_Harness backlog format version 3. The rules are defined in\n"
        "`docs/techdocs/interfaces.md` of the ToDo Viewer.\n\n"
        "## Work items\n"
    ),
    ARCHIVE_FILE: (
        "# Project Backlog Archive\n\n"
        "Completed and rejected work items, moved unchanged from `TODO.md` after the\n"
        "project owner's decision.\n\n"
        "Format: Claude_Harness backlog format version 3. The rules are defined in\n"
        "`docs/techdocs/interfaces.md` of the ToDo Viewer.\n\n"
        "## Work items\n"
    ),
}


def target_file(entry: MirrorEntry) -> str:
    """`archive.md` für abgeschlossene und gelöschte Items, sonst `TODO.md` (die Lage ist keine Information)."""
    closed = entry.fields["status"] in ("Completed", "Rejected") or entry.fields["deleted"] is not None
    return ARCHIVE_FILE if closed else TODO_FILE


def desired_fields(entry: MirrorEntry) -> dict[str, str]:
    """Feld → Text, wie er im Eintrag stehen soll (Format Version 3); fehlende Werte fehlen."""
    f = entry.fields
    parent = entry.refs.get("parent", ())
    values: dict[str, str] = {}
    if entry.uid is not None:
        values["Uid"] = entry.uid
    type_label = {"epic": "Epic", "story": "Story", "task": "Task"}[entry.kind]
    values["Type"] = type_label
    if entry.kind != "epic" or parent:
        values["Parent"] = reference_text(parent)
    if parent:
        values["Required for parent"] = "No" if f["required_for_parent"] is False else "Yes"
    values["Status"] = f["status"]
    if f["created"]:
        values["Created"] = f["created"]
    values["Priority"] = f["priority"]
    values["Dependencies"] = reference_text(entry.refs.get("dependencies", ()))
    values["Goal"] = f["goal"]
    values["Completion criteria"] = f["completion_criteria"]
    if f["summary"]:
        values["Summary"] = f["summary"]
    if f["resolution"]:
        values["Resolution"] = f["resolution"]
    if f["deleted"]:
        values["Deleted"] = f["deleted"]
    return values


def _field_text(label: str, text: str) -> str:
    return text if label in FREE_TEXT else with_period(text)


def render_block(entry: MirrorEntry) -> list[str]:
    lines = [f"- `{entry.label}` **{entry.fields['title']}**"]
    for label, text in desired_fields(entry).items():
        lines += field_lines(label, _field_text(label, text))
    return lines


@dataclass
class _File:
    path: str
    lines: list[str]
    existed: bool
    original: str

    def blocks(self) -> list[Block]:
        return parse_blocks(self.lines)


def _find(files: dict[str, _File], uid: str | None, placeholder: str | None) -> tuple[_File, Block] | None:
    for file in files.values():
        for block in file.blocks():
            uid_field = block.field("Uid")
            if uid is not None and uid_field is not None and clean(uid_field.value) == uid:
                return file, block
            if uid is None and placeholder is not None and block.ident == placeholder:
                return file, block
    return None


def _find_by_ident(files: dict[str, _File], ident: str) -> tuple[_File, Block] | None:
    for file in files.values():
        for block in file.blocks():
            if block.ident == ident:
                return file, block
    return None


def _same_value(label: str, existing: str, wanted: str) -> bool:
    if label in FREE_TEXT:
        return same_text(existing, wanted)
    if label in REFERENCE_FIELDS:
        return sorted(references(existing)) == sorted(references(wanted))
    return clean(existing) == clean(wanted)


def _block_at(file: _File, first: int) -> Block:
    """Der Eintrag, dessen Kopfzeile bei Index `first` steht (die Kopfzeile wandert beim Ändern der Felder nicht)."""
    return next(block for block in file.blocks() if block.first == first)


def _edit(file: _File, first: int, entry: MirrorEntry) -> None:
    """Bringt den Eintrag in `file` auf den Stand von `entry`: Kopfzeile und je Feld nur, was sich unterscheidet."""

    def block() -> Block:
        return _block_at(file, first)

    header = f"- `{entry.label}` **{entry.fields['title']}**"
    current = block()
    if file.lines[current.first] != header:
        file.lines[current.first] = header
    wanted = desired_fields(entry)
    before = list(file.lines)
    # Ersetzen und Einfügen in der Reihenfolge des Formats; jedes Mal neu lesen, weil sich Indizes verschieben.
    for label in FIELD_ORDER:
        current = block()
        existing = current.field(label)
        if label not in wanted:
            if existing is not None:
                del file.lines[existing.first : existing.end]
            continue
        text = _field_text(label, wanted[label])
        if existing is not None:
            if not _same_value(label, existing.value, text):
                file.lines[existing.first : existing.end] = field_lines(label, text)
            continue
        position = current.first + 1
        for earlier in FIELD_ORDER[: FIELD_ORDER.index(label)]:
            present = current.field(earlier)
            if present is not None:
                position = present.end
        file.lines[position:position] = field_lines(label, text)
    if file.lines != before:  # nur ein ohnehin geänderter Eintrag verliert die Felder früherer Versionen
        for label in IGNORED_FIELDS:
            old = block().field(label)
            if old is not None:
                del file.lines[old.first : old.end]


def _section_start(lines: list[str]) -> int | None:
    return next((i for i, line in enumerate(lines) if WORK_ITEMS.match(line)), None)


def _cut(file: _File, first: int) -> list[str]:
    block = _block_at(file, first)
    lines = file.lines
    stop = block.end + 1 if block.end < len(lines) and not lines[block.end].strip() else block.end
    start = block.first
    if stop == block.end and start > 0 and not lines[start - 1].strip():
        start -= 1  # letzter Eintrag: die Leerzeile davor statt dahinter
    removed = lines[block.first : block.end]
    del lines[start:stop]
    section = _section_start(lines)
    if section is not None and not parse_blocks(lines):
        del lines[section + 1 :]
        lines.extend(["", NO_ENTRIES])
    return removed


def _append(file: _File, block: list[str]) -> None:
    lines = file.lines
    section = _section_start(lines)
    if section is None:
        while lines and not lines[-1].strip():
            lines.pop()
        lines.extend(["", "## Work items"])
        section = len(lines) - 1
    for index in range(section + 1, len(lines)):
        if lines[index].strip() == NO_ENTRIES:
            del lines[index]
            break
    while lines and not lines[-1].strip():
        lines.pop()
    lines.extend(["", *block])


def _load(current: FileSet) -> dict[str, _File]:
    files: dict[str, _File] = {}
    for path in (TODO_FILE, ARCHIVE_FILE):
        entry = current.files.get(path)
        text = entry.text if entry is not None else _TEMPLATES[path]
        files[path] = _File(path, text.rstrip("\n").split("\n"), entry is not None, text)
    return files


def _doc_path(entry: MirrorEntry) -> str:
    return f"items/{entry.refs['item'][0]}/{entry.label}"


def _doc_text(entry: MirrorEntry) -> str:
    """Notizen bekommen ihre Titelzeile aus dem aktuellen Label und Titel des Items."""
    if entry.fields["kind"] != "notes":
        return str(entry.fields["content"])
    return f"# {entry.refs['item'][0]} — {entry.fields['title']}\n{entry.fields['content']}"


def encode(upserts: Sequence[MirrorEntry], removed: Sequence[MirrorEntry], current: FileSet) -> list[Change]:
    files = _load(current)
    items = [e for e in upserts if e.kind != DOCUMENT_KIND]
    docs = [e for e in upserts if e.kind == DOCUMENT_KIND]

    removed_items = [e for e in removed if e.kind != DOCUMENT_KIND]
    for entry in removed_items:
        found = _find(files, entry.uid, entry.placeholder)
        if found is not None:
            _cut(found[0], found[1].first)

    for entry in items:
        found = _find(files, entry.uid, None)
        if found is None and entry.placeholder is not None:
            found = _find(files, None, entry.placeholder)
        destination = files[target_file(entry)]
        if found is None:
            _append(destination, render_block(entry))
            continue
        file, block = found
        _edit(file, block.first, entry)
        if file is not destination:
            _append(destination, _cut(file, block.first))

    changes: list[Change] = []
    for file in files.values():
        text = "\n".join(file.lines).rstrip("\n") + "\n"
        if file.existed and text == file.original:
            continue
        upgrade_format_line(file.lines)  # geschrieben wird immer die aktuelle Version
        text = "\n".join(file.lines).rstrip("\n") + "\n"
        if not file.existed and not parse_blocks(file.lines):
            continue  # eine Datei, die es nicht gibt und die leer bliebe, wird nicht angelegt
        changes.append(WriteFile(file.path, text))
    changes.extend(_document_changes(docs, [e for e in removed if e.kind == DOCUMENT_KIND], current))
    return changes


def _document_changes(upserts: Sequence[MirrorEntry], removed: Sequence[MirrorEntry], current: FileSet) -> list[Change]:
    changes: list[Change] = []
    existing = _existing_documents(current)
    for entry in upserts:
        new_path = _doc_path(entry)
        old_path: str | None = None
        if entry.placeholder:
            folder, suffix = entry.placeholder.split("/", 1)
            old_path = f"items/{folder}/{folder}_{suffix}.md"
        elif entry.uid is not None:
            old_path = existing.get(entry.uid)
        content = _doc_text(entry)
        if old_path is not None and old_path in current.files and old_path != new_path:
            changes.append(RenameFile(old_path, new_path))
            if current.files[old_path].text != content:
                changes.append(WriteFile(new_path, content))
        elif old_path is None or old_path not in current.files or current.files[old_path].text != content:
            if new_path in current.files and current.files[new_path].text == content:
                continue
            changes.append(WriteFile(new_path, content))
    for entry in removed:
        path = existing.get(str(entry.uid)) or _doc_path(entry)
        if path in current.files:
            changes.append(DeleteFile(path))
    return changes


def _existing_documents(current: FileSet) -> dict[str, str]:
    """Dokument-`uid` → Pfad der Dokumente, die schon in den Dateien liegen."""
    uids = {}
    for path in (TODO_FILE, ARCHIVE_FILE):
        entry = current.files.get(path)
        if entry is None:
            continue
        for block in parse_blocks(entry.text.split("\n")):
            uid_field = block.field("Uid")
            if uid_field is not None:
                uids[block.ident] = clean(uid_field.value)
    documents: dict[str, str] = {}
    for path in current.files:
        parts = path.split("/")
        if len(parts) == 3 and parts[0] == "items":
            match = DOCUMENT_NAME.match(parts[2])
            if match and parts[1] in uids and match.group("label") == parts[1]:
                documents[f"{uids[parts[1]]}/{match.group('kind')}"] = path
    return documents

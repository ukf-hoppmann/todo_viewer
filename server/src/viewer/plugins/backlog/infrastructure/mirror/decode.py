"""Dateien → Einträge: liest `TODO.md`, `archive.md` und `items/**` und prüft sie nach dem Format Version 2."""

from __future__ import annotations

import re
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from viewer.core.domain.files import FileSet
from viewer.core.domain.sync import MirrorEntry, MirrorFormatError
from viewer.plugins.backlog.domain.lifecycle import LifecycleRules, LifecycleViolation
from viewer.plugins.backlog.domain.model import KIND_BY_TYPE, PRIORITIES, STATUSES, TYPES, Item
from viewer.plugins.backlog.domain.notes import assemble, split, without_title
from viewer.plugins.backlog.infrastructure.mirror.syntax import (
    ARCHIVE_FILE,
    DAY,
    FIELD_ORDER,
    LABEL,
    PLACEHOLDER,
    TODO_FILE,
    Block,
    clean,
    format_line,
    parse_blocks,
    references,
)

DOCUMENT_KIND = "backlog.document"
DOCUMENT_NAME = re.compile(r"^(?P<label>.+?)_(?P<kind>notes|spec(?:_[A-Za-z0-9-]+)?)\.md$")
ITEM_FILES = (TODO_FILE, ARCHIVE_FILE)
FINAL = ("Completed", "Rejected")


@dataclass
class _Decoded:
    entry: MirrorEntry
    block: Block
    path: str


def decode(files: FileSet) -> list[MirrorEntry]:
    """Alle Einträge: erst die Items (`TODO.md`, dann `archive.md`), dann die Dokumente aus `items/<LABEL>/`."""
    decoded = _items(files)
    entries = [d.entry for d in decoded]
    docs = _documents(files, decoded)
    _check_rules(decoded, docs)
    return [*entries, *docs]


# --- Items ---------------------------------------------------------------------------------------------------------


def _items(files: FileSet) -> list[_Decoded]:
    decoded: list[_Decoded] = []
    seen_uids: dict[str, str] = {}
    seen_ids: dict[str, str] = {}
    for path in ITEM_FILES:
        entry = files.files.get(path)
        if entry is None:
            continue
        lines = entry.text.split("\n")
        line, version = format_line(lines)
        if version != 2:
            raise MirrorFormatError(
                "format_version",
                "Die Kennung fehlt" if version is None else f"Die Kennung nennt Version {version}, gebraucht wird 2",
                file=path,
                line=line,
            )
        for block in parse_blocks(lines):
            item = _entry(path, block)
            if block.ident in seen_ids:
                raise MirrorFormatError(
                    "duplicate_label",
                    f"`{block.ident}` steht schon in `{seen_ids[block.ident]}`",
                    file=path,
                    line=block.line,
                )
            seen_ids[block.ident] = path
            if item.uid is not None:
                if item.uid in seen_uids:
                    uid_line = (block.field("Uid") or block.fields[0]).line
                    raise MirrorFormatError(
                        "duplicate_uid",
                        f"`{block.ident}` trägt die Uid von `{seen_uids[item.uid]}`",
                        file=path,
                        line=uid_line,
                    )
                seen_uids[item.uid] = block.ident
            decoded.append(_Decoded(item, block, path))
    return decoded


def _fail(code: str, message: str, path: str, line: int) -> MirrorFormatError:
    return MirrorFormatError(code, message, file=path, line=line)


def _entry(path: str, block: Block) -> MirrorEntry:
    ident = block.ident
    is_new = ident.startswith("NEW-")
    if is_new and not PLACEHOLDER.match(ident):
        raise _fail(
            "invalid_placeholder",
            f"`{ident}`: nach `NEW-` nur Kleinbuchstaben, Ziffern und `-`",
            path,
            block.line,
        )
    if not is_new and not LABEL.match(ident):
        raise _fail("invalid_value", f"`{ident}` ist kein Label (EPIC-001, STORY-001, TASK-001)", path, block.line)

    values: dict[str, str] = {}
    lines: dict[str, int] = {}
    for field in block.fields:
        if field.label not in FIELD_ORDER:
            raise _fail("unknown_field", f"Das Feld `{field.label}` kennt das Format nicht", path, field.line)
        if field.label in values:
            raise _fail("invalid_value", f"Das Feld `{field.label}` steht zweimal", path, field.line)
        values[field.label] = field.value
        lines[field.label] = field.line

    def need(label: str) -> str:
        if label not in values:
            raise _fail("missing_field", f"`{ident}` ohne `{label}`", path, block.line)
        return values[label]

    uid: str | None = None
    if "Uid" in values:
        text = clean(values["Uid"])
        try:
            uid = str(uuid.UUID(text))
        except ValueError:
            raise _fail("invalid_value", f"`{text}` ist keine Uid", path, lines["Uid"]) from None
        if is_new:
            raise _fail("invalid_value", f"`{ident}` ist ein neuer Eintrag und hat keine Uid", path, lines["Uid"])
    elif not is_new:
        raise _fail("missing_field", f"`{ident}` ohne `Uid`", path, block.line)

    type_ = clean(need("Type"))
    if type_ not in TYPES:
        raise _fail("invalid_value", f"Typ `{type_}` gibt es nicht", path, lines["Type"])
    if not is_new and LABEL.match(ident) and ident.split("-")[0] != type_.upper():
        raise _fail("invalid_value", f"Typ `{type_}` passt nicht zu `{ident}`", path, lines["Type"])
    status = _choice("Status", clean(need("Status")), STATUSES, path, lines)
    priority = _choice("Priority", clean(need("Priority")), tuple(PRIORITIES), path, lines)
    area = clean(need("Area"))
    goal = need("Goal").strip()
    criteria = need("Completion criteria").strip()
    dependencies = _refs(need("Dependencies"), path, lines["Dependencies"])
    parent: tuple[str, ...] = ()
    if type_ != "Epic" or "Parent" in values:
        parent = _refs(need("Parent"), path, lines.get("Parent", block.line))
    required: bool | None = None
    if parent:
        text = clean(need("Required for parent"))
        if text not in ("Yes", "No"):
            raise _fail("invalid_value", f"`{text}` ist weder Yes noch No", path, lines["Required for parent"])
        required = text == "Yes"
    elif "Required for parent" in values:
        raise _fail(
            "invalid_value", "'Required for parent' gibt es nur mit einem Parent", path, lines["Required for parent"]
        )
    created = _day(values, "Created", path, lines)
    deleted = _day(values, "Deleted", path, lines)
    resolution = values.get("Resolution", "").strip() or None
    if status in FINAL and resolution is None:
        raise _fail("missing_field", f"`{ident}` ({status}) ohne `Resolution`", path, block.line)
    summary = values.get("Summary", "").strip() or None

    fields = {
        "title": block.title,
        "status": status,
        "priority": priority,
        "area": area,
        "created": created,
        "goal": goal,
        "completion_criteria": criteria,
        "summary": summary,
        "resolution": resolution,
        "required_for_parent": required,
        "deleted": deleted,
    }
    refs: dict[str, tuple[str, ...]] = {}
    if parent:
        refs["parent"] = parent
    if dependencies:
        refs["dependencies"] = tuple(sorted(dependencies))
    return MirrorEntry(
        kind=KIND_BY_TYPE[type_],
        label=None if is_new else ident,
        fields=fields,
        refs=refs,
        uid=uid,
        placeholder=ident if is_new else None,
        source=(path, block.line),
        source_lines={name: line for name, line in lines.items()},
    )


def _choice(label: str, value: str, allowed: Sequence[str], path: str, lines: dict[str, int]) -> str:
    if value not in allowed:
        raise _fail("invalid_value", f"{label} `{value}` gibt es nicht", path, lines[label])
    return value


def _refs(value: str, path: str, line: int) -> tuple[str, ...]:
    text = clean(value)
    if text == "None" or not text:
        return ()
    found = references(value)
    if not found or ", ".join(f"`{ref}`" for ref in found) != text:
        raise _fail("invalid_value", f"Verweise stehen in Backticks, mehrere mit Komma: `{text}`", path, line)
    return found


def _day(values: dict[str, str], label: str, path: str, lines: dict[str, int]) -> str | None:
    if label not in values:
        return None
    text = clean(values[label])
    try:
        if not DAY.match(text):
            raise ValueError(text)
        date.fromisoformat(text)
    except ValueError:
        raise _fail("invalid_value", f"{label} `{text}` ist kein Tag (JJJJ-MM-TT)", path, lines[label]) from None
    return text


# --- Dokumente -----------------------------------------------------------------------------------------------------


def _documents(files: FileSet, items: list[_Decoded]) -> list[MirrorEntry]:
    by_ident = {d.block.ident: d.entry for d in items}
    docs: list[MirrorEntry] = []
    for path in sorted(files.files):
        parts = path.split("/")
        if len(parts) != 3 or parts[0] != "items":
            continue
        folder, name = parts[1], parts[2]
        match = DOCUMENT_NAME.match(name)
        if match is None:
            continue
        if match.group("label") != folder:
            raise _fail("file_label_mismatch", f"Datei `{name}` liegt im Ordner `{folder}`", path, 1)
        item = by_ident.get(folder)
        if item is None:
            continue  # ein Ordner ohne Eintrag in TODO.md oder archive.md: nichts zuzuordnen
        suffix = match.group("kind")  # `notes`, `spec` oder `spec_<thema>`: bleibt beim Typwechsel gleich
        text = files.files[path].text
        if suffix == "notes":
            # Die Titelzeile ist abgeleitet: das Schreiben erzeugt sie aus Label und Titel des Items, verglichen wird
            # sie nicht. So erscheint die Datei nach einem Typwechsel nicht als geändert, und eine abweichende alte
            # Titelzeile ist kein Konflikt; sie wird beim nächsten Schreiben erneuert.
            # Ebenso das Layout: die Datenbank hält Notes zerlegt und setzt sie in festem Layout zusammen (zusätzliche
            # Leerzeilen vor den Einträgen gehen verloren). Verglichen wird die Form, die die Datenbank liefern würde;
            # sonst bliebe ein Unterschied nur im Leerraum nach „Dateien“ + Sync ein Konflikt.
            content = without_title(assemble("", split(text)))
            fields: dict[str, Any] = {"content": content, "kind": "notes", "title": item.fields["title"]}
        else:
            fields = {"content": text, "kind": "spec"}
        refs = {"item": (folder,)}
        if item.uid is not None:
            docs.append(MirrorEntry(DOCUMENT_KIND, name, fields, refs, f"{item.uid}/{suffix}", source=(path, 1)))
        else:
            docs.append(MirrorEntry(DOCUMENT_KIND, None, fields, refs, None, f"{folder}/{suffix}", source=(path, 1)))
    return docs


# --- Regeln --------------------------------------------------------------------------------------------------------


def _check_rules(items: list[_Decoded], docs: list[MirrorEntry]) -> None:
    """Die Regeln des Backlog-Formats über die Einträge der Dateien; was nur die Datenbank wissen kann (frühere
    Labels), bleibt dem Teilnehmer."""
    keys = {d.block.ident: (d.entry.uid or f"new:{d.entry.placeholder}") for d in items}
    notes = {ref for doc in docs if doc.fields["kind"] == "notes" for ref in doc.refs["item"]}
    built: list[Item] = []
    where: dict[str, _Decoded] = {}
    for d in items:
        uid = keys[d.block.ident]
        where[uid] = d
        f = d.entry.fields
        parent = d.entry.refs.get("parent", ())
        built.append(
            Item(
                uid=uid,
                project_uid="",
                label=d.block.ident,
                type=next(t for t, k in KIND_BY_TYPE.items() if k == d.entry.kind),
                title=f["title"],
                status=f["status"],
                priority=f["priority"],
                area=f["area"],
                parent_uid=keys.get(parent[0], f"unknown:{parent[0]}") if parent else None,
                required_for_parent=f["required_for_parent"],
                goal=f["goal"],
                completion_criteria=f["completion_criteria"],
                summary=f["summary"],
                resolution=f["resolution"],
                created=date.min,
                position=0,
                revision=1,
                dependencies=tuple(keys.get(ref, f"unknown:{ref}") for ref in d.entry.refs.get("dependencies", ())),
                notes=(f"{d.block.ident}_notes.md",) if d.block.ident in notes else (),
            )
        )
    # Gelöschte Items zählen nicht (sie liegen im Papierkorb).
    live = [item for item in built if where[item.uid].entry.fields["deleted"] is None]
    rules = LifecycleRules()
    for violation in sorted(rules.violations(live)):
        if violation.code == "unknown_reference":
            continue  # das entscheidet die Datenbank (frühere Labels)
        if violation.code == "summary_required_with_notes":
            continue  # gilt für Änderungen in der Oberfläche; ein Spiegel mit Notizen ohne Kurzfassung bleibt lesbar
        labels = sorted(next(i.label for i in live if i.uid == uid) for uid in violation.related if uid in where)
        # Ein aktives Kind unter einem geschlossenen Parent wird bei dessen `Parent`-Zeile gemeldet, sonst beim Eintrag.
        at = where[violation.related[0]] if violation.code == "children_still_active" else where[violation.uid]
        parent_field = at.block.field("Parent") if violation.code == "children_still_active" else None
        line = parent_field.line if parent_field else at.block.line
        try:
            raise LifecycleViolation(violation.code, where[violation.uid].block.ident, labels)
        except LifecycleViolation as error:
            raise MirrorFormatError("rule_violation", error.message, file=at.path, line=line) from error

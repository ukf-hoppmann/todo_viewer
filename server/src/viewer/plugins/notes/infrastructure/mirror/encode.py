"""Einträge → Dateien für `notes/`: Notes und Dokumente als ganze Dateien, `topics.md` aus Zeilen neu aufgebaut."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from viewer.core.domain.files import Change, DeleteFile, FileSet, RenameFile, WriteFile
from viewer.core.domain.sync import MirrorEntry
from viewer.plugins.notes.infrastructure.mirror.decode import parse_topics
from viewer.plugins.notes.infrastructure.mirror.syntax import (
    COUNTERS_FILE,
    KIND_DOCUMENT,
    KIND_NOTE,
    KIND_TOPIC,
    TOPICS_FILE,
    display_target,
    escape,
)


def note_path(entry: MirrorEntry) -> str:
    return f"notes/{entry.label or entry.placeholder}.md"


def render_note(entry: MirrorEntry, project: str) -> str:
    """Die Datei einer Note: Kopf, Auslöser, Verknüpfungen, Langtext."""
    f, refs, extra = entry.fields, entry.refs, entry.extra
    lines = [f"# {entry.label or 'NEW'}"]
    if entry.uid is not None:
        lines.append(f"Uid: {entry.uid}")
    lines += [
        f"Summary: {f['summary']}",
        f"Status: {f['status']}",
        f"Topic: {refs['topic'][0] if refs.get('topic') else ''}".rstrip(),
        f"Review: {f['review_at'] or ''}".rstrip(),
        f"Mode: {f['mode']}",
        f"Created: {extra.get('created') or ''}".rstrip(),
        f"Updated: {extra.get('updated') or ''}".rstrip(),
        f"Archived: {'true' if f['archived'] else 'false'}",
        f"Deleted: {f['deleted_at'] or ''}".rstrip(),
    ]
    triggers: list[dict[str, Any]] = f["triggers"]
    if triggers:
        lines.append("Triggers:")
        targets = iter(refs.get("trigger_targets", ()))
        for trigger in triggers:
            if trigger["kind"] == "topic_date":
                lines.append("- topic_due")
                continue
            line = f"- event {display_target(next(targets, '?'), project)} {trigger['status']}"
            if trigger["fired_at"]:
                line += f" [fired {trigger['fired_at']}]"
            if trigger["already_met"]:
                line += " [already_met]"
            lines.append(line)
    links = [(role, token) for role in ("reference", "origin") for token in refs.get(role, ())]
    if links:
        lines.append("Links:")
        lines += [f"- {role} {display_target(token, project)}" for role, token in links]
    text = "\n".join(lines) + "\n"
    if f["body"]:
        text += "\n" + f["body"] + "\n"
    return text


def _topic_row(entry: MirrorEntry) -> str:
    f = entry.fields
    if entry.uid is None:
        return f"- NEW | {escape(f['name'])} | due={f['due_at'] or ''}".rstrip()
    return (
        f"- {entry.label} | {escape(f['name'])} | uid={entry.uid} | due={f['due_at'] or ''} | "
        f"created={entry.extra.get('created') or ''} | archived={f['archived_at'] or ''} | "
        f"deleted={f['deleted_at'] or ''}"
    )


def _token(entry: MirrorEntry) -> str:
    return str(entry.label) if entry.label else str(entry.placeholder)


def _topics_text(current: FileSet, upserts: Sequence[MirrorEntry], removed: Sequence[MirrorEntry]) -> str | None:
    """`topics.md` mit den Änderungen: Reihenfolge der Datei bleibt, neue Topics ans Ende ihres Parents."""
    existing = current.files.get(TOPICS_FILE)
    records = parse_topics(existing.text) if existing is not None else []
    gone = {e.uid or e.placeholder for e in removed}
    records = [r for r in records if (r.uid or r.placeholder) not in gone]
    for entry in upserts:
        position = next(
            (
                i
                for i, r in enumerate(records)
                if (entry.uid is not None and r.uid == entry.uid)
                or (entry.placeholder is not None and r.uid is None and r.placeholder == entry.placeholder)
            ),
            None,
        )
        if position is None:
            records.append(entry)
        else:
            records[position] = entry
    if not records:
        return None
    children: dict[str | None, list[MirrorEntry]] = {}
    tokens = {_token(r) for r in records}
    for record in records:
        parent = record.refs["parent"][0] if record.refs.get("parent") else None
        children.setdefault(parent if parent in tokens else None, []).append(record)
    lines: list[str] = []

    def walk(parent: str | None, depth: int, seen: frozenset[str]) -> None:
        for record in children.get(parent, []):
            token = _token(record)
            if token in seen:
                continue
            lines.append("  " * depth + _topic_row(record))
            walk(token, depth + 1, seen | {token})

    walk(None, 0, frozenset())
    return "\n".join(lines) + "\n"


def encode(
    upserts: Sequence[MirrorEntry], removed: Sequence[MirrorEntry], current: FileSet, project: str
) -> list[Change]:
    changes: list[Change] = []
    notes = [e for e in upserts if e.kind == KIND_NOTE]
    for entry in notes:
        path = note_path(entry)
        changes.append(WriteFile(path, render_note(entry, project)))
        old = f"notes/{entry.placeholder}.md" if entry.placeholder and entry.label else None
        if old is not None and old != path and old in current.files:
            changes.append(DeleteFile(old))
    for entry in removed:
        if entry.kind == KIND_NOTE and note_path(entry) in current.files:
            changes.append(DeleteFile(note_path(entry)))
    changes.extend(_document_changes([e for e in upserts if e.kind == KIND_DOCUMENT], removed, current))
    topics = [e for e in upserts if e.kind == KIND_TOPIC]
    gone_topics = [e for e in removed if e.kind == KIND_TOPIC]
    if topics or gone_topics:
        text = _topics_text(current, topics, gone_topics)
        if text is not None:
            changes.append(WriteFile(TOPICS_FILE, text))
        elif TOPICS_FILE in current.files:
            changes.append(DeleteFile(TOPICS_FILE))
    if changes and COUNTERS_FILE in current.files:
        changes.append(DeleteFile(COUNTERS_FILE))  # `counters.md` entfällt in Version 2
    return changes


def _document_changes(upserts: Sequence[MirrorEntry], removed: Sequence[MirrorEntry], current: FileSet) -> list[Change]:
    changes: list[Change] = []
    for entry in upserts:
        path = f"notes/{entry.label}"
        content = entry.fields["content"]
        if entry.placeholder:
            stem, suffix = entry.placeholder.split("/", 1)
            old = f"notes/{stem}_{suffix}.md"
            if old in current.files and old != path:
                changes.append(RenameFile(old, path))
                if current.files[old].text != content:
                    changes.append(WriteFile(path, content))
                continue
        existing = current.files.get(path)
        if existing is None or existing.text != content:
            changes.append(WriteFile(path, content))
    for entry in removed:
        path = f"notes/{entry.label}"
        if entry.kind == KIND_DOCUMENT and path in current.files:
            changes.append(DeleteFile(path))
    return changes

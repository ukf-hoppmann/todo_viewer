"""Einträge → `alarms.md`: die Datei entsteht ganz aus den Einträgen, die Einleitung bleibt."""

from __future__ import annotations

from collections.abc import Sequence

from viewer.core.domain.files import Change, FileSet, WriteFile
from viewer.core.domain.sync import MirrorEntry
from viewer.plugins.alarms.infrastructure.mirror.decode import decode
from viewer.plugins.alarms.infrastructure.mirror.syntax import (
    ALARMS_FILE,
    NO_ENTRIES,
    REPEAT_WORDS,
    SECTION,
    TEMPLATE,
)


def render_entry(entry: MirrorEntry, project: str) -> list[str]:
    f, extra = entry.fields, entry.extra
    head = f"- `{entry.label or entry.placeholder}`"
    lines = [f"{head} **{f['text']}**" if f["text"] else head]
    if entry.uid is not None:
        lines.append(f"  - Uid: {entry.uid}.")
    lines.append(f"  - At: {f['at']}.")
    if f.get("repeat", "none") != "none":
        lines.append(f"  - Repeat: {REPEAT_WORDS[f['repeat']]}.")
        lines.append(f"  - Series from: {f['series_from']}.")
    targets = entry.refs.get("target")
    lines.append(f"  - Target: {', '.join(f'`{t}`' for t in targets) if targets else 'None'}.")
    lines.append(f"  - Status: {f['status']}.")
    if f["snoozed_until"]:
        lines.append(f"  - Snoozed until: {f['snoozed_until']}.")
    if f.get("done_at"):
        lines.append(f"  - Done at: {f['done_at']}.")
    if extra.get("created"):
        lines.append(f"  - Created: {extra['created']}.")
    if f["deleted"]:
        lines.append(f"  - Deleted: {f['deleted']}.")
    return lines


def _key(entry: MirrorEntry) -> str:
    return entry.uid or f"new:{entry.placeholder}"


def encode(
    upserts: Sequence[MirrorEntry], removed: Sequence[MirrorEntry], current: FileSet, project: str
) -> list[Change]:
    if not upserts and not removed:
        return []
    existing = current.files.get(ALARMS_FILE)
    records = decode(current, project) if existing is not None else []
    gone = {_key(e) for e in removed}
    records = [r for r in records if _key(r) not in gone]
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
    preamble = TEMPLATE
    if existing is not None:
        lines = existing.text.split("\n")
        start = next((i for i, text in enumerate(lines) if SECTION.match(text)), None)
        if start is not None:
            preamble = "\n".join(lines[: start + 1]) + "\n"
    body: list[str] = []
    for record in records:
        body += ["", *render_entry(record, project)]
    text = preamble + ("\n".join(body) + "\n" if body else f"\n{NO_ENTRIES}\n")
    if existing is not None and existing.text == text:
        return []
    return [WriteFile(ALARMS_FILE, text)]

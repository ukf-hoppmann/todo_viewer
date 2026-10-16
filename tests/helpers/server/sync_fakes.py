"""Fakes für Tests des Sync: ein einfaches Dateiformat und im Speicher gehaltene Ports.

Dateiformat (`items.md`), eine Zeile je Eintrag:
`- <LABEL oder NEW-name> | <uid oder leer> | <kind> | <titel> | parent=<label> | deps=<label>,<label>`
"""

from __future__ import annotations

import itertools
import uuid
from collections.abc import Collection, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path

from viewer.core.application.ports import Transaction
from viewer.core.application.sync import MirrorConfig, SyncChanges
from viewer.core.domain.files import Change, FileSet, WriteFile
from viewer.core.domain.sync import MirrorEntry, MirrorFormatError

FILE = "items.md"
KINDS = {"task": "TASK", "story": "STORY", "epic": "EPIC"}


class LineCodec:
    patterns = (FILE,)

    def decode(self, files: FileSet) -> list[MirrorEntry]:
        entry = files.files.get(FILE)
        if entry is None:
            return []
        result: list[MirrorEntry] = []
        for number, line in enumerate(entry.text.splitlines(), start=1):
            if not line.startswith("- "):
                continue
            result.append(self._parse(line, number))
        return result

    @staticmethod
    def _parse(line: str, number: int) -> MirrorEntry:
        parts = [p.strip() for p in line[2:].split(" | ")]
        if len(parts) != 6:
            raise MirrorFormatError("invalid_value", "Zeile braucht sechs Felder", file=FILE, line=number)
        label, uid, kind, title, parent, deps = parts
        if kind not in KINDS:
            raise MirrorFormatError("invalid_value", f"unbekannter Typ {kind}", file=FILE, line=number)
        refs: dict[str, tuple[str, ...]] = {}
        parent = parent.removeprefix("parent=")
        if parent:
            refs["parent"] = (parent,)
        deps = deps.removeprefix("deps=")
        if deps:
            refs["deps"] = tuple(deps.split(","))
        is_new = not uid
        return MirrorEntry(
            kind=kind,
            label=None if is_new else label,
            fields={"title": title},
            refs=refs,
            uid=uid or None,
            placeholder=label if is_new else None,
        )

    def encode(
        self, upserts: Sequence[MirrorEntry], removed: Sequence[MirrorEntry], current: FileSet
    ) -> Sequence[Change]:
        text = current.files[FILE].text if FILE in current.files else "# Items\n\n"
        lines = text.splitlines()
        drop_uids = {e.uid for e in removed}
        by_uid = {e.uid: e for e in upserts}
        by_placeholder = {e.placeholder: e for e in upserts if e.placeholder}
        written: set[str | None] = set()
        out: list[str] = []
        for number, line in enumerate(lines, start=1):
            if not line.startswith("- "):
                out.append(line)
                continue
            old = self._parse(line, number)
            if old.uid in drop_uids:
                continue
            replacement = by_uid.get(old.uid) if old.uid else by_placeholder.get(old.placeholder)
            if replacement is not None:
                out.append(self._render(replacement))
                written.add(replacement.uid)
            else:
                out.append(line)
        for entry in upserts:
            if entry.uid not in written:
                out.append(self._render(entry))
        return [WriteFile(FILE, "\n".join(out) + "\n")]

    @staticmethod
    def _render(entry: MirrorEntry) -> str:
        parent = ",".join(entry.refs.get("parent", ()))
        deps = ",".join(entry.refs.get("deps", ()))
        return f"- {entry.label} | {entry.uid} | {entry.kind} | {entry.fields['title']} | parent={parent} | deps={deps}"


class MemoryParticipant:
    """Datenbankseite im Speicher: Einträge, Label-Zähler und Label-Historie."""

    def __init__(self) -> None:
        self.rows: dict[str, MirrorEntry] = {}
        self.history: dict[str, str] = {}  # altes Label → aktuelles Label
        self.counters: dict[str, int] = {}
        self.applied: list[SyncChanges] = []

    def add(self, uid: str, kind: str, title: str, label: str | None = None, **refs: tuple[str, ...]) -> MirrorEntry:
        label = label or self._next_label(kind)
        entry = MirrorEntry(kind, label, {"title": title}, refs, uid)
        self.rows[uid] = entry
        return entry

    def _next_label(self, kind: str) -> str:
        prefix = KINDS[kind]
        self.counters[prefix] = self.counters.get(prefix, 0) + 1
        return f"{prefix}-{self.counters[prefix]:03d}"

    def load(self, project: str) -> list[MirrorEntry]:
        return list(self.rows.values())

    def resolve_labels(self, project: str, labels: Collection[str]) -> Mapping[str, str]:
        known = {e.label: e.label for e in self.rows.values() if e.label}
        known.update(self.history)
        return {label: known[label] for label in labels if label in known}

    def assign_labels(self, project: str, entries: Sequence[MirrorEntry], tx: Transaction) -> Mapping[str, str]:
        return {str(e.placeholder): self._next_label(e.kind) for e in entries}

    def apply(self, project: str, changes: SyncChanges, tx: Transaction) -> None:
        self.applied.append(changes)
        for entry in changes.created:
            self.rows[str(entry.uid)] = entry
        for entry in changes.updated:
            self.rows[str(entry.uid)] = replace(entry, label=self.rows[str(entry.uid)].label)
        for entry in changes.deleted:
            self.rows.pop(str(entry.uid), None)


@dataclass
class MemoryProjects:
    configs: dict[str, MirrorConfig] = field(default_factory=dict)

    def config(self, project: str) -> MirrorConfig | None:
        return self.configs.get(project)

    def auto_sync_projects(self) -> list[str]:
        return [p for p, c in self.configs.items() if c.auto_sync]


class MemoryStateStore:
    def __init__(self) -> None:
        self.hashes: dict[str, dict[str, str]] = {}

    def load(self, project: str) -> dict[str, str]:
        return dict(self.hashes.get(project, {}))

    def save(self, project: str, hashes: Mapping[str, str], at: datetime) -> None:
        self.hashes.setdefault(project, {}).update(hashes)

    def forget(self, project: str, uids: Collection[str]) -> None:
        for uid in uids:
            self.hashes.get(project, {}).pop(uid, None)


class SequentialIds:
    def __init__(self) -> None:
        self._counter = itertools.count(1)

    def new_uid(self) -> str:
        return str(uuid.UUID(int=next(self._counter)))


class TransactionRecorder:
    def __init__(self) -> None:
        self.committed = 0

    @contextmanager
    def transaction(self) -> Iterator[Transaction]:
        yield object()  # type: ignore[misc]
        self.committed += 1


class BackupRecorder:
    def __init__(self) -> None:
        self.reasons: list[str] = []

    def create(self, reason: str) -> Path:
        self.reasons.append(reason)
        return Path(f"/backups/{reason}.db")


class ScheduleRecorder:
    def __init__(self) -> None:
        self.appointments: dict[str, tuple[datetime, object] | None] = {}

    def schedule(self, owner: str, at: datetime | None, callback: object) -> None:  # type: ignore[override]
        self.appointments[owner] = (at, callback) if at else None


class EventRecorder:
    def __init__(self) -> None:
        self.events: list = []  # type: ignore[type-arg]

    def publish(self, event) -> None:  # type: ignore[no-untyped-def]
        self.events.append(event)

    def subscribe(self, topic, handler):  # type: ignore[no-untyped-def]
        return lambda: None

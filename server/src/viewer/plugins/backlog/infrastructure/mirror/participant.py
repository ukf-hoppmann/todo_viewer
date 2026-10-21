"""Datenbank ⇄ Einträge für den Spiegel: liest Items und Dokumente, vergibt Labels, schreibt Änderungen."""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping, Sequence
from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any

from viewer.core.application.ports import Clock, Database, Transaction
from viewer.core.application.sync import SyncChanges
from viewer.core.domain.sync import MirrorEntry, MirrorFormatError
from viewer.plugins.backlog.application.ports import (
    Document,
    DocumentRepository,
    ItemRepository,
    Notes,
    NotesRepository,
)
from viewer.plugins.backlog.domain.lifecycle import LifecycleRules, LifecycleViolation
from viewer.plugins.backlog.domain.model import KIND_BY_TYPE, TYPE_BY_KIND, Item
from viewer.plugins.backlog.domain.notes import assemble, split, title_of, without_title
from viewer.plugins.backlog.infrastructure.mirror.decode import DOCUMENT_KIND
from viewer.plugins.backlog.infrastructure.mirror.syntax import TODO_FILE


def _day(value: datetime | None) -> str | None:
    return value.astimezone(UTC).date().isoformat() if value is not None else None


def _suffix(label: str, name: str) -> str | None:
    """`STORY-001_spec_Teil.md` → `spec_Teil`; `None`, wenn der Name nicht dem Label folgt."""
    match = re.fullmatch(rf"{re.escape(label)}_(notes|spec(?:_[A-Za-z0-9-]+)?)\.md", name)
    return match.group(1) if match else None


def _items(entries: Sequence[MirrorEntry]) -> list[MirrorEntry]:
    return [e for e in entries if e.kind != DOCUMENT_KIND]


def _documents(entries: Sequence[MirrorEntry]) -> list[MirrorEntry]:
    return [e for e in entries if e.kind == DOCUMENT_KIND]


class BacklogParticipant:
    def __init__(
        self,
        items: ItemRepository,
        documents: DocumentRepository,
        notes: NotesRepository,
        registry: Any,
        database: Database,
        clock: Clock,
    ) -> None:
        self._items = items
        self._documents = documents
        self._notes = notes
        self._registry = registry
        self._database = database
        self._clock = clock
        self._rules = LifecycleRules()

    # --- Lesen ----------------------------------------------------------------------------------------------------

    def load(self, project: str) -> list[MirrorEntry]:
        with self._database.transaction() as tx:
            items = self._items.list_in(tx, [project], include_deleted=True)
            label = {item.uid: item.label for item in items}
            entries = [self._entry(item, label) for item in items]
            for item in items:
                notes = self._notes.get(tx, item.uid)
                documents: list[tuple[str, dict[str, Any]]] = []
                if notes is not None:
                    content = without_title(assemble(title_of(item), notes.parts))
                    documents.append((notes.name, {"content": content, "kind": "notes", "title": item.title}))
                for document in self._documents.list_for(tx, item.uid):
                    documents.append((document.name, {"content": document.content, "kind": document.kind}))
                for name, fields in documents:
                    suffix = _suffix(item.label, name)
                    if suffix is None:
                        continue
                    entries.append(
                        MirrorEntry(DOCUMENT_KIND, name, fields, {"item": (item.label,)}, f"{item.uid}/{suffix}")
                    )
        return entries

    @staticmethod
    def _entry(item: Item, label: Mapping[str, str]) -> MirrorEntry:
        fields = {
            "title": item.title,
            "status": item.status,
            "priority": item.priority,
            "area": item.area,
            "created": item.created.isoformat(),
            "goal": item.goal,
            "completion_criteria": item.completion_criteria,
            "summary": item.summary,
            "resolution": item.resolution,
            "required_for_parent": item.required_for_parent,
            "deleted": _day(item.deleted_at),
        }
        refs: dict[str, tuple[str, ...]] = {}
        if item.parent_uid:
            refs["parent"] = (label.get(item.parent_uid, item.parent_uid),)
        if item.dependencies:
            refs["dependencies"] = tuple(sorted(label.get(uid, uid) for uid in item.dependencies))
        return MirrorEntry(KIND_BY_TYPE[item.type].lower(), item.label, fields, refs, item.uid)

    def resolve_labels(self, project: str, labels: Collection[str]) -> Mapping[str, str]:
        found: dict[str, str] = {}
        with self._database.transaction() as tx:
            for label in labels:
                element = self._registry.find_by_label(tx, project, label)
                if element is not None:
                    found[label] = element.label
        return found

    def assign_labels(
        self, project: str, entries: Sequence[MirrorEntry], tx: Transaction, taken: Collection[str] = ()
    ) -> Mapping[str, str]:
        self._registry.note_labels(tx, project, list(taken))  # Labels, die dieser Lauf aus den Dateien mitbringt
        result: dict[str, str] = {}
        for entry in entries:
            if entry.kind != DOCUMENT_KIND:
                result[str(entry.placeholder)] = self._registry.reserve_label(tx, project, entry.kind)
        for entry in entries:
            if entry.kind == DOCUMENT_KIND:
                placeholder = str(entry.placeholder)
                suffix = placeholder.split("/", 1)[1]
                owner = entry.refs["item"][0]
                result[placeholder] = f"{result.get(owner, owner)}_{suffix}.md"
        return result

    # --- Schreiben ------------------------------------------------------------------------------------------------

    def apply(self, project: str, changes: SyncChanges, tx: Transaction) -> None:
        before = [i for i in self._items.list_in(tx, [project]) if i.deleted_at is None]
        existing = {i.uid: i for i in self._items.list_in(tx, [project], include_deleted=True)}
        created, updated, deleted = _items(changes.created), _items(changes.updated), _items(changes.deleted)

        for entry in created:
            self._create(tx, project, entry)
        by_label = {str(e.label): str(e.uid) for e in created}
        returning: list[Item] = []
        for entry in [*created, *updated]:
            item = self._write(tx, project, entry, existing.get(str(entry.uid)), by_label)
            if entry in created or (existing.get(str(entry.uid)) and existing[str(entry.uid)].deleted_at is not None):
                returning.append(item)
        for entry in deleted:
            current = existing.get(str(entry.uid))
            if current is not None and current.deleted_at is None:
                self._registry.mark_deleted(tx, current.uid)
        self._write_documents(
            tx, project, _documents(changes.created), _documents(changes.updated), _documents(changes.deleted), by_label
        )
        self._check(tx, project, before, returning, [*created, *updated])

    def _create(self, tx: Transaction, project: str, entry: MirrorEntry) -> None:
        f = entry.fields
        self._registry.register_as(tx, project, entry.kind, str(entry.uid), str(entry.label), f["title"])
        created = date.fromisoformat(f["created"]) if f["created"] else self._clock.now().date()
        siblings = self._items.siblings(tx, project, None)
        self._items.insert(
            tx,
            Item(
                uid=str(entry.uid),
                project_uid=project,
                label=str(entry.label),
                type=TYPE_BY_KIND[entry.kind],
                title=f["title"],
                status=f["status"],
                priority=f["priority"],
                area=f["area"],
                parent_uid=None,
                required_for_parent=None,
                goal=f["goal"],
                completion_criteria=f["completion_criteria"],
                summary=f["summary"],
                resolution=f["resolution"],
                created=created,
                position=max((s.position for s in siblings), default=-1) + 1,
                revision=1,
            ),
        )

    def _write(
        self, tx: Transaction, project: str, entry: MirrorEntry, current: Item | None, new: Mapping[str, str]
    ) -> Item:
        """Setzt Felder und Verweise des Items auf den Stand des Eintrags (das Item gibt es schon)."""
        f = entry.fields
        stored = self._items.get(tx, str(entry.uid))
        assert stored is not None
        parent = (
            self._uid_of(tx, project, entry, entry.refs["parent"][0], new, "Parent") if "parent" in entry.refs else None
        )
        dependencies = tuple(
            self._uid_of(tx, project, entry, ref, new, "Dependencies") for ref in entry.refs.get("dependencies", ())
        )
        item = replace(
            stored,
            title=f["title"],
            status=f["status"],
            priority=f["priority"],
            area=f["area"],
            goal=f["goal"],
            completion_criteria=f["completion_criteria"],
            summary=f["summary"],
            resolution=f["resolution"],
            required_for_parent=f["required_for_parent"],
            parent_uid=parent,
            dependencies=tuple(sorted(dependencies)),
            created=date.fromisoformat(f["created"]) if f["created"] else stored.created,
        )
        if current is not None:  # ein vorhandenes Item: die Revision zieht mit
            item = replace(item, revision=self._registry.bump_revision(tx, item.uid, current.revision))
            if item.title != current.title:
                self._registry.set_title(tx, item.uid, item.title)
        self._items.update(tx, item)
        day = f["deleted"]
        if day and (current is None or current.deleted_at is None):
            self._registry.mark_deleted(tx, item.uid, datetime.fromisoformat(f"{day}T00:00:00+00:00"))
        elif not day and current is not None and current.deleted_at is not None:
            self._registry.restore(tx, item.uid)
        return item

    def _uid_of(
        self, tx: Transaction, project: str, entry: MirrorEntry, label: str, new: Mapping[str, str], field: str = ""
    ) -> str:
        if label in new:
            return new[label]
        element = self._registry.find_by_label(tx, project, label)
        if element is None:
            file, header_line = entry.source or (TODO_FILE, 1)
            line = entry.source_lines.get(field, header_line)
            raise MirrorFormatError(
                "unknown_reference",
                f"`{label}` gab es im Projekt nie (verwendet von `{entry.label}`)",
                file=file,
                line=line,
            )
        return str(element.uid)

    def _write_documents(
        self,
        tx: Transaction,
        project: str,
        created: Sequence[MirrorEntry],
        updated: Sequence[MirrorEntry],
        deleted: Sequence[MirrorEntry],
        new: Mapping[str, str],
    ) -> None:
        now = self._clock.now()
        for entry in (*created, *updated):
            item_uid = self._uid_of(tx, project, entry, entry.refs["item"][0], new)
            name = str(entry.label)
            if entry.fields["kind"] == "notes":
                self._write_notes(tx, item_uid, name, entry.fields["content"], now)
                continue
            existing = self._documents.get(tx, item_uid, name)
            if existing is None:
                self._documents.insert(
                    tx, Document(item_uid, name, entry.fields["kind"], entry.fields["content"], 1, now)
                )
            else:
                self._documents.update(tx, item_uid, name, entry.fields["content"], existing.revision, now)
        for entry in deleted:
            element = self._registry.find_by_label(tx, project, entry.refs["item"][0])
            if element is None:
                continue
            notes = self._notes.get(tx, element.uid)
            if notes is not None and notes.name == str(entry.label):
                self._notes.delete(tx, element.uid)
            else:
                self._documents.delete(tx, element.uid, str(entry.label))

    def _write_notes(self, tx: Transaction, item_uid: str, name: str, content: str, now: datetime) -> None:
        """Die Datei ist im Spiegel der ganze Stand: der Stempel kommt aus ihr, ohne `## State` ist der Kopf leer."""
        parts = split(content)
        existing = self._notes.get(tx, item_uid)
        if existing is None:
            self._notes.insert(tx, Notes(item_uid, name, parts, 1, 1, now))
            return
        changed = (parts.state, parts.stamp) != (existing.parts.state, existing.parts.stamp)
        self._notes.save(tx, item_uid, parts, expected=existing.revision, state_changed=changed, at=now)

    def _check(
        self, tx: Transaction, project: str, before: list[Item], returning: list[Item], entries: Sequence[MirrorEntry]
    ) -> None:
        """Die Regeln des Backlog-Formats über das Projekt nach der Änderung; ein Verstoß bricht den Sync ab."""
        after = [i for i in self._items.list_in(tx, [project]) if i.deleted_at is None]
        back = {i.uid for i in returning}
        try:
            self._rules.check_change(before, after, [i for i in after if i.uid in back])
        except LifecycleViolation as error:
            source = next((e.source for e in entries if e.label == error.details.get("item")), None)
            file, line = source or (TODO_FILE, 1)
            raise MirrorFormatError("rule_violation", error.message, file=file, line=line) from error

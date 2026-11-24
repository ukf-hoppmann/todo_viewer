"""Datenbank ⇄ Einträge für den Spiegel: liest Topics, Memos und Dokumente, vergibt Labels, schreibt Änderungen."""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping, Sequence
from dataclasses import replace
from datetime import datetime
from typing import Any

from viewer.core.application.ports import Transaction
from viewer.core.application.sync import SyncChanges
from viewer.core.domain.sync import MirrorEntry, MirrorFormatError
from viewer.plugins.memos.application.deps import Deps
from viewer.plugins.memos.application.ports import Document
from viewer.plugins.memos.domain.documents import document_kind
from viewer.plugins.memos.domain.due import Trigger
from viewer.plugins.memos.domain.model import Memo, Topic
from viewer.plugins.memos.infrastructure.mirror.syntax import (
    KIND_DOCUMENT,
    KIND_MEMO,
    KIND_TOPIC,
    TOPICS_FILE,
    format_time,
    to_datetime,
)

_LABEL = re.compile(r"^[A-Z]+-\d+$")


def _suffix(label: str, name: str) -> str | None:
    """`MEMO-001_spec_Teil.md` → `spec_Teil`; `None`, wenn der Name nicht dem Label folgt."""
    match = re.fullmatch(rf"{re.escape(label)}_(notes|spec(?:_[A-Za-z0-9-]+)?)\.md", name)
    return match.group(1) if match else None


def _time(value: str | None) -> datetime | None:
    return to_datetime(value) if value else None


class MemosParticipant:
    def __init__(self, deps: Deps, project_store: Any) -> None:
        self._d = deps
        self._projects = project_store

    # --- Lesen ----------------------------------------------------------------------------------------------------

    def load(self, project: str) -> list[MirrorEntry]:
        d = self._d
        with d.database.transaction() as tx:
            names = {p.uid: p.name for p in self._projects.list(tx, include_deleted=True)}
            topics = d.topics.list_in(tx, [project], include_deleted=True)
            memos = d.memos.list_in(tx, [project], include_deleted=True)
            label = {t.uid: t.label for t in topics} | {n.uid: n.label for n in memos}
            triggers = d.triggers.for_memos(tx, [n.uid for n in memos])
            entries = [self._topic_entry(tx, topic, label) for topic in topics]
            for memo in memos:
                entries.append(self._memo_entry(tx, project, memo, label, triggers.get(memo.uid, []), names))
            for memo in memos:
                for document in d.documents.list_for(tx, memo.uid):
                    suffix = _suffix(memo.label, document.name)
                    if suffix is None:
                        continue
                    fields = {"content": document.content, "kind": document.kind}
                    entries.append(
                        MirrorEntry(
                            KIND_DOCUMENT, document.name, fields, {"memo": (memo.label,)}, f"{memo.uid}/{suffix}"
                        )
                    )
        return entries

    def _topic_entry(self, tx: Transaction, topic: Topic, label: Mapping[str, str]) -> MirrorEntry:
        element = self._d.registry.get(tx, topic.uid)
        fields = {
            "name": topic.name,
            "due_at": format_time(topic.due_at) or None,
            "archived_at": format_time(topic.archived_at) or None,
            "deleted_at": format_time(topic.deleted_at) or None,
        }
        refs = {"parent": (label.get(topic.parent_uid, topic.parent_uid),)} if topic.parent_uid else {}
        extra = {"created": format_time(element.created_at) if element else None}
        return MirrorEntry(
            KIND_TOPIC, topic.label, fields, refs, topic.uid, extra=extra, trashed=topic.deleted_at is not None
        )

    def _token(self, tx: Transaction, project: str, uid: str, names: Mapping[str, str]) -> str:
        element = self._d.registry.get(tx, uid)
        if element is None:
            return uid
        if element.project_uid == project:
            return str(element.label)
        return f"{names.get(element.project_uid, element.project_uid)}:{element.label}"

    def _memo_entry(
        self,
        tx: Transaction,
        project: str,
        memo: Memo,
        label: Mapping[str, str],
        triggers: Sequence[Trigger],
        names: Mapping[str, str],
    ) -> MirrorEntry:
        d = self._d
        element = d.registry.get(tx, memo.uid)
        fields = {
            "summary": memo.summary,
            "status": memo.status,
            "review_at": format_time(memo.review_at) or None,
            "mode": memo.trigger_mode,
            "archived": memo.archived,
            "deleted_at": format_time(memo.deleted_at) or None,
            "body": (memo.body or "").rstrip("\n"),
            "triggers": [
                {
                    "kind": t.kind,
                    "status": t.status if t.kind == "event" else None,
                    "fired_at": format_time(t.fired_at) or None,
                    "already_met": t.already_met,
                }
                for t in triggers
            ],
        }
        refs: dict[str, tuple[str, ...]] = {}
        if memo.topic_uid:
            refs["topic"] = (label.get(memo.topic_uid, memo.topic_uid),)
        by_role: dict[str, list[str]] = {"reference": [], "origin": []}
        for view in d.links.outgoing(tx, memo.uid):
            if view.link.role in by_role:
                by_role[view.link.role].append(self._token(tx, project, view.link.to_uid, names))
        for role, tokens in by_role.items():
            if tokens:
                refs[role] = tuple(sorted(tokens))
        targets = [
            self._token(tx, project, t.target_uid, names) for t in triggers if t.kind == "event" and t.target_uid
        ]
        if targets:
            refs["trigger_targets"] = tuple(targets)
        extra = {
            "created": format_time(element.created_at) if element else None,
            "updated": format_time(element.updated_at) if element else None,
        }
        trashed = memo.deleted_at is not None
        return MirrorEntry(KIND_MEMO, memo.label, fields, refs, memo.uid, extra=extra, trashed=trashed)

    def resolve_labels(self, project: str, labels: Collection[str]) -> Mapping[str, str]:
        found: dict[str, str] = {}
        with self._d.database.transaction() as tx:
            by_name = {p.name: p.uid for p in self._projects.list(tx)}
            for token in labels:
                qualifier, separator, bare = token.rpartition(":")
                if not separator:
                    qualifier, bare = "", token
                if not _LABEL.match(bare):
                    continue
                target = by_name.get(qualifier) if qualifier else project
                if target is None:
                    continue
                element = self._d.registry.find_by_label(tx, target, bare)
                if element is not None:
                    found[token] = f"{qualifier}:{element.label}" if qualifier else str(element.label)
        return found

    def assign_labels(
        self, project: str, entries: Sequence[MirrorEntry], tx: Transaction, taken: Collection[str] = ()
    ) -> Mapping[str, str]:
        registry = self._d.registry
        registry.note_labels(tx, project, list(taken))
        result: dict[str, str] = {}
        for entry in entries:
            if entry.kind != KIND_DOCUMENT:
                result[str(entry.placeholder)] = registry.reserve_label(
                    tx, project, "topic" if entry.kind == KIND_TOPIC else "memo"
                )
        for entry in entries:
            if entry.kind == KIND_DOCUMENT:
                placeholder = str(entry.placeholder)
                suffix = placeholder.split("/", 1)[1]
                owner = entry.refs["memo"][0]
                result[placeholder] = f"{result.get(owner, owner)}_{suffix}.md"
        return result

    # --- Schreiben ------------------------------------------------------------------------------------------------

    def apply(self, project: str, changes: SyncChanges, tx: Transaction) -> None:
        d = self._d
        created = {str(e.label): str(e.uid) for e in (*changes.created, *changes.updated) if e.kind != KIND_DOCUMENT}
        topics = [e for e in (*changes.created, *changes.updated) if e.kind == KIND_TOPIC]
        memos = [e for e in (*changes.created, *changes.updated) if e.kind == KIND_MEMO]
        new_uids = {str(e.uid) for e in changes.created}
        for entry in [e for e in topics if str(e.uid) in new_uids]:
            f = entry.fields
            d.registry.register_as(tx, project, "topic", str(entry.uid), str(entry.label), f["name"])
            d.topics.insert(tx, Topic(str(entry.uid), project, str(entry.label), f["name"], None, None, None, False, 1))
        for entry in topics:
            self._write_topic(tx, project, entry, created, str(entry.uid) in new_uids)
        for entry in [e for e in memos if str(e.uid) in new_uids]:
            d.registry.register_as(tx, project, "memo", str(entry.uid), str(entry.label), entry.fields["summary"])
            d.memos.insert(
                tx,
                Memo(
                    str(entry.uid),
                    project,
                    str(entry.label),
                    entry.fields["summary"],
                    None,
                    "waiting",
                    None,
                    None,
                    "any",
                    False,
                    1,
                ),
            )
        for entry in memos:
            self._write_memo(tx, project, entry, created, str(entry.uid) in new_uids)
        self._write_documents(tx, project, changes, created)
        for entry in changes.deleted:
            if entry.kind == KIND_DOCUMENT:
                continue
            element = d.registry.get(tx, str(entry.uid))
            if element is not None and element.deleted_at is None:
                d.registry.mark_deleted(tx, element.uid)

    def _write_topic(
        self, tx: Transaction, project: str, entry: MirrorEntry, new: Mapping[str, str], is_new: bool
    ) -> None:
        d = self._d
        f = entry.fields
        stored = d.topics.get(tx, str(entry.uid))
        assert stored is not None
        parent = (
            self._uid_of(tx, project, entry, entry.refs["parent"][0], new, "parent")
            if entry.refs.get("parent")
            else None
        )
        topic = replace(
            stored, name=f["name"], parent_uid=parent, due_at=_time(f["due_at"]), archived_at=_time(f["archived_at"])
        )
        if not is_new:
            topic = replace(topic, revision=d.registry.bump_revision(tx, topic.uid, stored.revision))
            if topic.name != stored.name:
                d.registry.set_title(tx, topic.uid, topic.name)
        d.topics.update(tx, topic)
        self._set_deleted(tx, topic.uid, f["deleted_at"])

    def _write_memo(
        self, tx: Transaction, project: str, entry: MirrorEntry, new: Mapping[str, str], is_new: bool
    ) -> None:
        d = self._d
        f = entry.fields
        stored = d.memos.get(tx, str(entry.uid))
        assert stored is not None
        topic = (
            self._uid_of(tx, project, entry, entry.refs["topic"][0], new, "topic") if entry.refs.get("topic") else None
        )
        memo = replace(
            stored,
            summary=f["summary"],
            body=f["body"] or None,
            status=f["status"],
            topic_uid=topic,
            review_at=_time(f["review_at"]),
            trigger_mode=f["mode"],
            archived=bool(f["archived"]),
        )
        if not is_new:
            memo = replace(memo, revision=d.registry.bump_revision(tx, memo.uid, stored.revision))
            if memo.summary != stored.summary:
                d.registry.set_title(tx, memo.uid, memo.summary)
        d.memos.update(tx, memo)
        self._set_deleted(tx, memo.uid, f["deleted_at"])
        self._write_links(tx, project, entry, memo.uid, new)

    def _set_deleted(self, tx: Transaction, uid: str, deleted_at: str | None) -> None:
        registry = self._d.registry
        element = registry.get(tx, uid)
        if element is None:
            return
        if deleted_at and element.deleted_at is None:
            registry.mark_deleted(tx, uid, to_datetime(deleted_at))
        elif not deleted_at and element.deleted_at is not None:
            registry.restore(tx, uid)

    def _write_links(self, tx: Transaction, project: str, entry: MirrorEntry, uid: str, new: Mapping[str, str]) -> None:
        """Verknüpfungen und Auslöser des Memos auf den Stand des Eintrags bringen."""
        d = self._d
        wanted: set[tuple[str, str]] = set()
        for role in ("reference", "origin"):
            for token in entry.refs.get(role, ()):
                target = self._uid_of(tx, project, entry, token, new, f"{role}:{token}")
                if target == uid:
                    file, line = entry.source or (TOPICS_FILE, 1)
                    raise MirrorFormatError(
                        "invalid_value", f"`{entry.label}` verweist auf sich selbst", file=file, line=line
                    )
                wanted.add((role, target))
        trigger_targets = [
            self._uid_of(tx, project, entry, token, new, f"trigger_targets:{token}")
            for token in entry.refs.get("trigger_targets", ())
        ]
        wanted |= {("trigger", target) for target in trigger_targets}
        have = {(v.link.role, v.link.to_uid): v.link.uid for v in d.links.outgoing(tx, uid)}
        for key, link_uid in have.items():
            if key not in wanted:
                d.links.remove(tx, link_uid)
        for role, target in sorted(wanted - set(have)):
            have[(role, target)] = d.links.add(tx, uid, target, role).uid
        for old in d.triggers.for_memos(tx, [uid]).get(uid, []):
            d.triggers.delete(tx, old.uid)
        targets = iter(trigger_targets)
        for spec in entry.fields["triggers"]:
            trigger_target = next(targets) if spec["kind"] == "event" else None
            d.triggers.insert(
                tx,
                Trigger(
                    d.new_uid(),
                    uid,
                    spec["kind"],
                    trigger_target,
                    spec["status"],
                    _time(spec["fired_at"]),
                    bool(spec["already_met"]),
                    have.get(("trigger", trigger_target)) if trigger_target else None,
                ),
            )

    def _uid_of(
        self, tx: Transaction, project: str, entry: MirrorEntry, token: str, new: Mapping[str, str], field: str
    ) -> str:
        if token in new:
            return new[token]
        qualifier, separator, bare = token.rpartition(":")
        target_project = project
        if separator:
            match = next((p for p in self._projects.list(tx) if p.name == qualifier), None)
            target_project = match.uid if match is not None else ""
        element = (
            self._d.registry.find_by_label(tx, target_project, bare if separator else token) if target_project else None
        )
        if element is None:
            file, header_line = entry.source or (TOPICS_FILE, 1)
            line = entry.source_lines.get(field, header_line)
            raise MirrorFormatError(
                "unknown_reference", f"`{token}` gab es nie (verwendet von `{entry.label}`)", file=file, line=line
            )
        return str(element.uid)

    def _write_documents(self, tx: Transaction, project: str, changes: SyncChanges, new: Mapping[str, str]) -> None:
        d = self._d
        now = d.clock.now()
        for entry in (*changes.created, *changes.updated):
            if entry.kind != KIND_DOCUMENT:
                continue
            memo_uid = self._uid_of(tx, project, entry, entry.refs["memo"][0], new, "memo")
            name = str(entry.label)
            existing = d.documents.get(tx, memo_uid, name)
            kind = document_kind(entry.refs["memo"][0], name) or entry.fields["kind"]
            if existing is None:
                d.documents.insert(tx, Document(memo_uid, name, kind, entry.fields["content"], 1, now))
            else:
                d.documents.update(tx, memo_uid, name, entry.fields["content"], existing.revision, now)
        for entry in changes.deleted:
            if entry.kind != KIND_DOCUMENT:
                continue
            element = d.registry.find_by_label(tx, project, entry.refs["memo"][0])
            if element is not None:
                self._remove_document(tx, element.uid, str(entry.label))

    def _remove_document(self, tx: Transaction, memo_uid: str, name: str) -> None:
        self._d.documents.delete(tx, memo_uid, name)

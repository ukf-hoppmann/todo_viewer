"""Anwendungsfälle für Notes: lesen, anlegen, ändern und durch den Lebenszyklus führen."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from viewer.core.application.ports import Transaction
from viewer.core.domain.errors import InvalidInput
from viewer.core.domain.events import Event
from viewer.plugins.notes.application.common import (
    NOTE_TOPIC,
    moment_field,
    text_field,
    unknown_fields,
    usable_topic,
)
from viewer.plugins.notes.application.deps import Deps
from viewer.plugins.notes.application.telling import tell_items
from viewer.plugins.notes.application.triggers import Announce, TriggerService
from viewer.plugins.notes.domain import lifecycle
from viewer.plugins.notes.domain.due import DueState, Trigger, due_state, reset, trigger_arrived
from viewer.plugins.notes.domain.model import (
    STATUSES,
    TRIGGER_MODES,
    Note,
    Topic,
    default_review_at,
)
from viewer.plugins.notes.domain.notices import Notice

NOTE_FIELDS = {"summary", "body", "topic", "review_at", "trigger_mode"}


@dataclass(frozen=True)
class IndexedNote:
    note: Note
    #: Der abgeleitete Status (`due`, wenn die Note fällig ist).
    status: str


@dataclass(frozen=True)
class IndexedTopic:
    topic: Topic
    #: Offene (nicht archivierte) Notes direkt im Topic und in allen Unter-Topics.
    open_notes: int
    #: Davon fällige.
    due_notes: int


@dataclass(frozen=True)
class NotesIndex:
    topics: list[IndexedTopic]
    notes: list[IndexedNote]


@dataclass(frozen=True)
class TriggerView:
    trigger: Trigger
    #: Das Item eines Ereignisses (uid, label, title), sonst leer.
    target: Any | None
    arrived: bool


@dataclass(frozen=True)
class NoteDetail:
    note: Note
    state: DueState
    #: Von der Wurzel bis zum Topic der Note.
    path: list[Topic]
    triggers: list[TriggerView] = field(default_factory=list)
    #: Die offenen Hinweise an die Note.
    notices: list[Notice] = field(default_factory=list)
    #: Der Elementtitel (Label, Titel) zu den `source_uid` der Hinweise.
    sources: dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> str:
        return self.state.status


@dataclass(frozen=True)
class DueEntry:
    note: Note
    state: DueState
    path: list[Topic]
    triggers: list[TriggerView]
    notices: list[Notice]


class NoteService:
    def __init__(self, deps: Deps, triggers: TriggerService) -> None:
        self._d = deps
        self._triggers = triggers

    # --- Lesen ----------------------------------------------------------------------------------------------------

    def _states(self, tx: Transaction, notes: Sequence[Note], topics: Mapping[str, Topic]) -> dict[str, DueState]:
        """Der abgeleitete Zustand jeder Note: mit ihren Auslösern, ihrem Topic und ihren offenen Hinweisen."""
        uids = [note.uid for note in notes]
        triggers = self._d.triggers.for_notes(tx, uids)
        notices = self._d.notices.open_for(tx, uids)
        now = self._d.clock.now()
        return {
            note.uid: due_state(
                note,
                triggers.get(note.uid, []),
                topics.get(note.topic_uid) if note.topic_uid else None,
                len(notices.get(note.uid, [])),
                now,
            )
            for note in notes
        }

    def index(self, project_uids: Sequence[str] | None, statuses: Sequence[str] = (), query: str = "") -> NotesIndex:
        """Topics (alle, mit Zählern) und die Notes, die Status und Text durchlassen."""
        unknown = [status for status in statuses if status not in STATUSES]
        if unknown:
            raise InvalidInput(
                f"Unbekannte Status: {', '.join(unknown)}", details={"field": "status", "allowed": list(STATUSES)}
            )
        needle = query.strip().lower()
        with self._d.database.transaction() as tx:
            topics = self._d.topics.list_in(tx, project_uids)
            notes = self._d.notes.list_in(tx, project_uids)
            by_uid = {topic.uid: topic for topic in topics}
            states = self._states(tx, notes, by_uid)
        open_count: dict[str, int] = {}
        due_count: dict[str, int] = {}
        for note in notes:
            if note.archived:
                continue
            current = note.topic_uid
            while current is not None and current in by_uid:
                open_count[current] = open_count.get(current, 0) + 1
                if states[note.uid].status == "due":
                    due_count[current] = due_count.get(current, 0) + 1
                current = by_uid[current].parent_uid
        indexed = [
            IndexedNote(note, states[note.uid].status)
            for note in notes
            if (not statuses or states[note.uid].status in statuses)
            and (not needle or needle in note.summary.lower() or needle in note.label.lower())
        ]
        return NotesIndex([IndexedTopic(t, open_count.get(t.uid, 0), due_count.get(t.uid, 0)) for t in topics], indexed)

    def get(self, ref: str, project_uid: str | None) -> NoteDetail:
        with self._d.database.transaction() as tx:
            note = self._d.resolver.note(tx, ref, project_uid)
            path = self._path(tx, note)
            topic = path[-1] if path else None
            triggers = self._d.triggers.for_notes(tx, [note.uid]).get(note.uid, [])
            notices = self._d.notices.open_for(tx, [note.uid]).get(note.uid, [])
            state = due_state(note, triggers, topic, len(notices), self._d.clock.now())
            views = self._trigger_views(tx, triggers, topic)
            sources = {}
            for notice in notices:
                element = self._d.registry.get(tx, notice.source_uid)
                if element is not None:
                    sources[notice.source_uid] = element
        return NoteDetail(note, state, path, views, notices, sources)

    def due(self, project_uids: Sequence[str] | None) -> list[DueEntry]:
        """Die fälligen Notes mit Grund, eingetretenen Auslösern und offenen Hinweisen."""
        with self._d.database.transaction() as tx:
            topics = {t.uid: t for t in self._d.topics.list_in(tx, project_uids)}
            notes = self._d.notes.list_in(tx, project_uids)
            states = self._states(tx, notes, topics)
            entries = []
            for note in notes:
                if states[note.uid].status != "due":
                    continue
                path = self._path(tx, note)
                triggers = self._d.triggers.for_notes(tx, [note.uid]).get(note.uid, [])
                views = self._trigger_views(tx, triggers, topics.get(note.topic_uid) if note.topic_uid else None)
                notices = self._d.notices.open_for(tx, [note.uid]).get(note.uid, [])
                entries.append(DueEntry(note, states[note.uid], path, views, notices))
        return entries

    def _path(self, tx: Transaction, note: Note) -> list[Topic]:
        path: list[Topic] = []
        current = self._d.topics.get(tx, note.topic_uid) if note.topic_uid else None
        while current is not None and len(path) < 50:
            path.insert(0, current)
            current = self._d.topics.get(tx, current.parent_uid) if current.parent_uid else None
        return path

    def _trigger_views(self, tx: Transaction, triggers: Sequence[Trigger], topic: Topic | None) -> list[TriggerView]:
        now = self._d.clock.now()
        return [
            TriggerView(
                trigger,
                self._d.registry.get(tx, trigger.target_uid) if trigger.target_uid else None,
                trigger_arrived(trigger, topic, now),
            )
            for trigger in triggers
        ]

    # --- Schreiben ------------------------------------------------------------------------------------------------

    def create(self, project_uid: str, fields: Mapping[str, Any]) -> str:
        unknown_fields(dict(fields), NOTE_FIELDS)
        summary = text_field("summary", fields.get("summary"))
        assert summary is not None
        body = text_field("body", fields.get("body"), required=False)
        mode = self._mode(fields.get("trigger_mode", "any"))
        review_at = moment_field("review_at", fields.get("review_at"))
        with self._d.database.transaction() as tx:
            usable_topic(self._d.topics, tx, fields.get("topic"), project_uid)
            review_at = review_at or default_review_at(self._d.clock.now(), self._d.settings.load(tx).review_days)
            element = self._d.registry.register(tx, project_uid, "note", summary)
            note = Note(
                element.uid,
                project_uid,
                element.label,
                summary,
                body,
                "waiting",
                fields.get("topic"),
                review_at,
                mode,
                False,
                element.revision,
            )
            self._d.notes.insert(tx, note)
        self._changed(note.uid, "created")
        return note.uid

    def update(self, ref: str, project_uid: str | None, version: int, fields: Mapping[str, Any]) -> str:
        """Ändert die genannten Felder einer Note in Gebrauch; ein geänderter Text setzt ein neues Prüfdatum, wenn
        keines mitkommt."""
        unknown_fields(dict(fields), NOTE_FIELDS)
        with self._d.database.transaction() as tx:
            note = self._d.resolver.note(tx, ref, project_uid)
            lifecycle.check_open(note)
            updated = note
            if "summary" in fields:
                summary = text_field("summary", fields["summary"])
                assert summary is not None
                updated = replace(updated, summary=summary)
            if "body" in fields:
                updated = replace(updated, body=text_field("body", fields["body"], required=False))
            if "topic" in fields:
                usable_topic(self._d.topics, tx, fields["topic"], note.project_uid)
                updated = replace(updated, topic_uid=fields["topic"])
            if "trigger_mode" in fields:
                updated = replace(updated, trigger_mode=self._mode(fields["trigger_mode"]))
            if "review_at" in fields:
                updated = replace(updated, review_at=moment_field("review_at", fields["review_at"]))
            elif updated.summary != note.summary or updated.body != note.body:
                days = self._d.settings.load(tx).review_days
                updated = replace(updated, review_at=default_review_at(self._d.clock.now(), days))
            self._save(tx, note, updated, version)
        self._changed(note.uid, "updated")
        return note.uid

    def keep(self, ref: str, project_uid: str | None, version: int) -> str:
        return self._transition(
            ref, project_uid, version, lambda tx, note: lifecycle.keep(note, self._d.clock.now(), self._days(tx))
        )

    def snooze(
        self,
        ref: str,
        project_uid: str | None,
        version: int,
        review_at: object = None,
        trigger: Mapping[str, Any] | None = None,
    ) -> str:
        """Zurückgestellt: gefeuerte Auslöser feuern wieder neu, ein vorbeigegangener Topic-Termin fällt weg; ein neuer
        Auslöser (`trigger`: `kind`, `target`, `status`) ersetzt alle alten."""
        until = moment_field("review_at", review_at)
        announce = Announce()

        def apply(tx: Transaction, note: Note) -> Note:
            now = self._d.clock.now()
            changed = lifecycle.snooze(note, now, self._days(tx), until)
            topic = self._d.topics.get(tx, note.topic_uid) if note.topic_uid else None
            old = self._d.triggers.for_notes(tx, [note.uid]).get(note.uid, [])
            if trigger is not None:
                for entry in old:
                    self._triggers.remove_in_tx(tx, entry, announce)
                self._triggers.create_in_tx(
                    tx, changed, str(trigger.get("kind", "")), trigger.get("target"), trigger.get("status"), announce
                )
                return changed
            kept, removed = reset(old, topic, now)
            for entry in kept:
                self._d.triggers.update(tx, entry)
            for uid in removed:
                self._d.triggers.delete(tx, uid)
            return changed

        uid = self._transition(ref, project_uid, version, apply)
        announce.publish(self._d)
        return uid

    def finish(self, ref: str, project_uid: str | None, version: int, target: str) -> str:
        """Erledigt, verworfen oder befördert: die Note wandert ins Archiv; verworfen und befördert sagt es den Items,
        auf die sie verweist."""

        def apply(tx: Transaction, note: Note) -> Note:
            done = lifecycle.finish(note, target)
            cause = {"dropped": "note_dropped", "promoted": "note_promoted"}.get(target)
            if cause is not None:
                tell_items(self._d, tx, note, cause)
            return done

        return self._transition(ref, project_uid, version, apply)

    def restore(self, ref: str, project_uid: str | None, version: int) -> str:
        def apply(tx: Transaction, note: Note) -> Note:
            topic = self._d.topics.get(tx, note.topic_uid) if note.topic_uid else None
            return lifecycle.restore(note, topic, self._d.clock.now(), self._days(tx))

        return self._transition(ref, project_uid, version, apply)

    # --- Hilfen ---------------------------------------------------------------------------------------------------

    def _transition(self, ref: str, project_uid: str | None, version: int, change: Callable[..., Note]) -> str:
        with self._d.database.transaction() as tx:
            note = self._d.resolver.note(tx, ref, project_uid)
            self._save(tx, note, change(tx, note), version)
        self._changed(note.uid, "updated")
        return note.uid

    def _save(self, tx: Transaction, before: Note, after: Note, version: int) -> None:
        revision = self._d.registry.bump_revision(tx, before.uid, version)
        self._d.notes.update(tx, replace(after, revision=revision))
        if after.summary != before.summary:
            self._d.registry.set_title(tx, before.uid, after.summary)

    def _days(self, tx: Transaction) -> int:
        return self._d.settings.load(tx).review_days

    @staticmethod
    def _mode(value: object) -> str:
        if value not in TRIGGER_MODES:
            raise InvalidInput("trigger_mode ist any oder all", details={"field": "trigger_mode"})
        return str(value)

    def _changed(self, uid: str, change: str) -> None:
        self._d.events.publish(Event(NOTE_TOPIC, {"uid": uid, "change": change}, public=True))

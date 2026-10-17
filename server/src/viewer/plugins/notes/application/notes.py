"""Anwendungsfälle für Notes: lesen, anlegen, ändern und durch den Lebenszyklus führen."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from viewer.core.application.ports import Clock, Database, EventBus, Transaction
from viewer.core.domain.errors import InvalidInput
from viewer.core.domain.events import Event
from viewer.plugins.notes.application.common import (
    NOTE_TOPIC,
    Resolver,
    moment_field,
    text_field,
    unknown_fields,
    usable_topic,
)
from viewer.plugins.notes.application.ports import NoteRepository, SettingsRepository, TopicRepository
from viewer.plugins.notes.domain import lifecycle
from viewer.plugins.notes.domain.model import (
    STATUSES,
    TRIGGER_MODES,
    Note,
    Topic,
    default_review_at,
    effective_status,
    is_due,
)

NOTE_FIELDS = {"summary", "body", "topic", "review_at", "trigger_mode"}


@dataclass(frozen=True)
class IndexedNote:
    note: Note
    #: Der abgeleitete Status (`due`, wenn das Prüfdatum erreicht ist).
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
class NoteDetail:
    note: Note
    status: str
    #: Von der Wurzel bis zum Topic der Note.
    path: list[Topic]


class NoteService:
    def __init__(
        self,
        notes: NoteRepository,
        topics: TopicRepository,
        settings: SettingsRepository,
        resolver: Resolver,
        registry: Any,
        database: Database,
        clock: Clock,
        events: EventBus,
    ) -> None:
        self._notes = notes
        self._topics = topics
        self._settings = settings
        self._resolver = resolver
        self._registry = registry
        self._database = database
        self._clock = clock
        self._events = events

    # --- Lesen ----------------------------------------------------------------------------------------------------

    def index(self, project_uids: Sequence[str] | None, statuses: Sequence[str] = (), query: str = "") -> NotesIndex:
        """Topics (alle, mit Zählern) und die Notes, die Status und Text durchlassen."""
        unknown = [status for status in statuses if status not in STATUSES]
        if unknown:
            raise InvalidInput(
                f"Unbekannte Status: {', '.join(unknown)}", details={"field": "status", "allowed": list(STATUSES)}
            )
        now = self._clock.now()
        needle = query.strip().lower()
        with self._database.transaction() as tx:
            topics = self._topics.list_in(tx, project_uids)
            notes = self._notes.list_in(tx, project_uids)
        by_uid = {topic.uid: topic for topic in topics}
        open_count: dict[str, int] = {}
        due_count: dict[str, int] = {}
        for note in notes:
            if note.archived:
                continue
            current = note.topic_uid
            while current is not None and current in by_uid:
                open_count[current] = open_count.get(current, 0) + 1
                if is_due(note, now):
                    due_count[current] = due_count.get(current, 0) + 1
                current = by_uid[current].parent_uid
        indexed = [
            IndexedNote(note, effective_status(note, now))
            for note in notes
            if (not statuses or effective_status(note, now) in statuses)
            and (not needle or needle in note.summary.lower() or needle in note.label.lower())
        ]
        return NotesIndex([IndexedTopic(t, open_count.get(t.uid, 0), due_count.get(t.uid, 0)) for t in topics], indexed)

    def get(self, ref: str, project_uid: str | None) -> NoteDetail:
        with self._database.transaction() as tx:
            note = self._resolver.note(tx, ref, project_uid)
            path: list[Topic] = []
            current = self._topics.get(tx, note.topic_uid) if note.topic_uid else None
            while current is not None and len(path) < 50:
                path.insert(0, current)
                current = self._topics.get(tx, current.parent_uid) if current.parent_uid else None
        return NoteDetail(note, effective_status(note, self._clock.now()), path)

    def due(self, project_uids: Sequence[str] | None) -> list[IndexedNote]:
        now = self._clock.now()
        with self._database.transaction() as tx:
            notes = self._notes.list_in(tx, project_uids)
        return [IndexedNote(note, "due") for note in notes if is_due(note, now)]

    # --- Schreiben ------------------------------------------------------------------------------------------------

    def create(self, project_uid: str, fields: Mapping[str, Any]) -> str:
        unknown_fields(dict(fields), NOTE_FIELDS)
        summary = text_field("summary", fields.get("summary"))
        assert summary is not None
        body = text_field("body", fields.get("body"), required=False)
        mode = self._mode(fields.get("trigger_mode", "any"))
        review_at = moment_field("review_at", fields.get("review_at"))
        with self._database.transaction() as tx:
            usable_topic(self._topics, tx, fields.get("topic"), project_uid)
            review_at = review_at or default_review_at(self._clock.now(), self._settings.load(tx).review_days)
            element = self._registry.register(tx, project_uid, "note", summary)
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
            self._notes.insert(tx, note)
        self._changed(note.uid, "created")
        return note.uid

    def update(self, ref: str, project_uid: str | None, version: int, fields: Mapping[str, Any]) -> str:
        """Ändert die genannten Felder einer Note in Gebrauch; ein geänderter Text setzt ein neues Prüfdatum, wenn
        keines mitkommt."""
        unknown_fields(dict(fields), NOTE_FIELDS)
        with self._database.transaction() as tx:
            note = self._resolver.note(tx, ref, project_uid)
            lifecycle.check_open(note)
            updated = note
            if "summary" in fields:
                summary = text_field("summary", fields["summary"])
                assert summary is not None
                updated = replace(updated, summary=summary)
            if "body" in fields:
                updated = replace(updated, body=text_field("body", fields["body"], required=False))
            if "topic" in fields:
                usable_topic(self._topics, tx, fields["topic"], note.project_uid)
                updated = replace(updated, topic_uid=fields["topic"])
            if "trigger_mode" in fields:
                updated = replace(updated, trigger_mode=self._mode(fields["trigger_mode"]))
            if "review_at" in fields:
                updated = replace(updated, review_at=moment_field("review_at", fields["review_at"]))
            elif updated.summary != note.summary or updated.body != note.body:
                days = self._settings.load(tx).review_days
                updated = replace(updated, review_at=default_review_at(self._clock.now(), days))
            self._save(tx, note, updated, version)
        self._changed(note.uid, "updated")
        return note.uid

    def keep(self, ref: str, project_uid: str | None, version: int) -> str:
        return self._transition(
            ref, project_uid, version, lambda tx, note: lifecycle.keep(note, self._clock.now(), self._days(tx))
        )

    def snooze(self, ref: str, project_uid: str | None, version: int, review_at: object = None) -> str:
        until = moment_field("review_at", review_at)
        return self._transition(
            ref,
            project_uid,
            version,
            lambda tx, note: lifecycle.snooze(note, self._clock.now(), self._days(tx), until),
        )

    def finish(self, ref: str, project_uid: str | None, version: int, target: str) -> str:
        return self._transition(ref, project_uid, version, lambda tx, note: lifecycle.finish(note, target))

    def restore(self, ref: str, project_uid: str | None, version: int) -> str:
        def apply(tx: Transaction, note: Note) -> Note:
            topic = self._topics.get(tx, note.topic_uid) if note.topic_uid else None
            return lifecycle.restore(note, topic, self._clock.now(), self._days(tx))

        return self._transition(ref, project_uid, version, apply)

    # --- Hilfen ---------------------------------------------------------------------------------------------------

    def _transition(self, ref: str, project_uid: str | None, version: int, change: Any) -> str:
        with self._database.transaction() as tx:
            note = self._resolver.note(tx, ref, project_uid)
            self._save(tx, note, change(tx, note), version)
        self._changed(note.uid, "updated")
        return note.uid

    def _save(self, tx: Transaction, before: Note, after: Note, version: int) -> None:
        revision = self._registry.bump_revision(tx, before.uid, version)
        self._notes.update(tx, replace(after, revision=revision))
        if after.summary != before.summary:
            self._registry.set_title(tx, before.uid, after.summary)

    def _days(self, tx: Transaction) -> int:
        return self._settings.load(tx).review_days

    @staticmethod
    def _mode(value: object) -> str:
        if value not in TRIGGER_MODES:
            raise InvalidInput("trigger_mode ist any oder all", details={"field": "trigger_mode"})
        return str(value)

    def _changed(self, uid: str, change: str) -> None:
        self._events.publish(Event(NOTE_TOPIC, {"uid": uid, "change": change}, public=True))

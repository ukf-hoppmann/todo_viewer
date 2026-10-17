"""Gemeinsames der Dienste von `notes`: Auflösen von Verweisen, Prüfen von Eingaben, Ereignisse."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from viewer.core.application.ports import Transaction
from viewer.core.domain.errors import InvalidInput, NotFound
from viewer.plugins.notes.application.ports import NoteRepository, TopicRepository
from viewer.plugins.notes.domain.model import Note, NotesViolation, Topic, utc

NOTE_TOPIC = "notes.note.changed"
TOPIC_TOPIC = "notes.topic.changed"
DOCUMENT_TOPIC = "notes.document.changed"
SETTINGS_TOPIC = "notes.settings.changed"
ELEMENT_TOPIC = "workspace.element.changed"

_LABEL = re.compile(r"^[A-Z]+-\d+$")


def text_field(name: str, value: object, *, required: bool = True) -> str | None:
    """Ein Textfeld ohne Rand; leer heißt bei `required` fehlend, sonst „kein Wert“."""
    if value is None:
        text = ""
    elif isinstance(value, str):
        text = value.strip()
    else:
        raise InvalidInput(f"{name} muss ein Text sein", details={"field": name})
    if not text:
        if required:
            raise InvalidInput(f"{name} fehlt", details={"field": name})
        return None
    return text


def moment_field(name: str, value: object) -> datetime | None:
    """Ein Zeitpunkt als ISO-Text oder `datetime`; `None` heißt „kein Zeitpunkt“."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return utc(value)
    if isinstance(value, str):
        try:
            return utc(datetime.fromisoformat(value))
        except ValueError:
            pass
    raise InvalidInput(f"{name} ist kein Zeitpunkt (JJJJ-MM-TT[THH:MM])", details={"field": name})


def unknown_fields(fields: dict[str, Any], allowed: set[str]) -> None:
    unknown = sorted(set(fields) - allowed)
    if unknown:
        raise InvalidInput(
            f"Unbekannte Felder: {', '.join(unknown)}", details={"field": unknown[0], "allowed": sorted(allowed)}
        )


class Resolver:
    """Löst `uid` oder Label (mit Projekt, auch ein früheres) zu Note oder Topic auf."""

    def __init__(self, notes: NoteRepository, topics: TopicRepository, registry: Any) -> None:
        self._notes = notes
        self._topics = topics
        self._registry = registry

    def _uid(self, tx: Transaction, ref: str, project_uid: str | None) -> str:
        if project_uid is not None and _LABEL.match(ref.strip()):
            element = self._registry.find_by_label(tx, project_uid, ref)
            if element is not None:
                return str(element.uid)
        return ref

    def note(self, tx: Transaction, ref: str, project_uid: str | None) -> Note:
        note = self._notes.get(tx, self._uid(tx, ref, project_uid))
        if note is None:
            self._missing("Note", ref, project_uid)
        assert note is not None
        return note

    def topic(self, tx: Transaction, ref: str, project_uid: str | None) -> Topic:
        topic = self._topics.get(tx, self._uid(tx, ref, project_uid))
        if topic is None:
            self._missing("Topic", ref, project_uid)
        assert topic is not None
        return topic

    @staticmethod
    def _missing(what: str, ref: str, project_uid: str | None) -> None:
        if project_uid is None and _LABEL.match(ref.strip()):
            raise InvalidInput(
                f"'{ref}' ist keine uid; für ein Label braucht es das Projekt", details={"field": "project"}
            )
        raise NotFound(f"{what} {ref} gibt es nicht", details={"ref": ref})


def usable_topic(topics: TopicRepository, tx: Transaction, topic_uid: str | None, project_uid: str) -> Topic | None:
    """Das Topic, in das eine Note darf: im selben Projekt, nicht im Papierkorb, nicht archiviert."""
    if topic_uid is None:
        return None
    topic = topics.get(tx, topic_uid)
    if topic is None or topic.deleted_at is not None:
        raise NotFound(f"Topic {topic_uid} gibt es nicht", details={"topic": topic_uid})
    if topic.project_uid != project_uid:
        raise NotesViolation("topic_other_project", "Das Topic gehört zu einem anderen Projekt", topic=topic.label)
    if topic.archived_at is not None:
        raise NotesViolation("topic_archived", f"Das Topic {topic.name} ist archiviert", topic=topic.label)
    return topic

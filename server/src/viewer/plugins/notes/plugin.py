"""Plugin `notes`: Notes mit Wiedervorlage und Topics."""

from __future__ import annotations

from typing import Any

from viewer.core.application.plugin import PluginContext, PluginDefinition
from viewer.core.application.ports import Transaction
from viewer.core.domain.errors import DomainError
from viewer.core.domain.plugin import ElementKind
from viewer.plugins.notes.application.common import Resolver
from viewer.plugins.notes.application.documents import DocumentService
from viewer.plugins.notes.application.notes import NoteService
from viewer.plugins.notes.application.operations import OPERATIONS, NotesServices
from viewer.plugins.notes.application.settings import SettingsService
from viewer.plugins.notes.application.topics import TopicService
from viewer.plugins.notes.infrastructure.database.repository import (
    SqlDocumentRepository,
    SqlNoteRepository,
    SqlSettingsRepository,
    SqlTopicRepository,
)
from viewer.plugins.notes.infrastructure.database.schema import MIGRATIONS
from viewer.plugins.workspace.domain.model import Element

ELEMENT_KINDS = (ElementKind("note", "NOTE"), ElementKind("topic", "TOPIC"))


class TopicInTrash(DomainError):
    code = "topic_in_trash"


def _build(context: PluginContext) -> NotesServices:
    workspace: Any = context.required["workspace"]
    notes = SqlNoteRepository()
    topics = SqlTopicRepository()
    documents = SqlDocumentRepository()
    settings = SqlSettingsRepository()
    resolver = Resolver(notes, topics, workspace.registry)

    def topic_children(tx: Transaction, uid: str) -> list[str]:
        return [*(t.uid for t in topics.children(tx, uid)), *(n.uid for n in notes.in_topic(tx, uid))]

    def note_restore_guard(tx: Transaction, element: Element) -> None:
        note = notes.get(tx, element.uid)
        topic = topics.get(tx, note.topic_uid) if note and note.topic_uid else None
        if topic is not None and topic.deleted_at is not None:
            raise TopicInTrash(
                f"{topic.label} liegt im Papierkorb; erst dieses wiederherstellen", details={"topic": topic.label}
            )

    def topic_restore_guard(tx: Transaction, element: Element) -> None:
        topic = topics.get(tx, element.uid)
        parent = topics.get(tx, topic.parent_uid) if topic and topic.parent_uid else None
        if parent is not None and parent.deleted_at is not None:
            raise TopicInTrash(
                f"{parent.label} liegt im Papierkorb; erst dieses wiederherstellen", details={"topic": parent.label}
            )

    workspace.trash.register("note", restore_guard=note_restore_guard, purger=notes.delete)
    workspace.trash.register("topic", children=topic_children, restore_guard=topic_restore_guard, purger=topics.delete)
    args = (context.database, context.clock, context.events)
    return NotesServices(
        NoteService(notes, topics, settings, resolver, workspace.registry, *args),
        TopicService(notes, topics, settings, resolver, workspace.registry, *args),
        DocumentService(documents, resolver, *args),
        SettingsService(settings, context.database, context.events),
    )


plugin = PluginDefinition(
    id="notes",
    build=_build,
    requires=("workspace",),
    migrations=MIGRATIONS,
    element_kinds=ELEMENT_KINDS,
    operations=OPERATIONS,
)

"""Plugin `notes`: Notes mit Wiedervorlage und Topics."""

from __future__ import annotations

import uuid
from typing import Any

from viewer.core.application.plugin import PluginContext, PluginDefinition
from viewer.core.application.ports import Transaction
from viewer.core.application.sync import MirrorBinding
from viewer.core.domain.errors import DomainError
from viewer.core.domain.events import Event
from viewer.core.domain.plugin import ElementKind, Subscription
from viewer.plugins.notes.application.common import Resolver
from viewer.plugins.notes.application.conversion import ConversionService
from viewer.plugins.notes.application.deps import Deps
from viewer.plugins.notes.application.documents import DocumentService
from viewer.plugins.notes.application.notes import NoteService
from viewer.plugins.notes.application.notices import NoticeService
from viewer.plugins.notes.application.operations import OPERATIONS, NotesServices
from viewer.plugins.notes.application.settings import SettingsService
from viewer.plugins.notes.application.topics import TopicService
from viewer.plugins.notes.application.triggers import TriggerService
from viewer.plugins.notes.infrastructure.backlog_gateway import ServicesBacklogGateway
from viewer.plugins.notes.infrastructure.database.repository import (
    SqlDocumentRepository,
    SqlNoteRepository,
    SqlNoticeRepository,
    SqlSettingsRepository,
    SqlTopicRepository,
    SqlTriggerRepository,
)
from viewer.plugins.notes.infrastructure.database.schema import MIGRATIONS
from viewer.plugins.notes.infrastructure.mirror.codec import NotesCodec
from viewer.plugins.notes.infrastructure.mirror.participant import NotesParticipant
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
    deps = Deps(
        notes,
        topics,
        SqlTriggerRepository(),
        SqlNoticeRepository(),
        documents,
        settings,
        resolver,
        workspace.registry,
        workspace.links,
        ServicesBacklogGateway(context.required["backlog"], context.database),
        context.database,
        context.clock,
        context.events,
        lambda: str(uuid.uuid4()),
    )
    triggers = TriggerService(deps)
    note_service = NoteService(deps, triggers)
    conversion = ConversionService(deps, note_service)
    args = (context.database, context.clock, context.events)
    return NotesServices(
        note_service,
        TopicService(notes, topics, settings, resolver, workspace.registry, *args),
        DocumentService(documents, resolver, *args),
        SettingsService(settings, context.database, context.events),
        triggers,
        NoticeService(deps, note_service, conversion),
        conversion,
        NotesParticipant(deps, workspace.project_store),
    )


def _on_status_changed(services: NotesServices, event: Event) -> None:
    services.triggers.on_status_changed(event)


def _on_element_changed(services: NotesServices, event: Event) -> None:
    services.notices.on_elements_changed(event)


def _on_item_changed(services: NotesServices, event: Event) -> None:
    services.notices.on_item_changed(event)


plugin = PluginDefinition(
    id="notes",
    build=_build,
    requires=("workspace", "backlog"),
    migrations=MIGRATIONS,
    element_kinds=ELEMENT_KINDS,
    operations=OPERATIONS,
    mirror=lambda services: MirrorBinding("notes", NotesCodec(), services.participant),
    subscriptions=(
        Subscription("backlog.item.status_changed", _on_status_changed),
        Subscription("backlog.item.changed", _on_item_changed),
        Subscription("workspace.element.changed", _on_element_changed),
    ),
)

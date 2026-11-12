"""Plugin `memos`: Memos mit Wiedervorlage und Topics."""

from __future__ import annotations

import uuid
from typing import Any

from viewer.core.application.plugin import PluginContext, PluginDefinition
from viewer.core.application.ports import Transaction
from viewer.core.application.sync import MirrorBinding
from viewer.core.domain.errors import DomainError
from viewer.core.domain.events import Event
from viewer.core.domain.plugin import ElementKind, Subscription
from viewer.plugins.memos.application.common import Resolver
from viewer.plugins.memos.application.conversion import ConversionService
from viewer.plugins.memos.application.deps import Deps
from viewer.plugins.memos.application.documents import DocumentService
from viewer.plugins.memos.application.due_watch import DueWatch
from viewer.plugins.memos.application.hints import HintService
from viewer.plugins.memos.application.memos import MemoService
from viewer.plugins.memos.application.operations import OPERATIONS, MemosServices
from viewer.plugins.memos.application.relocation import RelocationService
from viewer.plugins.memos.application.settings import SettingsService
from viewer.plugins.memos.application.topics import TopicService
from viewer.plugins.memos.application.triggers import TriggerService
from viewer.plugins.memos.infrastructure.backlog_gateway import ServicesBacklogGateway
from viewer.plugins.memos.infrastructure.database.repository import (
    SqlDocumentRepository,
    SqlHintRepository,
    SqlMemoRepository,
    SqlSettingsRepository,
    SqlTopicRepository,
    SqlTriggerRepository,
)
from viewer.plugins.memos.infrastructure.database.schema import MIGRATIONS
from viewer.plugins.memos.infrastructure.mirror.codec import MemosCodec
from viewer.plugins.memos.infrastructure.mirror.participant import MemosParticipant
from viewer.plugins.workspace.domain.model import Element

ELEMENT_KINDS = (ElementKind("memo", "MEMO"), ElementKind("topic", "TOPIC"))


class TopicInTrash(DomainError):
    code = "topic_in_trash"


def _build(context: PluginContext) -> MemosServices:
    workspace: Any = context.required["workspace"]
    memos = SqlMemoRepository()
    topics = SqlTopicRepository()
    documents = SqlDocumentRepository()
    settings = SqlSettingsRepository()
    resolver = Resolver(memos, topics, workspace.registry)

    def topic_children(tx: Transaction, uid: str) -> list[str]:
        return [*(t.uid for t in topics.children(tx, uid)), *(n.uid for n in memos.in_topic(tx, uid))]

    def memo_restore_guard(tx: Transaction, element: Element) -> None:
        memo = memos.get(tx, element.uid)
        topic = topics.get(tx, memo.topic_uid) if memo and memo.topic_uid else None
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

    def memo_closed(tx: Transaction, uid: str) -> bool:
        memo = memos.get(tx, uid)
        return memo is not None and (memo.archived or memo.finished)

    def topic_closed(tx: Transaction, uid: str) -> bool:
        topic = topics.get(tx, uid)
        return topic is not None and topic.archived_at is not None

    workspace.trash.register("memo", restore_guard=memo_restore_guard, purger=memos.delete)
    workspace.registry.register_state("memo", memo_closed)
    workspace.registry.register_state("topic", topic_closed)
    workspace.trash.register("topic", children=topic_children, restore_guard=topic_restore_guard, purger=topics.delete)
    deps = Deps(
        memos,
        topics,
        SqlTriggerRepository(),
        SqlHintRepository(),
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
    memo_service = MemoService(deps, triggers)
    conversion = ConversionService(deps, memo_service)
    args = (context.database, context.clock, context.events)
    due_watch = DueWatch(memos, topics, context.database, context.clock, context.events, context.scheduler)
    due_watch.start()
    return MemosServices(
        memo_service,
        TopicService(memos, topics, settings, resolver, workspace.registry, *args),
        DocumentService(documents, resolver, *args),
        SettingsService(settings, context.database, context.events),
        triggers,
        HintService(deps, memo_service, conversion),
        conversion,
        RelocationService(deps, triggers),
        MemosParticipant(deps, workspace.project_store),
        due_watch,
    )


def _on_status_changed(services: MemosServices, event: Event) -> None:
    services.triggers.on_status_changed(event)


def _on_element_changed(services: MemosServices, event: Event) -> None:
    services.hints.on_elements_changed(event)


def _on_item_changed(services: MemosServices, event: Event) -> None:
    services.hints.on_item_changed(event)


def _on_any(services: MemosServices, event: Event) -> None:
    services.due_watch.on_event(event)


plugin = PluginDefinition(
    id="memos",
    former_ids=("notes",),
    build=_build,
    requires=("workspace", "backlog"),
    migrations=MIGRATIONS,
    element_kinds=ELEMENT_KINDS,
    operations=OPERATIONS,
    mirror=lambda services: MirrorBinding("memos", MemosCodec(), services.participant),
    subscriptions=(
        Subscription("backlog.item.status_changed", _on_status_changed),
        Subscription("backlog.item.changed", _on_item_changed),
        Subscription("workspace.element.changed", _on_element_changed),
        # Jedes Ereignis kann ein Prüfdatum oder einen Topic-Termin geändert haben (auch die eigenen und der Sync):
        # der Termin für `memos.due` wird neu gesetzt.
        Subscription("*", _on_any),
    ),
)

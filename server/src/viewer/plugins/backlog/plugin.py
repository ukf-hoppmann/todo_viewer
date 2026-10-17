"""Plugin `backlog`: Epics, Stories und Tasks."""

from __future__ import annotations

from typing import Any

from viewer.core.application.plugin import PluginContext, PluginDefinition
from viewer.core.application.ports import Transaction
from viewer.core.application.sync import MirrorBinding
from viewer.core.domain.errors import DomainError
from viewer.core.domain.plugin import ElementKind
from viewer.plugins.backlog.application.documents import DocumentService
from viewer.plugins.backlog.application.editing import EditService
from viewer.plugins.backlog.application.items import ItemService
from viewer.plugins.backlog.application.operations import OPERATIONS, BacklogServices
from viewer.plugins.backlog.infrastructure.database.documents import SqlDocumentRepository
from viewer.plugins.backlog.infrastructure.database.repository import SqlItemRepository
from viewer.plugins.backlog.infrastructure.database.schema import MIGRATIONS
from viewer.plugins.backlog.infrastructure.mirror.codec import BacklogCodec
from viewer.plugins.backlog.infrastructure.mirror.participant import BacklogParticipant
from viewer.plugins.workspace.domain.model import Element

ELEMENT_KINDS = (ElementKind("epic", "EPIC"), ElementKind("story", "STORY"), ElementKind("task", "TASK"))


class ParentInTrash(DomainError):
    code = "parent_in_trash"


def _build(context: PluginContext) -> BacklogServices:
    workspace: Any = context.required["workspace"]
    repository = SqlItemRepository()
    items = ItemService(repository, workspace.registry, context.database)

    def children(tx: Transaction, uid: str) -> list[str]:
        return [child.uid for child in repository.children(tx, uid)]

    def restore_guard(tx: Transaction, element: Element) -> None:
        item = repository.get(tx, element.uid)
        parent = repository.get(tx, item.parent_uid) if item and item.parent_uid else None
        if parent is not None and parent.deleted_at is not None:
            raise ParentInTrash(
                f"{parent.label} liegt im Papierkorb; erst dieses wiederherstellen", details={"parent": parent.label}
            )

    for kind in ELEMENT_KINDS:
        workspace.trash.register(kind.kind, children=children, restore_guard=restore_guard, purger=repository.delete)
    documents = SqlDocumentRepository()
    editing = EditService(
        items, repository, documents, workspace.registry, context.database, context.clock, context.events
    )
    document_service = DocumentService(
        items, repository, documents, workspace.registry, context.database, context.clock, context.events
    )
    participant = BacklogParticipant(repository, documents, workspace.registry, context.database, context.clock)
    return BacklogServices(items, repository, editing, document_service, participant)


plugin = PluginDefinition(
    id="backlog",
    build=_build,
    requires=("workspace",),
    migrations=MIGRATIONS,
    element_kinds=ELEMENT_KINDS,
    operations=OPERATIONS,
    mirror=lambda services: MirrorBinding("backlog", BacklogCodec(), services.participant),
)

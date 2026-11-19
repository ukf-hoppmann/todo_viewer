"""Plugin `mindmap`: Themenbaum je Projekt aus Knoten und ihren Platzierungen."""

from __future__ import annotations

import uuid
from typing import Any

from viewer.core.application.plugin import PluginContext, PluginDefinition
from viewer.core.application.ports import Transaction
from viewer.core.domain.events import Event
from viewer.core.domain.plugin import ElementKind, Subscription
from viewer.plugins.mindmap.application.assignments import AssignmentService
from viewer.plugins.mindmap.application.documents import DocumentService
from viewer.plugins.mindmap.application.maps import MapService, MapTrash
from viewer.plugins.mindmap.application.operations import OPERATIONS, MindmapServices
from viewer.plugins.mindmap.application.service import KIND, MindmapService
from viewer.plugins.mindmap.infrastructure.backlog_gateway import ServicesBacklogItems
from viewer.plugins.mindmap.infrastructure.database.repository import SqlDocumentRepository, SqlMindmapRepository
from viewer.plugins.mindmap.infrastructure.database.schema import MIGRATIONS
from viewer.plugins.workspace import Element

ELEMENT_KINDS = (ElementKind(KIND, "NODE"),)


def _build(context: PluginContext) -> MindmapServices:
    workspace: Any = context.required["workspace"]
    backlog: Any = context.required["backlog"]
    repository = SqlMindmapRepository()
    documents = SqlDocumentRepository()
    service = MindmapService(
        repository,
        documents,
        workspace.registry,
        workspace.project_store,
        context.database,
        context.events,
        lambda: str(uuid.uuid4()),
    )

    def restore_guard(tx: Transaction, element: Element) -> None:
        service.restore_guard(tx, element.uid)

    # Ein Ast wandert mit seinen Kindern in den Papierkorb und kommt mit ihnen zurück (`children`).
    workspace.trash.register(KIND, children=service.children, restore_guard=restore_guard, purger=service.purge)
    assignments = AssignmentService(
        repository,
        ServicesBacklogItems(backlog),
        service,
        workspace.links,
        workspace.registry,
        context.database,
        context.events,
    )
    maps = MapService(
        repository,
        workspace.registry,
        workspace.project_store,
        context.database,
        context.events,
        context.clock,
        lambda: str(uuid.uuid4()),
    )
    # Freie Maps liegen als eigene Einträge im Papierkorb; ihre Knoten tragen den Löschzeitpunkt der Map.
    workspace.trash.register_source(MapTrash(repository, workspace.registry, workspace.project_store))
    return MindmapServices(
        service,
        DocumentService(documents, service, context.database, context.clock, context.events),
        assignments,
        maps,
    )


def _on_workspace_event(services: MindmapServices, event: Event) -> None:
    """Knoten, die der Papierkorb von `workspace` löscht oder zurückholt, werden als `mindmap.node.changed` gemeldet."""
    kind = str(event.payload.get("change"))
    uids = list(event.payload.get("uids", []))
    change = {"deleted": "deleted", "restored": "restored"}.get(kind)
    if change is not None:
        services.mindmap.announce(uids, change)
    if kind == "entry_restored":
        services.maps.announce_entries(uids, "restored")


plugin = PluginDefinition(
    id="mindmap",
    build=_build,
    requires=("workspace", "backlog"),
    migrations=MIGRATIONS,
    element_kinds=ELEMENT_KINDS,
    operations=OPERATIONS,
    subscriptions=(Subscription("workspace.element.changed", _on_workspace_event),),
)

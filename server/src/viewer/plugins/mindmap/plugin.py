"""Plugin `mindmap`: Themenbaum je Projekt aus Knoten und ihren Platzierungen."""

from __future__ import annotations

import uuid
from typing import Any

from viewer.core.application.plugin import PluginContext, PluginDefinition
from viewer.core.application.ports import Transaction
from viewer.core.domain.events import Event
from viewer.core.domain.plugin import ElementKind, Subscription
from viewer.plugins.mindmap.application.operations import OPERATIONS, MindmapServices
from viewer.plugins.mindmap.application.service import KIND, MindmapService
from viewer.plugins.mindmap.infrastructure.database.repository import SqlMindmapRepository
from viewer.plugins.mindmap.infrastructure.database.schema import MIGRATIONS
from viewer.plugins.workspace import Element

ELEMENT_KINDS = (ElementKind(KIND, "NODE"),)


def _build(context: PluginContext) -> MindmapServices:
    workspace: Any = context.required["workspace"]
    repository = SqlMindmapRepository()
    service = MindmapService(
        repository,
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
    return MindmapServices(service)


def _on_workspace_event(services: MindmapServices, event: Event) -> None:
    """Knoten, die der Papierkorb von `workspace` löscht oder zurückholt, werden als `mindmap.node.changed` gemeldet."""
    change = {"deleted": "deleted", "restored": "restored"}.get(str(event.payload.get("change")))
    if change is not None:
        services.mindmap.announce(list(event.payload.get("uids", [])), change)


plugin = PluginDefinition(
    id="mindmap",
    build=_build,
    requires=("workspace",),
    migrations=MIGRATIONS,
    element_kinds=ELEMENT_KINDS,
    operations=OPERATIONS,
    subscriptions=(Subscription("workspace.element.changed", _on_workspace_event),),
)

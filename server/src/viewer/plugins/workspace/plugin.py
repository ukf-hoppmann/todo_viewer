"""Plugin `workspace`: Projekte, Element-Register mit Labels, Label-Historie und Spiegel-Einstellungen je Projekt."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from viewer.core.application.plugin import PluginContext, PluginDefinition
from viewer.plugins.workspace.application.links import LinkService
from viewer.plugins.workspace.application.operations import OPERATIONS, WorkspaceServices
from viewer.plugins.workspace.application.projects import ProjectService
from viewer.plugins.workspace.application.registry import RegistryService
from viewer.plugins.workspace.application.trash import TrashService
from viewer.plugins.workspace.infrastructure.database.schema import MIGRATIONS
from viewer.plugins.workspace.infrastructure.database.stores import SqlElementStore, SqlLinkStore, SqlProjectStore


def _build(context: PluginContext) -> WorkspaceServices:
    projects = SqlProjectStore()
    elements = SqlElementStore()

    def browse_start() -> Path:
        configured = context.settings.get("browse_start") or os.environ.get("BROWSE_START")
        return Path(str(configured)) if configured else Path.home()

    service = ProjectService(
        projects,
        elements,
        context.database,
        context.clock,
        context.events,
        context.files,
        lambda: str(uuid.uuid4()),
        browse_start,
    )
    registry = RegistryService(elements, projects, context.clock, lambda: str(uuid.uuid4()))
    links = LinkService(
        SqlLinkStore(), elements, context.database, context.clock, context.events, lambda: str(uuid.uuid4())
    )
    trash = TrashService(elements, projects, context.database, context.clock, context.events)
    return WorkspaceServices(service, registry, projects, links, trash)


plugin = PluginDefinition(id="workspace", build=_build, migrations=MIGRATIONS, operations=OPERATIONS)

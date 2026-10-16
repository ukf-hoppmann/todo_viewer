"""Composition Root des Servers: feste Plugin-Liste und Verdrahtung per Konstruktor-Injektion."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from viewer.core.api.app import create_http_app
from viewer.core.api.mcp import create_mcp_host
from viewer.core.api.sse import SseHub
from viewer.core.application.core_plugin import build_core_definition
from viewer.core.application.plugin import PluginDefinition, PluginHost
from viewer.core.application.ports import Clock
from viewer.core.application.sync import MirrorConfig, MirrorProjects, SyncService
from viewer.core.domain.errors import PluginSetupError
from viewer.core.domain.plugin import ElementKind, load_order, validate_plugins
from viewer.core.domain.settings import Settings
from viewer.core.infrastructure.clock import SystemClock
from viewer.core.infrastructure.database import MigrationRunner, SqliteBackupMaker, SqliteDatabase
from viewer.core.infrastructure.database.core_schema import CORE_MIGRATIONS
from viewer.core.infrastructure.database.sync_state import SqlSyncStateStore
from viewer.core.infrastructure.database.ui_state import SqlUiStateStore
from viewer.core.infrastructure.event_bus import InProcessEventBus
from viewer.core.infrastructure.files import LocalFileStore
from viewer.core.infrastructure.ids import UuidIds
from viewer.core.infrastructure.scheduler import AsyncioScheduler
from viewer.plugins.backlog.plugin import plugin as backlog_plugin
from viewer.plugins.workspace.plugin import plugin as workspace_plugin

# Die aktiven Plugins: eine feste Liste im Code (Architektur §1). Die übrigen fachlichen Plugins
# (backlog, notes, alarms) kommen mit ihren Stories hierher.
PLUGINS: tuple[PluginDefinition, ...] = (workspace_plugin, backlog_plugin)


class WorkspaceMirrorProjects:
    """Die Projekte mit Spiegel-Ordner kommen vom Plugin `workspace`; ohne es hat kein Projekt einen Ordner."""

    def __init__(self, host: Callable[[], PluginHost]) -> None:
        self._host = host

    def _workspace(self) -> Any:
        host = self._host()
        return host.services("workspace").projects if host.has("workspace") else None

    def config(self, project: str) -> MirrorConfig | None:
        workspace = self._workspace()
        return workspace.mirror_config(project) if workspace else None

    def auto_sync_projects(self) -> list[str]:
        workspace = self._workspace()
        return workspace.auto_sync_projects() if workspace else []


def create_app(
    settings: Settings | None = None,
    plugins: Sequence[PluginDefinition] = PLUGINS,
    clock: Clock | None = None,
    mirror_projects: MirrorProjects | None = None,
) -> FastAPI:
    """Baut die Anwendung. Eine fehlerhafte Plugin-Liste wirft `PluginSetupError` (Start abgebrochen)."""
    problems = validate_plugins(plugins)  # vor jedem Zugriff auf Datenbank oder Dateien
    if problems:
        raise PluginSetupError(problems)
    settings = settings or Settings()
    clock = clock or SystemClock()
    events = InProcessEventBus()
    scheduler = AsyncioScheduler(clock)
    hub = SseHub(events, settings.sse_keepalive_seconds)
    database = SqliteDatabase(settings.db_path)
    backups = SqliteBackupMaker(database, settings.backup_dir, clock)
    files = LocalFileStore()
    sync = SyncService(
        lambda: host.mirrors,
        projects=mirror_projects or WorkspaceMirrorProjects(lambda: host),
        files=files,
        state=SqlSyncStateStore(database),
        database=database,
        backups=backups,
        events=events,
        scheduler=scheduler,
        clock=clock,
        ids=UuidIds(),
        auto_interval_seconds=settings.auto_sync_interval_seconds,
    )
    core = build_core_definition(SqlUiStateStore(database, clock), CORE_MIGRATIONS, sync)
    definitions = [core, *plugins]
    MigrationRunner(database, backups).run([{d.id: d for d in definitions}[pid] for pid in load_order(definitions)])
    host = PluginHost(
        plugins,
        clock=clock,
        events=events,
        scheduler=scheduler,
        database=database,
        backups=backups,
        files=files,
        settings=settings,
        core=core,
    )

    _register_element_kinds(host, database)
    # Ändert sich ein Projekt (Spiegel, Auto-Sync), setzt der Sync seinen Termin neu.
    events.subscribe("workspace.project.changed", lambda event: sync.refresh_auto())

    mcp = create_mcp_host(host)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        scheduler.start(asyncio.get_running_loop())
        sync.refresh_auto()
        try:
            async with mcp.lifespan:
                yield
        finally:
            hub.close()
            scheduler.stop()
            database.dispose()

    app = create_http_app(host, hub, lifespan=lifespan, mcp=mcp)
    app.state.settings = settings
    app.state.plugin_host = host
    app.state.events = events
    app.state.scheduler = scheduler
    app.state.hub = hub
    app.state.sync = sync
    app.state.database = database
    return app


def _register_element_kinds(host: PluginHost, database: SqliteDatabase) -> None:
    """Trägt die Elementtypen aller aktiven Plugins ins Element-Register von `workspace` ein."""
    if not host.has("workspace"):
        return
    by_owner: dict[str, list[ElementKind]] = {}
    for owner, kind in host.element_kinds():
        by_owner.setdefault(owner, []).append(kind)
    with database.transaction() as tx:
        for owner, kinds in by_owner.items():
            host.services("workspace").registry.register_kinds(tx, owner, kinds)

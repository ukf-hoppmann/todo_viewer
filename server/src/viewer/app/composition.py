"""Composition Root des Servers: feste Plugin-Liste und Verdrahtung per Konstruktor-Injektion."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

from fastapi import FastAPI

from viewer.core.api.app import create_http_app
from viewer.core.api.sse import SseHub
from viewer.core.application.plugin import PluginDefinition, PluginHost
from viewer.core.application.ports import Clock
from viewer.core.domain.settings import Settings
from viewer.core.infrastructure.clock import SystemClock
from viewer.core.infrastructure.event_bus import InProcessEventBus
from viewer.core.infrastructure.scheduler import AsyncioScheduler

# Die aktiven Plugins: eine feste Liste im Code (Architektur §1). Die fachlichen Plugins
# (workspace, backlog, notes, alarms) kommen mit ihren Stories hierher.
PLUGINS: tuple[PluginDefinition, ...] = ()


def create_app(
    settings: Settings | None = None,
    plugins: Sequence[PluginDefinition] = PLUGINS,
    clock: Clock | None = None,
) -> FastAPI:
    """Baut die Anwendung. Eine fehlerhafte Plugin-Liste wirft `PluginSetupError` (Start abgebrochen)."""
    settings = settings or Settings()
    clock = clock or SystemClock()
    events = InProcessEventBus()
    scheduler = AsyncioScheduler(clock)
    hub = SseHub(events, settings.sse_keepalive_seconds)
    host = PluginHost(plugins, clock=clock, events=events, scheduler=scheduler, settings=settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        scheduler.start(asyncio.get_running_loop())
        try:
            yield
        finally:
            hub.close()
            scheduler.stop()

    app = create_http_app(host, hub, lifespan=lifespan)
    app.state.settings = settings
    app.state.plugin_host = host
    app.state.events = events
    app.state.scheduler = scheduler
    app.state.hub = hub
    return app

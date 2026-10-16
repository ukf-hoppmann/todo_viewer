"""Plugin-Definition und Plugin-Host."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from viewer.core.application.ports import BackupMaker, Clock, Database, EventBus, Scheduler
from viewer.core.application.sync import MirrorBinding
from viewer.core.domain.errors import NotFound, PluginSetupError
from viewer.core.domain.operations import Operation
from viewer.core.domain.plugin import Migration, Subscription, load_order, validate_plugins
from viewer.core.domain.settings import Settings


@dataclass(frozen=True)
class PluginContext:
    """Was die Composition Root einem Plugin in `build` übergibt."""

    plugin_id: str
    clock: Clock
    events: EventBus
    scheduler: Scheduler
    database: Database
    backups: BackupMaker
    settings: Mapping[str, Any]
    required: Mapping[str, Any]  # Dienste der Plugins aus `requires`, nach ID


@dataclass(frozen=True)
class PluginDefinition:
    """Das, was `plugin.py` eines Plugins exportiert. Import ohne Nebenwirkungen."""

    id: str
    build: Callable[[PluginContext], Any]
    requires: tuple[str, ...] = ()
    migrations: tuple[Migration, ...] = ()
    element_kinds: tuple[str, ...] = ()
    operations: tuple[Operation, ...] = ()
    mirror: Callable[[Any], MirrorBinding] | None = None
    subscriptions: tuple[Subscription, ...] = field(default=())


@dataclass(frozen=True)
class LoadedPlugin:
    definition: PluginDefinition
    services: Any


class PluginHost:
    """Prüft die feste Plugin-Liste, baut die Dienste und führt Operationen aus."""

    def __init__(
        self,
        definitions: Sequence[PluginDefinition],
        *,
        clock: Clock,
        events: EventBus,
        scheduler: Scheduler,
        database: Database,
        backups: BackupMaker,
        settings: Settings,
        core: PluginDefinition | None = None,
    ) -> None:
        all_definitions = [*([core] if core else []), *definitions]
        problems = validate_plugins(all_definitions, reserved_owners=() if core else ("core",))
        if problems:
            raise PluginSetupError(problems)
        by_id = {d.id: d for d in all_definitions}
        self._loaded: dict[str, LoadedPlugin] = {}
        self._mirrors: list[MirrorBinding] = []
        for pid in load_order(all_definitions):
            definition = by_id[pid]
            context = PluginContext(
                plugin_id=pid,
                clock=clock,
                events=events,
                scheduler=scheduler,
                database=database,
                backups=backups,
                settings=settings.for_plugin(pid),
                required={r: self._loaded[r].services for r in definition.requires},
            )
            loaded = LoadedPlugin(definition, definition.build(context))
            self._loaded[pid] = loaded
            if definition.mirror is not None:
                self._mirrors.append(definition.mirror(loaded.services))
            for sub in definition.subscriptions:
                events.subscribe(sub.topic, _bind(sub, loaded.services))

    @property
    def mirrors(self) -> list[MirrorBinding]:
        """Die Spiegel der Plugins in Ladereihenfolge (zuerst die verlangten Plugins)."""
        return list(self._mirrors)

    @property
    def plugins(self) -> list[LoadedPlugin]:
        return list(self._loaded.values())

    def services(self, plugin_id: str) -> Any:
        return self._loaded[plugin_id].services

    def operation(self, owner: str, name: str) -> Operation:
        loaded = self._loaded.get(owner)
        for op in loaded.definition.operations if loaded else ():
            if op.name == name:
                return op
        raise NotFound(f"Operation {owner}.{name} gibt es nicht", details={"owner": owner, "name": name})

    async def call(self, owner: str, name: str, payload: Any) -> Any:
        """Führt eine Operation aus (sync oder async); gemeinsamer Weg für HTTP und MCP."""
        op = self.operation(owner, name)
        handler = op.handler
        services = self._loaded[owner].services
        if inspect.iscoroutinefunction(handler):
            result = await handler(services, payload)
        else:  # blockierende Handler (Datenbank) dürfen die Ereignisschleife nicht anhalten
            result = await asyncio.to_thread(handler, services, payload)
        if inspect.isawaitable(result):
            result = await result
        return result


def _bind(sub: Subscription, services: Any) -> Callable[[Any], None]:
    def handler(event: Any) -> None:
        sub.handler(services, event)

    return handler

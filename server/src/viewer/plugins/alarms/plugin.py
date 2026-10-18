"""Plugin `alarms`: Wecker zu einem Zeitpunkt, als freie Erinnerung oder an Elemente gebunden."""

from __future__ import annotations

from typing import Any

from viewer.core.application.plugin import PluginContext, PluginDefinition
from viewer.core.application.sync import MirrorBinding
from viewer.core.domain.events import Event
from viewer.core.domain.plugin import ElementKind, Subscription
from viewer.plugins.alarms.application.operations import OPERATIONS, AlarmServices
from viewer.plugins.alarms.application.service import AlarmService
from viewer.plugins.alarms.infrastructure.database.repository import SqlAlarmRepository
from viewer.plugins.alarms.infrastructure.database.schema import MIGRATIONS
from viewer.plugins.alarms.infrastructure.mirror.codec import AlarmsCodec
from viewer.plugins.alarms.infrastructure.mirror.participant import AlarmsParticipant

ELEMENT_KINDS = (ElementKind("alarm", "ALARM"),)


def _build(context: PluginContext) -> AlarmServices:
    workspace: Any = context.required["workspace"]
    repository = SqlAlarmRepository()
    workspace.trash.register("alarm", purger=repository.delete)
    service = AlarmService(
        repository, workspace.registry, context.database, context.clock, context.events, context.scheduler
    )
    service.start()
    participant = AlarmsParticipant(
        repository, workspace.registry, workspace.project_store, context.database, context.clock
    )
    return AlarmServices(service, participant)


def _on_event(services: AlarmServices, event: Event) -> None:
    services.alarms.on_event(event)


plugin = PluginDefinition(
    id="alarms",
    build=_build,
    requires=("workspace",),
    migrations=MIGRATIONS,
    element_kinds=ELEMENT_KINDS,
    operations=OPERATIONS,
    # Wecker sind kurzlebig: nach dem Aufräumen verschwinden sie ohne Konflikt auch aus `alarms.md`.
    mirror=lambda services: MirrorBinding("alarms", AlarmsCodec(), services.participant, ephemeral=True),
    # Jedes fremde Ereignis kann ein Element geschlossen oder wieder geöffnet haben; der Wecker fragt nach, statt die
    # Ereignisse anderer Plugins zu kennen.
    subscriptions=(Subscription("*", _on_event),),
)

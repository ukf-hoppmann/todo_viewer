"""Was die Dienste von `notes` gemeinsam brauchen: Speicher, Register, Verknüpfungen, Uhr, Ereignisse."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from viewer.core.application.ports import Clock, Database, EventBus
from viewer.plugins.notes.application.common import Resolver
from viewer.plugins.notes.application.ports import (
    BacklogGateway,
    DocumentRepository,
    NoteRepository,
    NoticeRepository,
    SettingsRepository,
    TopicRepository,
    TriggerRepository,
)

#: Die Elementtypen des Backlogs: nur auf sie verweisen Auslöser, Hinweise, Befördern und Zurückstufen.
ITEM_KINDS = frozenset({"epic", "story", "task"})


@dataclass(frozen=True)
class Deps:
    notes: NoteRepository
    topics: TopicRepository
    triggers: TriggerRepository
    notices: NoticeRepository
    documents: DocumentRepository
    settings: SettingsRepository
    resolver: Resolver
    #: `ElementRegistry` und `Links` von `workspace`.
    registry: Any
    links: Any
    gateway: BacklogGateway
    database: Database
    clock: Clock
    events: EventBus
    new_uid: Callable[[], str]

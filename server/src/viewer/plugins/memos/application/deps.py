"""Was die Dienste von `memos` gemeinsam brauchen: Speicher, Register, Verknüpfungen, Uhr, Ereignisse."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from viewer.core.application.ports import Clock, Database, EventBus
from viewer.plugins.memos.application.common import Resolver
from viewer.plugins.memos.application.ports import (
    BacklogGateway,
    DocumentRepository,
    HintRepository,
    MemoRepository,
    SettingsRepository,
    TopicRepository,
    TriggerRepository,
)

#: Die Elementtypen des Backlogs: nur auf sie verweisen Auslöser, Hinweise, Befördern und Zurückstufen.
ITEM_KINDS = frozenset({"epic", "story", "task"})


@dataclass(frozen=True)
class Deps:
    memos: MemoRepository
    topics: TopicRepository
    triggers: TriggerRepository
    hints: HintRepository
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

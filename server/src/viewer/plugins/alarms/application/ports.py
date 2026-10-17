"""Ports des Plugins `alarms`."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from viewer.core.application.ports import Transaction
from viewer.plugins.alarms.domain.model import Alarm


class AlarmRepository(Protocol):
    def insert(self, tx: Transaction, alarm: Alarm) -> None: ...

    def update(self, tx: Transaction, alarm: Alarm) -> None:
        """Schreibt alle änderbaren Felder; die Revision hat das Register."""
        ...

    def get(self, tx: Transaction, uid: str) -> Alarm | None: ...

    def list_in(
        self, tx: Transaction, project_uids: Sequence[str] | None, *, include_deleted: bool = False
    ) -> list[Alarm]:
        """Wecker der Projekte (alle, wenn `None`) nach Zeitpunkt und Label."""
        ...

    def delete(self, tx: Transaction, uid: str) -> None: ...

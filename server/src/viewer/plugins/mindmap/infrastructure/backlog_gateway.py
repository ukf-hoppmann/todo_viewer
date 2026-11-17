"""Der Adapter des Ports `BacklogItems` auf die Dienste des Plugins `backlog` (ohne dessen Code zu importieren)."""

from __future__ import annotations

from typing import Any

from viewer.core.application.ports import Transaction
from viewer.plugins.mindmap.application.ports import BacklogItem


class ServicesBacklogItems:
    """`services` ist das Ergebnis von `build` des Plugins `backlog` (`BacklogServices`)."""

    def __init__(self, services: Any) -> None:
        self._repository = services.repository

    def list_items(self, tx: Transaction, project_uid: str) -> list[BacklogItem]:
        items = self._repository.list_in(tx, [project_uid], include_deleted=True)
        return [
            BacklogItem(
                i.uid, i.project_uid, i.label, i.type, i.title, i.status, i.parent_uid, i.deleted_at is not None
            )
            for i in items
        ]

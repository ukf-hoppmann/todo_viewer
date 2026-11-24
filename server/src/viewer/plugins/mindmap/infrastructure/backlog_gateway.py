"""Der Adapter des Ports `BacklogItems` auf die Dienste des Plugins `backlog` (ohne dessen Code zu importieren)."""

from __future__ import annotations

from typing import Any

from viewer.core.application.ports import Database, Transaction
from viewer.plugins.mindmap.application.ports import BacklogItem, CreatedElement


class ServicesBacklogItems:
    """`services` ist das Ergebnis von `build` des Plugins `backlog` (`BacklogServices`)."""

    def __init__(self, services: Any) -> None:
        self._repository = services.repository

    def list_items(self, tx: Transaction, project_uid: str) -> list[BacklogItem]:
        items = self._repository.list_in(tx, [project_uid], include_deleted=True)
        return [
            BacklogItem(
                i.uid,
                i.project_uid,
                i.label,
                i.type,
                i.title,
                i.status,
                i.parent_uid,
                i.deleted_at is not None,
                tuple(i.dependencies),
            )
            for i in items
        ]


class ServicesBacklogWriter:
    """Legt Items über `services.editing` des Plugins `backlog` an."""

    def __init__(self, services: Any, database: Database) -> None:
        self._services = services
        self._database = database

    def create_item(self, project_uid: str, type_: str, fields: dict[str, Any]) -> CreatedElement:
        uid = str(self._services.editing.create_item(project_uid, type_, fields))
        with self._database.transaction() as tx:
            item = self._services.repository.get(tx, uid)
        return CreatedElement(uid, item.label, item.title, item.type)

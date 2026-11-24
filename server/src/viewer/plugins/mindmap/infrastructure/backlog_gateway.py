"""Der Adapter des Ports `BacklogItems` auf die Dienste des Plugins `backlog` (ohne dessen Code zu importieren)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from viewer.core.application.ports import Database, Transaction
from viewer.plugins.mindmap.application.ports import BacklogItem, BacklogProblem, CreatedElement


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


class ServicesBacklogChecker:
    """Prüft geplante Items über `services.editing` des Plugins `backlog`, mit den Regeln, die beim Anlegen gelten.

    Die geplanten Items (`PlannedItem` der Mindmap) haben dieselben Felder wie die des Backlogs und werden so
    übergeben; Code des Plugins `backlog` wird nicht importiert."""

    def __init__(self, services: Any) -> None:
        self._editing = services.editing

    def check_new_items(self, project_uid: str, planned: Sequence[Any]) -> list[BacklogProblem]:
        found = self._editing.check_new_items(project_uid, planned)
        return [BacklogProblem(p.key, p.code, p.message, dict(p.details)) for p in found]

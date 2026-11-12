"""Der Adapter des Ports `BacklogGateway` auf die Dienste des Plugins `backlog` (ohne dessen Code zu importieren)."""

from __future__ import annotations

from typing import Any

from viewer.core.application.ports import Database
from viewer.core.domain.errors import DomainError
from viewer.plugins.memos.application.ports import GatewayDocument, ItemInfo


class ServicesBacklogGateway:
    """`services` ist das Ergebnis von `build` des Plugins `backlog` (`BacklogServices`)."""

    def __init__(self, services: Any, database: Database) -> None:
        self._services = services
        self._database = database

    def get_item(self, uid: str) -> ItemInfo | None:
        repository = self._services.repository
        with self._database.transaction() as tx:
            item = repository.get(tx, uid)
            if item is None:
                return None
            everything = repository.list_in(tx, [item.project_uid])
        live = [other for other in everything if other.deleted_at is None and other.uid != uid]
        return ItemInfo(
            uid=item.uid,
            project_uid=item.project_uid,
            label=item.label,
            title=item.title,
            type=item.type,
            status=item.status,
            summary=item.summary,
            revision=item.revision,
            deleted=item.deleted_at is not None,
            children=tuple(sorted(other.uid for other in live if other.parent_uid == uid)),
            dependents=tuple(sorted(other.uid for other in live if uid in other.dependencies)),
            documents=(*item.notes, *item.spec),
        )

    def create_item(self, project_uid: str, type_: str, fields: dict[str, object]) -> str:
        return str(self._services.editing.create_item(project_uid, type_, fields))

    def reject_item(self, uid: str, version: int, resolution: str) -> None:
        self._services.editing.update_item(uid, None, version, {"status": "Rejected"}, resolution)

    def read_document(self, item_uid: str, name: str) -> GatewayDocument | None:
        try:
            document = self._services.documents.get_document(item_uid, None, name)
        except DomainError as failure:
            if failure.code == "document_not_found":
                return None
            raise
        return GatewayDocument(document.content, document.revision)

    def write_document(self, item_uid: str, name: str, content: str, version: int | None, summary: str | None) -> None:
        self._services.documents.put_document(item_uid, None, name, content, version, summary)

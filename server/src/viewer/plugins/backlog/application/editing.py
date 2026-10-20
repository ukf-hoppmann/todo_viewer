from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from typing import Any

from viewer.core.application.ports import Clock, Database, EventBus, Transaction
from viewer.core.domain.errors import InvalidInput
from viewer.core.domain.events import Event
from viewer.plugins.backlog.application.items import ItemService
from viewer.plugins.backlog.application.ports import DocumentRepository, ItemRepository, NotesRepository
from viewer.plugins.backlog.domain.documents import renamed_documents
from viewer.plugins.backlog.domain.editing import (
    apply_update,
    build_new_item,
    normalize,
    rewrite_references,
)
from viewer.plugins.backlog.domain.lifecycle import LifecycleRules, LifecycleViolation, closed_ancestors, is_closed
from viewer.plugins.backlog.domain.model import KIND_BY_TYPE, TYPES, Item

CHANGED_TOPIC = "backlog.item.changed"
STATUS_TOPIC = "backlog.item.status_changed"


class ItemDeleted(LifecycleViolation):
    def __init__(self, label: str) -> None:
        super().__init__("item_deleted", label)
        self.message = f"{label} liegt im Papierkorb; erst wiederherstellen"


@dataclass(frozen=True)
class Notice:
    """Etwas, das der Aufrufer nach einer gelungenen Änderung wissen sollte; `code` ist stabil."""

    code: str
    message: str
    details: dict[str, str]


@dataclass(frozen=True)
class RetypeResult:
    uid: str
    old_label: str
    new_label: str
    notices: list[Notice]


class EditService:
    """Schreibende Fälle des Backlogs: eine Transaktion je Fall, Regeln vor dem Schreiben, Ereignisse danach."""

    def __init__(
        self,
        items: ItemService,
        repository: ItemRepository,
        documents: DocumentRepository,
        notes: NotesRepository,
        registry: Any,
        database: Database,
        clock: Clock,
        events: EventBus,
    ) -> None:
        self._items = items
        self._repository = repository
        self._documents = documents
        self._notes = notes
        self._registry = registry
        self._database = database
        self._clock = clock
        self._events = events
        self._rules = LifecycleRules()

    # --- Anlegen --------------------------------------------------------------------------------------------------

    def create_item(self, project_uid: str, type_: str, fields: Mapping[str, object]) -> str:
        today = self._clock.now().date()
        # Zuerst prüfen (mit Platzhaltern), damit das Register kein Label für ein ungültiges Item vergibt.
        build_new_item("-", "-", project_uid, type_, fields, today, 0, 1)
        with self._database.transaction() as tx:
            title = str(normalize("title", fields.get("title")))
            element = self._registry.register(tx, project_uid, KIND_BY_TYPE[type_], title)
            siblings = self._repository.siblings(tx, project_uid, normalize("parent", fields.get("parent")))  # type: ignore[arg-type]
            position = max((s.position for s in siblings), default=-1) + 1
            item = build_new_item(
                element.uid, element.label, project_uid, type_, fields, today, position, element.revision
            )
            before = self._repository.list_in(tx, [project_uid])
            self._rules.check_change(before, [*before, item])
            self._repository.insert(tx, item)
        self._changed(item.uid, "created")
        return item.uid

    # --- Ändern ---------------------------------------------------------------------------------------------------

    def update_item(
        self, ref: str, project_uid: str | None, version: int, changes: Mapping[str, object], resolution: str | None
    ) -> str:
        events: list[Callable[[], None]] = []
        with self._database.transaction() as tx:
            item = self._live(tx, ref, project_uid)
            updated = apply_update(item, changes, resolution)
            before = self._repository.list_in(tx, [item.project_uid])
            self._rules.check_change(before, [updated if i.uid == item.uid else i for i in before])
            revision = self._registry.bump_revision(tx, item.uid, version)
            self._repository.update(tx, replace(updated, revision=revision))
            if updated.title != item.title:
                self._registry.set_title(tx, item.uid, updated.title)
            if updated.status != item.status:
                events.append(lambda: self._status_changed(item, updated.status))
        self._changed(item.uid, "updated")
        for publish in events:
            publish()
        return item.uid

    def reopen_ancestors(self, ref: str, project_uid: str | None) -> list[str]:
        """Setzt das Item und die geschlossenen Vorfahren darüber von oben nach unten auf `In progress`."""
        reopened: list[Item] = []
        with self._database.transaction() as tx:
            item = self._live(tx, ref, project_uid)
            before = self._repository.list_in(tx, [item.project_uid])
            by_uid = {i.uid: i for i in before}
            chain = [*closed_ancestors(before, item.uid), item.uid]
            changes = {
                uid: replace(by_uid[uid], status="In progress", resolution=None)
                for uid in chain
                if is_closed(by_uid[uid])
            }
            if not changes:
                return []
            self._rules.check_change(before, [changes.get(i.uid, i) for i in before])
            for uid in chain:
                if uid in changes:
                    revision = self._registry.bump_revision(tx, uid, by_uid[uid].revision)
                    updated = replace(changes[uid], revision=revision)
                    self._repository.update(tx, updated)
                    reopened.append(by_uid[uid])
        for old in reopened:
            self._changed(old.uid, "updated")
            self._status_changed(old, "In progress")
        return [old.uid for old in reopened]

    # --- Umhängen -------------------------------------------------------------------------------------------------

    def move_item(self, ref: str, project_uid: str | None, version: int, parent_uid: str | None, position: int) -> str:
        with self._database.transaction() as tx:
            item = self._live(tx, ref, project_uid)
            required = item.required_for_parent
            if parent_uid is None:
                required = None
            elif required is None:
                required = True
            moved = replace(item, parent_uid=parent_uid, required_for_parent=required)
            before = self._repository.list_in(tx, [item.project_uid])
            self._rules.check_change(before, [moved if i.uid == item.uid else i for i in before])
            revision = self._registry.bump_revision(tx, item.uid, version)
            self._repository.update(tx, replace(moved, revision=revision))
            siblings = [s.uid for s in self._repository.siblings(tx, item.project_uid, parent_uid) if s.uid != item.uid]
            index = max(0, min(position, len(siblings)))
            self._repository.set_positions(tx, [*siblings[:index], item.uid, *siblings[index:]])
        self._changed(item.uid, "moved")
        return item.uid

    # --- Typwechsel -----------------------------------------------------------------------------------------------

    def retype_item(self, ref: str, project_uid: str | None, version: int, new_type: str) -> RetypeResult:
        if new_type not in TYPES:
            raise InvalidInput(f"Unbekannter Typ '{new_type}'", details={"field": "type", "allowed": list(TYPES)})
        with self._database.transaction() as tx:
            item = self._live(tx, ref, project_uid)
            if item.type == new_type:
                raise InvalidInput(
                    f"{item.label} hat den Typ {new_type} schon",
                    details={"field": "type", "allowed": [t for t in TYPES if t != item.type]},
                )
            current = self._registry.get(tx, item.uid)
            if current.revision != version:
                self._registry.bump_revision(tx, item.uid, version)  # wirft version_conflict
            element = self._registry.relabel(tx, item.uid, KIND_BY_TYPE[new_type])
            renames = renamed_documents([*item.notes, *item.spec], item.label, element.label)
            for old_name, new_name in renames.items():
                if old_name in item.notes:
                    self._notes.rename(tx, item.uid, new_name)
                else:
                    self._documents.rename(tx, item.uid, old_name, new_name)
            retyped = replace(
                item,
                type=new_type,
                label=element.label,
                revision=element.revision,
                notes=tuple(renames.get(n, n) for n in item.notes),
                spec=tuple(renames.get(n, n) for n in item.spec),
            )
            before = self._repository.list_in(tx, [item.project_uid])
            after = [retyped if i.uid == item.uid else i for i in before]
            self._rules.check_change(before, after)
            self._repository.update(tx, retyped)
            rewritten = rewrite_references(after, item.label, element.label)
            changed_uids = []
            for uid, fields in rewritten.items():
                holder = next(i for i in after if i.uid == uid)
                revision = (
                    holder.revision if uid == item.uid else self._registry.bump_revision(tx, uid, holder.revision)
                )
                self._repository.update(tx, replace(holder, revision=revision, **fields))  # type: ignore[arg-type]
                if "title" in fields:
                    self._registry.set_title(tx, uid, fields["title"])
                changed_uids.append(uid)
        self._changed(item.uid, "retyped")
        for uid in changed_uids:
            if uid != item.uid:
                self._changed(uid, "updated")
        notice = Notice(
            "external_references_may_remain",
            f"Verweise auf {item.label} außerhalb des Backlogs (Technikdoku, Tagesberichte, Code, Commit-Nachrichten) "
            f"werden nicht angepasst. Nach {item.label} suchen und dort {element.label} eintragen.",
            {"old_label": item.label, "new_label": element.label},
        )
        return RetypeResult(item.uid, item.label, element.label, [notice])

    # --- Hilfen ---------------------------------------------------------------------------------------------------

    def _live(self, tx: Transaction, ref: str, project_uid: str | None) -> Item:
        item = self._items.resolve(tx, ref, project_uid)
        if item.deleted_at is not None:
            raise ItemDeleted(item.label)
        return item

    def _changed(self, uid: str, change: str) -> None:
        self._events.publish(Event(CHANGED_TOPIC, {"uid": uid, "change": change}, public=True))

    def _status_changed(self, item: Item, new_status: str) -> None:
        payload = {
            "uid": item.uid,
            "label": item.label,
            "project_uid": item.project_uid,
            "from": item.status,
            "to": new_status,
        }
        self._events.publish(Event(STATUS_TOPIC, payload, public=False))

    def list_areas(self, project_uid: str) -> list[str]:
        with self._database.transaction() as tx:
            return self._repository.area_names(tx, project_uid)


__all__ = ["CHANGED_TOPIC", "STATUS_TOPIC", "EditService", "Notice", "RetypeResult"]

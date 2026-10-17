from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from viewer.core.application.ports import Clock, Database, EventBus, FileStore
from viewer.core.application.sync import MirrorConfig
from viewer.core.domain.errors import NotFound
from viewer.core.domain.events import Event
from viewer.plugins.workspace.application.ports import ElementStore, ProjectStore
from viewer.plugins.workspace.domain.model import (
    BuiltinProject,
    Project,
    ProjectNameTaken,
    ProjectNotEmpty,
    UnknownReference,
    reorder,
    validate_mirror,
    validate_project_name,
    validate_sync_direction,
)

CHANGED_TOPIC = "workspace.project.changed"


@dataclass(frozen=True)
class UnsetType:
    """Marker: the field was not sent (so `None` can mean 'clear the value')."""


UNSET = UnsetType()


class ProjectService:
    """Anwendungsfälle für Projekte. Jeder Fall ist eine Transaktion; das Ereignis geht erst nach dem Commit raus."""

    def __init__(
        self,
        projects: ProjectStore,
        elements: ElementStore,
        database: Database,
        clock: Clock,
        events: EventBus,
        files: FileStore,
        new_uid: Callable[[], str],
        browse_start: Callable[[], Path],
    ) -> None:
        self._projects = projects
        self._elements = elements
        self._database = database
        self._clock = clock
        self._events = events
        self._files = files
        self._new_uid = new_uid
        self._browse_start = browse_start

    def list_projects(self) -> list[Project]:
        with self._database.transaction() as tx:
            return self._projects.list(tx)

    def create_project(
        self,
        name: str,
        mirror_folder: str | None = None,
        mirror_enabled: bool = False,
        auto_sync: bool = False,
        sync_direction: str = "both",
    ) -> Project:
        cleaned = validate_project_name(name)
        folder = validate_mirror(mirror_folder, mirror_enabled)
        direction = validate_sync_direction(sync_direction)
        with self._database.transaction() as tx:
            if self._projects.name_taken(tx, cleaned):
                raise ProjectNameTaken(f"Ein Projekt namens '{cleaned}' gibt es schon", details={"name": cleaned})
            existing = self._projects.list(tx, include_deleted=True)
            project = Project(
                uid=self._new_uid(),
                name=cleaned,
                mirror_folder=folder,
                mirror_enabled=mirror_enabled,
                auto_sync=auto_sync and mirror_enabled,
                sync_direction=direction,
                position=max((p.position for p in existing), default=-1) + 1,
                revision=1,
                created_at=self._clock.now(),
            )
            self._projects.insert(tx, project)
        self._changed(project.uid, "created")
        return project

    def update_project(
        self,
        uid: str,
        version: int,
        name: str | UnsetType = UNSET,
        mirror_folder: str | None | UnsetType = UNSET,
        mirror_enabled: bool | UnsetType = UNSET,
        auto_sync: bool | UnsetType = UNSET,
        sync_direction: str | UnsetType = UNSET,
    ) -> Project:
        with self._database.transaction() as tx:
            current = self._require(tx, uid)
            changed = current
            if not isinstance(name, UnsetType):
                cleaned = validate_project_name(name)
                if cleaned != current.name:
                    if current.builtin:
                        raise BuiltinProject("Das Projekt „Allgemein“ lässt sich nicht umbenennen")
                    if self._projects.name_taken(tx, cleaned, uid):
                        raise ProjectNameTaken(
                            f"Ein Projekt namens '{cleaned}' gibt es schon", details={"name": cleaned}
                        )
                changed = replace(changed, name=cleaned)
            if not isinstance(mirror_folder, UnsetType):
                changed = replace(changed, mirror_folder=mirror_folder)
            if not isinstance(mirror_enabled, UnsetType):
                changed = replace(changed, mirror_enabled=mirror_enabled)
            if not isinstance(auto_sync, UnsetType):
                changed = replace(changed, auto_sync=auto_sync)
            if not isinstance(sync_direction, UnsetType):
                changed = replace(changed, sync_direction=validate_sync_direction(sync_direction))
            folder = validate_mirror(changed.mirror_folder, changed.mirror_enabled)
            # Ohne Spiegel gibt es keinen Auto-Sync.
            changed = replace(changed, mirror_folder=folder, auto_sync=changed.auto_sync and changed.mirror_enabled)
            updated = self._projects.update(tx, changed, version)
        self._changed(uid, "updated")
        return updated

    def move_project(self, uid: str, version: int, position: int) -> list[Project]:
        with self._database.transaction() as tx:
            current = self._require(tx, uid)
            self._projects.update(tx, current, version)  # prüft die Version (version_conflict) und erhöht die revision
            order = [p.uid for p in self._projects.list(tx)]
            self._projects.set_positions(tx, reorder(order, uid, position))
            result = self._projects.list(tx)
        self._changed(uid, "moved")
        return result

    def remove_project(self, uid: str, version: int, confirm: bool = False) -> int:
        """Entfernt ein Projekt. Ein leeres wird gelöscht; eins mit Inhalt nur mit `confirm`, dann gehen Projekt und
        Inhalt in den Papierkorb. Gibt die Zahl der in den Papierkorb gelegten Elemente zurück."""
        with self._database.transaction() as tx:
            project = self._require(tx, uid)
            if project.builtin:
                raise BuiltinProject("Das Projekt „Allgemein“ lässt sich nicht entfernen")
            if self._projects.count_elements(tx, uid, include_deleted=True) == 0:
                if project.revision != version:
                    self._projects.update(tx, project, version)  # wirft version_conflict
                self._projects.delete(tx, uid)
                trashed = 0
            else:
                active = self._projects.count_elements(tx, uid, include_deleted=False)
                if active and not confirm:
                    raise ProjectNotEmpty(
                        f"Das Projekt enthält {active} Elemente; mit Bestätigung gehen sie in den Papierkorb",
                        details={"elements": active},
                    )
                now = self._clock.now()
                self._projects.update(
                    tx, replace(project, deleted_at=now, auto_sync=False, mirror_enabled=False), version
                )
                trashed = self._projects.mark_elements_deleted(tx, uid, now)
        self._changed(uid, "removed")
        return trashed

    def resolve_label(self, project_uid: str, label: str) -> tuple[str, str, str, int, bool]:
        """`(uid, kind, aktuelles Label, revision, gelöscht)`; findet auch frühere Labels."""
        with self._database.transaction() as tx:
            uid = self._elements.find_uid_by_label(tx, project_uid, label.strip())
            element = self._elements.get(tx, uid) if uid else None
        if element is None:
            raise UnknownReference(
                f"Das Label '{label}' gab es im Projekt nie", details={"project": project_uid, "label": label}
            )
        return element.uid, element.kind, element.label, element.revision, element.deleted_at is not None

    def browse_folders(self, path: str | None):  # type: ignore[no-untyped-def]
        return self._files.list_folders(Path(path) if path else self._browse_start())

    def mirror_config(self, project_uid: str) -> MirrorConfig | None:
        with self._database.transaction() as tx:
            project = self._projects.get(tx, project_uid)
        if project is None or project.deleted_at is not None or not project.mirror_enabled or not project.mirror_folder:
            return None
        return MirrorConfig(Path(project.mirror_folder), project.auto_sync, project.name)

    def auto_sync_projects(self) -> list[str]:
        with self._database.transaction() as tx:
            return [p.uid for p in self._projects.list(tx) if p.mirror_enabled and p.auto_sync and p.mirror_folder]

    def _require(self, tx, uid: str) -> Project:  # type: ignore[no-untyped-def]
        project = self._projects.get(tx, uid)
        if project is None or project.deleted_at is not None:
            raise NotFound(f"Projekt {uid} gibt es nicht", details={"uid": uid})
        return project

    def _changed(self, uid: str, change: str) -> None:
        self._events.publish(Event(CHANGED_TOPIC, {"uid": uid, "change": change}, public=True))

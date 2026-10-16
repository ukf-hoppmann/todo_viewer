"""Ein- und Ausgaben und Operationen des Plugins `workspace` (HTTP + MCP)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from viewer.core.domain.operations import HttpBinding, Operation
from viewer.plugins.workspace.application.projects import UNSET, ProjectService
from viewer.plugins.workspace.domain.model import Project

Direction = Literal["both", "to_files", "to_database"]


@dataclass(frozen=True)
class ProjectOut:
    uid: str
    name: str
    mirror_folder: str | None
    mirror_enabled: bool
    auto_sync: bool
    sync_direction: Direction
    position: int
    version: int
    created_at: datetime
    builtin: bool


def project_out(project: Project) -> ProjectOut:
    return ProjectOut(
        uid=project.uid,
        name=project.name,
        mirror_folder=project.mirror_folder,
        mirror_enabled=project.mirror_enabled,
        auto_sync=project.auto_sync,
        sync_direction=project.sync_direction,
        position=project.position,
        version=project.revision,
        created_at=project.created_at,
        builtin=project.builtin,
    )


@dataclass(frozen=True)
class ListProjects:
    pass


@dataclass(frozen=True)
class CreateProject:
    name: str
    mirror_folder: str | None = None
    mirror_enabled: bool = False
    auto_sync: bool = False
    sync_direction: Direction = "both"


@dataclass(frozen=True)
class UpdateProject:
    """Nur die gesetzten Felder ändern sich; `mirror_folder` = "" löscht den Ordner."""

    uid: str
    version: int
    name: str | None = None
    mirror_folder: str | None = None
    mirror_enabled: bool | None = None
    auto_sync: bool | None = None
    sync_direction: Direction | None = None


@dataclass(frozen=True)
class MoveProject:
    uid: str
    version: int
    position: int


@dataclass(frozen=True)
class RemoveProject:
    uid: str
    version: int
    confirm: bool = False


@dataclass(frozen=True)
class RemoveResult:
    trashed: int


@dataclass(frozen=True)
class BrowseFolders:
    path: str | None = None


@dataclass(frozen=True)
class FolderEntryOut:
    name: str
    has_mirror: bool


@dataclass(frozen=True)
class FolderListingOut:
    path: str
    parent: str | None
    has_mirror: bool
    folders: list[FolderEntryOut] = field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class ResolveLabel:
    project_uid: str
    label: str


@dataclass(frozen=True)
class ElementRef:
    uid: str
    kind: str
    label: str
    version: int
    deleted: bool


class WorkspaceServices:
    """Die Dienste des Plugins; `projects` für die Operationen, `registry` und `project_store` für andere Plugins."""

    def __init__(self, projects: ProjectService, registry: Any, project_store: Any) -> None:
        self.projects = projects
        self.registry = registry
        self.project_store = project_store


def _unset(value: Any) -> Any:
    return UNSET if value is None else value


def _update(services: WorkspaceServices, data: UpdateProject) -> ProjectOut:
    folder: Any = UNSET if data.mirror_folder is None else (data.mirror_folder or None)
    return project_out(
        services.projects.update_project(
            data.uid,
            data.version,
            name=_unset(data.name),
            mirror_folder=folder,
            mirror_enabled=_unset(data.mirror_enabled),
            auto_sync=_unset(data.auto_sync),
            sync_direction=_unset(data.sync_direction),
        )
    )


def _browse(services: WorkspaceServices, data: BrowseFolders) -> FolderListingOut:
    listing = services.projects.browse_folders(data.path)
    return FolderListingOut(
        listing.path,
        listing.parent,
        listing.has_mirror,
        [FolderEntryOut(f.name, f.has_mirror) for f in listing.folders],
        listing.error,
    )


def _resolve(services: WorkspaceServices, data: ResolveLabel) -> ElementRef:
    uid, kind, label, revision, deleted = services.projects.resolve_label(data.project_uid, data.label)
    return ElementRef(uid, kind, label, revision, deleted)


OPERATIONS: tuple[Operation, ...] = (
    Operation(
        "list_projects",
        "Alle Projekte in ihrer Reihenfolge",
        "read",
        ListProjects,
        list[ProjectOut],
        lambda s, d: [project_out(p) for p in s.projects.list_projects()],
        HttpBinding("GET", "/projects"),
    ),
    Operation(
        "create_project",
        "Legt ein Projekt an (optional mit Spiegel-Ordner)",
        "write",
        CreateProject,
        ProjectOut,
        lambda s, d: project_out(
            s.projects.create_project(d.name, d.mirror_folder, d.mirror_enabled, d.auto_sync, d.sync_direction)
        ),
        HttpBinding("POST", "/projects"),
        mcp=False,  # Spiegel- und Sync-Einstellungen: keine MCP-Tools (Architektur §3)
    ),
    Operation(
        "update_project",
        "Ändert Name, Spiegel-Ordner und Sync-Einstellungen eines Projekts",
        "write",
        UpdateProject,
        ProjectOut,
        _update,
        HttpBinding("PUT", "/projects/{uid}"),
        mcp=False,
    ),
    Operation(
        "move_project",
        "Rückt ein Projekt an eine Stelle der Reihenfolge (ab 0)",
        "write",
        MoveProject,
        list[ProjectOut],
        lambda s, d: [project_out(p) for p in s.projects.move_project(d.uid, d.version, d.position)],
        HttpBinding("POST", "/projects/{uid}/move"),
        mcp=False,
    ),
    Operation(
        "remove_project",
        "Entfernt ein Projekt; mit Inhalt nur mit confirm, dann geht der Inhalt in den Papierkorb",
        "write",
        RemoveProject,
        RemoveResult,
        lambda s, d: RemoveResult(s.projects.remove_project(d.uid, d.version, d.confirm)),
        HttpBinding("DELETE", "/projects/{uid}"),
        mcp=False,  # endgültiges Löschen: kein MCP-Tool
    ),
    Operation(
        "browse_folders",
        "Unterordner eines Ordners für den Ordner-Browser (ohne Pfad: der Startordner)",
        "read",
        BrowseFolders,
        FolderListingOut,
        _browse,
        HttpBinding("GET", "/folders"),
    ),
    Operation(
        "resolve_label",
        "Findet ein Element über sein Label, auch ein früheres, und nennt sein aktuelles Label",
        "read",
        ResolveLabel,
        ElementRef,
        _resolve,
        HttpBinding("GET", "/projects/{project_uid}/labels/{label}"),
    ),
)

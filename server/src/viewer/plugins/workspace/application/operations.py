"""Ein- und Ausgaben und Operationen des Plugins `workspace` (HTTP + MCP)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from viewer.core.domain.operations import HttpBinding, Operation
from viewer.plugins.workspace.application.links import LinkService
from viewer.plugins.workspace.application.projects import UNSET, ProjectService
from viewer.plugins.workspace.application.trash import TrashService
from viewer.plugins.workspace.domain.model import Element, LinkView, Project

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


LinkRoleName = Literal["reference", "origin", "trigger", "node"]


@dataclass(frozen=True)
class AddLink:
    from_uid: str
    to_uid: str
    role: LinkRoleName


@dataclass(frozen=True)
class RemoveLink:
    uid: str


@dataclass(frozen=True)
class ListLinks:
    uid: str


@dataclass(frozen=True)
class SearchElements:
    query: str
    limit: int = 50


@dataclass(frozen=True)
class LinkedElement:
    """Das Element am anderen Ende einer Verknüpfung; `deleted`: es liegt im Papierkorb."""

    link_uid: str
    role: LinkRoleName
    uid: str
    project_uid: str
    kind: str
    label: str
    title: str
    deleted: bool


@dataclass(frozen=True)
class LinksOut:
    outgoing: list[LinkedElement]
    incoming: list[LinkedElement]


@dataclass(frozen=True)
class ElementOut:
    uid: str
    project_uid: str
    kind: str
    label: str
    title: str
    version: int
    deleted: bool


@dataclass(frozen=True)
class DeleteElement:
    uid: str
    version: int
    cascade: bool = False


@dataclass(frozen=True)
class DeleteResult:
    """`has_children`: nichts gelöscht, weil es `children` Nachkommen gibt und `cascade` fehlte."""

    has_children: bool
    children: int
    deleted: int


@dataclass(frozen=True)
class ListTrash:
    #: Komma-getrennte Projekt-`uid`s; ohne Angabe alle Projekte.
    projects: str | None = None
    query: str = ""


@dataclass(frozen=True)
class TrashedElement:
    uid: str
    project_uid: str
    kind: str
    label: str
    title: str
    deleted_at: datetime | None
    #: Bei einem Eintrag, der kein Element ist (ein gelöschtes Dokument): das Element, zu dem er gehört.
    owner_uid: str | None = None


@dataclass(frozen=True)
class ElementUids:
    uids: list[str]


@dataclass(frozen=True)
class Affected:
    """Die `uid`s der Elemente, die wirklich geändert wurden (Nachkommen eingeschlossen)."""

    uids: list[str]


@dataclass(frozen=True)
class Removed:
    removed: bool = True


def linked_element(view: LinkView) -> LinkedElement:
    e = view.element
    return LinkedElement(
        view.link.uid, view.link.role, e.uid, e.project_uid, e.kind, e.label, e.title, e.deleted_at is not None
    )


def element_out(e: Element) -> ElementOut:
    return ElementOut(e.uid, e.project_uid, e.kind, e.label, e.title, e.revision, e.deleted_at is not None)


class WorkspaceServices:
    """Die Dienste des Plugins; `projects` für die Operationen, `registry`, `links` und `project_store` für andere."""

    def __init__(
        self, projects: ProjectService, registry: Any, project_store: Any, links: LinkService, trash: TrashService
    ) -> None:
        self.projects = projects
        self.registry = registry
        self.project_store = project_store
        self.links = links
        self.trash = trash


def _delete(services: WorkspaceServices, data: DeleteElement) -> DeleteResult:
    outcome = services.trash.delete_element(data.uid, data.version, data.cascade)
    return DeleteResult(outcome.has_children, outcome.children, outcome.deleted)


def _list_trash(services: WorkspaceServices, data: ListTrash) -> list[TrashedElement]:
    projects = [uid for uid in (data.projects or "").split(",") if uid] if data.projects is not None else None
    return [
        TrashedElement(e.uid, e.project_uid, e.kind, e.label, e.title, e.deleted_at, e.owner_uid)
        for e in services.trash.list_trash(projects, data.query)
    ]


def _list_links(services: WorkspaceServices, data: ListLinks) -> LinksOut:
    outgoing, incoming = services.links.list_links(data.uid)
    return LinksOut([linked_element(v) for v in outgoing], [linked_element(v) for v in incoming])


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
    Operation(
        "add_link",
        "Verknüpft zwei Elemente (Rolle reference oder origin; "
        "'trigger' legt nur ein Auslöser der Notes an, 'node' die Mindmap)",
        "write",
        AddLink,
        LinkedElement,
        lambda s, d: linked_element(s.links.add_link(d.from_uid, d.to_uid, d.role)),
        HttpBinding("POST", "/links"),
    ),
    Operation(
        "remove_link",
        "Entfernt eine Verknüpfung (nicht die Rollen 'trigger' und 'node')",
        "write",
        RemoveLink,
        Removed,
        lambda s, d: (s.links.remove_link(d.uid), Removed())[1],
        HttpBinding("DELETE", "/links/{uid}"),
    ),
    Operation(
        "list_links",
        "Ausgehende und eingehende Verknüpfungen eines Elements, gelöschte Gegenstücke markiert",
        "read",
        ListLinks,
        LinksOut,
        _list_links,
        HttpBinding("GET", "/elements/{uid}/links"),
    ),
    Operation(
        "search_elements",
        "Sucht Elemente aller Projekte über Label und Titel (für die Auswahl eines Verknüpfungsziels)",
        "read",
        SearchElements,
        list[ElementOut],
        lambda s, d: [element_out(e) for e in s.links.search_elements(d.query, d.limit)],
        HttpBinding("GET", "/elements"),
    ),
    Operation(
        "delete_element",
        "Legt ein Element in den Papierkorb; hat es Kinder, nur mit cascade (sonst nennt die Antwort has_children)",
        "write",
        DeleteElement,
        DeleteResult,
        _delete,
        HttpBinding("DELETE", "/elements/{uid}"),
    ),
    Operation(
        "list_trash",
        "Elemente im Papierkorb, neueste zuerst; optional nach Projekten (komma-getrennt) und Text gefiltert",
        "read",
        ListTrash,
        list[TrashedElement],
        _list_trash,
        HttpBinding("GET", "/trash"),
    ),
    Operation(
        "restore_elements",
        "Holt Elemente samt ihren mit ihnen gelöschten Kindern aus dem Papierkorb; Regeln des Plugins gelten",
        "write",
        ElementUids,
        Affected,
        lambda s, d: Affected(s.trash.restore_elements(d.uids)),
        HttpBinding("POST", "/trash/restore"),
    ),
    Operation(
        "purge_elements",
        "Löscht Elemente aus dem Papierkorb endgültig, samt Kindern, Plugin-Daten und Verknüpfungen",
        "write",
        ElementUids,
        Affected,
        lambda s, d: Affected(s.trash.purge_elements(d.uids)),
        HttpBinding("POST", "/trash/purge"),
        mcp=False,  # endgültiges Löschen nur durch den Projektinhaber, nicht über MCP
    ),
)

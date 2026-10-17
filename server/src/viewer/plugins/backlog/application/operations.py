"""Ein- und Ausgaben und Operationen des Plugins `backlog` (HTTP + MCP)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from viewer.core.domain.operations import HttpBinding, Operation
from viewer.plugins.backlog.application.documents import DocumentService
from viewer.plugins.backlog.application.editing import EditService
from viewer.plugins.backlog.application.items import IndexEntry, ItemDetail, ItemService
from viewer.plugins.backlog.application.ports import Document
from viewer.plugins.backlog.domain.model import Item, Progress


@dataclass(frozen=True)
class ProgressOut:
    done: int
    total: int


def _progress(progress: Progress | None) -> ProgressOut | None:
    return ProgressOut(progress.done, progress.total) if progress else None


@dataclass(frozen=True)
class ListItems:
    #: Komma-getrennte Projekt-`uid`s; ohne Angabe alle Projekte.
    projects: str | None = None
    #: Komma-getrennte Status; ohne Angabe alle.
    statuses: str | None = None
    #: Komma-getrennte Prioritäten; ohne Angabe alle.
    priorities: str | None = None
    query: str = ""


@dataclass(frozen=True)
class IndexItem:
    uid: str
    project_uid: str
    label: str
    type: str
    title: str
    status: str
    priority: str
    area: str | None
    parent_uid: str | None
    required_for_parent: bool | None
    #: Die `uid`s der Items, von denen dieses abhängt.
    dependencies: list[str]
    progress: ProgressOut | None
    version: int


@dataclass(frozen=True)
class GetItem:
    ref: str
    project: str | None = None


@dataclass(frozen=True)
class ItemSummary:
    uid: str
    label: str
    type: str
    title: str
    status: str
    required_for_parent: bool | None
    deleted: bool


@dataclass(frozen=True)
class ItemOut:
    uid: str
    project_uid: str
    label: str
    type: str
    title: str
    status: str
    priority: str
    area: str | None
    parent: ItemSummary | None
    required_for_parent: bool | None
    goal: str | None
    completion_criteria: str | None
    summary: str | None
    resolution: str | None
    created: date
    notes: list[str]
    spec: list[str]
    children: list[ItemSummary]
    dependencies: list[ItemSummary]
    progress: ProgressOut | None
    version: int
    deleted: bool


@dataclass(frozen=True)
class CreateItem:
    project: str
    type: str
    #: `title`, `area`, `goal`, `completion_criteria` sind Pflicht; dazu `priority`, `required_for_parent`, `summary`,
    #: `parent` (uid), `dependencies` (uids), `created` (JJJJ-MM-TT).
    fields: dict[str, Any]


@dataclass(frozen=True)
class UpdateItem:
    ref: str
    version: int
    #: Geändert werden nur die genannten Felder (`title`, `status`, `priority`, `required_for_parent`, `goal`,
    #: `completion_criteria`, `summary`, `area`, `parent`, `dependencies`).
    fields: dict[str, Any]
    #: Pflicht bei `Completed` und `Rejected`.
    resolution: str | None = None
    #: Das Projekt, wenn `ref` ein Label ist.
    project: str | None = None


@dataclass(frozen=True)
class MoveItem:
    ref: str
    version: int
    #: `uid` des neuen Parents; `None` macht das Item zur Wurzel.
    parent: str | None
    #: Stelle unter den Geschwistern (ab 0).
    position: int = 0
    project: str | None = None


@dataclass(frozen=True)
class RetypeItem:
    ref: str
    version: int
    type: str
    project: str | None = None


@dataclass(frozen=True)
class ReopenAncestors:
    ref: str
    project: str | None = None


@dataclass(frozen=True)
class NoticeOut:
    code: str
    message: str
    details: dict[str, str]


@dataclass(frozen=True)
class RetypeOut:
    item: ItemOut
    old_label: str
    new_label: str
    notices: list[NoticeOut]


@dataclass(frozen=True)
class ReopenOut:
    #: Die wieder geöffneten Items, von oben nach unten.
    reopened: list[ItemSummary]


@dataclass(frozen=True)
class ListAreas:
    project: str


@dataclass(frozen=True)
class AreasOut:
    areas: list[str]


@dataclass(frozen=True)
class ListDocuments:
    ref: str
    project: str | None = None


@dataclass(frozen=True)
class DocumentInfo:
    name: str
    kind: str
    version: int
    updated_at: datetime


@dataclass(frozen=True)
class GetDocument:
    ref: str
    name: str
    project: str | None = None


@dataclass(frozen=True)
class DocumentOut:
    name: str
    kind: str
    content: str
    version: int
    updated_at: datetime


@dataclass(frozen=True)
class PutDocument:
    ref: str
    name: str
    content: str
    #: Die Version, die ersetzt wird; ohne Angabe wird ein neues Dokument angelegt.
    version: int | None = None
    #: Die Kurzfassung des Items; nötig, wenn das Item mit diesem Dokument zum ersten Mal Notizen bekommt.
    summary: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class AppendNote:
    ref: str
    topic: str
    discussed: list[str] = field(default_factory=list)
    decided: list[str] = field(default_factory=list)
    open: list[str] = field(default_factory=list)
    summary: str | None = None
    project: str | None = None


def document_info(document: Document) -> DocumentInfo:
    return DocumentInfo(document.name, document.kind, document.revision, document.updated_at)


def document_out(document: Document) -> DocumentOut:
    return DocumentOut(document.name, document.kind, document.content, document.revision, document.updated_at)


class BacklogServices:
    """Die Dienste des Plugins; `repository` ist auch für Tests und für andere Teile des Backlogs offen."""

    def __init__(self, items: ItemService, repository: Any, editing: EditService, documents: DocumentService) -> None:
        self.items = items
        self.repository = repository
        self.editing = editing
        self.documents = documents


def _split(value: str | None) -> list[str]:
    return [part for part in (value or "").split(",") if part]


def summary(item: Item) -> ItemSummary:
    return ItemSummary(
        item.uid, item.label, item.type, item.title, item.status, item.required_for_parent, item.deleted_at is not None
    )


def index_item(entry: IndexEntry) -> IndexItem:
    i = entry.item
    return IndexItem(
        i.uid,
        i.project_uid,
        i.label,
        i.type,
        i.title,
        i.status,
        i.priority,
        i.area,
        i.parent_uid,
        i.required_for_parent,
        list(i.dependencies),
        _progress(entry.progress),
        i.revision,
    )


def item_out(detail: ItemDetail) -> ItemOut:
    i = detail.item
    return ItemOut(
        i.uid,
        i.project_uid,
        i.label,
        i.type,
        i.title,
        i.status,
        i.priority,
        i.area,
        summary(detail.parent) if detail.parent else None,
        i.required_for_parent,
        i.goal,
        i.completion_criteria,
        i.summary,
        i.resolution,
        i.created,
        list(i.notes),
        list(i.spec),
        [summary(child) for child in detail.children],
        [summary(dependency) for dependency in detail.dependencies],
        _progress(detail.progress),
        i.revision,
        i.deleted_at is not None,
    )


def _detail(services: BacklogServices, uid: str) -> ItemOut:
    return item_out(services.items.get_item(uid))


def _reopen(services: BacklogServices, data: ReopenAncestors) -> ReopenOut:
    uids = services.editing.reopen_ancestors(data.ref, data.project)
    return ReopenOut([summary(services.items.get_item(uid).item) for uid in uids])


def _retype(services: BacklogServices, data: RetypeItem) -> RetypeOut:
    result = services.editing.retype_item(data.ref, data.project, data.version, data.type)
    notices = [NoticeOut(n.code, n.message, n.details) for n in result.notices]
    return RetypeOut(_detail(services, result.uid), result.old_label, result.new_label, notices)


def _list(services: BacklogServices, data: ListItems) -> list[IndexItem]:
    projects = _split(data.projects) if data.projects is not None else None
    entries = services.items.list_items(projects, _split(data.statuses), _split(data.priorities), data.query)
    return [index_item(entry) for entry in entries]


OPERATIONS: tuple[Operation, ...] = (
    Operation(
        "list_items",
        "Items der Projekte als flache Liste mit Fortschritt; Filter nach Status, Priorität und Text "
        "(Projekte, Status und Prioritäten komma-getrennt)",
        "read",
        ListItems,
        list[IndexItem],
        _list,
        HttpBinding("GET", "/items"),
    ),
    Operation(
        "get_item",
        "Ein Item mit allen Feldern, Kindern (auch gelöschten) und Abhängigkeiten; `ref` ist die uid oder ein Label "
        "(mit `project`)",
        "read",
        GetItem,
        ItemOut,
        lambda s, d: item_out(s.items.get_item(d.ref, d.project)),
        HttpBinding("GET", "/items/{ref}"),
    ),
    Operation(
        "create_item",
        "Legt ein Item an (Status Open); das Label vergibt der Server. Pflicht: title, area, goal, completion_criteria",
        "write",
        CreateItem,
        ItemOut,
        lambda s, d: _detail(s, s.editing.create_item(d.project, d.type, d.fields)),
        HttpBinding("POST", "/items"),
    ),
    Operation(
        "update_item",
        "Ändert Felder eines Items mit Versionsprüfung und den Regeln des Backlog-Formats; Completed und Rejected "
        "brauchen eine resolution",
        "write",
        UpdateItem,
        ItemOut,
        lambda s, d: _detail(s, s.editing.update_item(d.ref, d.project, d.version, d.fields, d.resolution)),
        HttpBinding("PUT", "/items/{ref}"),
    ),
    Operation(
        "move_item",
        "Hängt ein Item unter einen anderen Parent (oder zur Wurzel) und setzt seine Stelle unter den Geschwistern",
        "write",
        MoveItem,
        ItemOut,
        lambda s, d: _detail(s, s.editing.move_item(d.ref, d.project, d.version, d.parent, d.position)),
        HttpBinding("POST", "/items/{ref}/move"),
    ),
    Operation(
        "retype_item",
        "Ändert den Typ eines Items: es bekommt ein neues Label, die uid bleibt, Verweise im Backlog folgen",
        "write",
        RetypeItem,
        RetypeOut,
        _retype,
        HttpBinding("POST", "/items/{ref}/retype"),
    ),
    Operation(
        "reopen_ancestors",
        "Öffnet ein geschlossenes Item und die geschlossenen Vorfahren darüber von oben nach unten (In progress)",
        "write",
        ReopenAncestors,
        ReopenOut,
        _reopen,
        HttpBinding("POST", "/items/{ref}/reopen"),
    ),
    Operation(
        "list_areas",
        "Die Bereiche eines Projekts (ein neuer entsteht mit dem ersten Item, das seinen Namen trägt)",
        "read",
        ListAreas,
        AreasOut,
        lambda s, d: AreasOut(s.editing.list_areas(d.project)),
        HttpBinding("GET", "/areas"),
    ),
    Operation(
        "list_documents",
        "Die Notizen und Specs eines Items (Name, Art, Version)",
        "read",
        ListDocuments,
        list[DocumentInfo],
        lambda s, d: [document_info(doc) for doc in s.documents.list_documents(d.ref, d.project)],
        HttpBinding("GET", "/items/{ref}/documents"),
    ),
    Operation(
        "get_document",
        "Ein Dokument eines Items mit Inhalt und Version",
        "read",
        GetDocument,
        DocumentOut,
        lambda s, d: document_out(s.documents.get_document(d.ref, d.project, d.name)),
        HttpBinding("GET", "/items/{ref}/documents/{name}"),
    ),
    Operation(
        "put_document",
        "Ersetzt ein Dokument in `version` oder legt ein neues an (<LABEL>_notes.md, <LABEL>_spec[_<thema>].md)",
        "write",
        PutDocument,
        DocumentOut,
        lambda s, d: document_out(s.documents.put_document(d.ref, d.project, d.name, d.content, d.version, d.summary)),
        HttpBinding("PUT", "/items/{ref}/documents/{name}"),
    ),
    Operation(
        "append_note",
        "Hängt einen datierten Eintrag (Thema, Discussed, Decided, Open) an die Notizen; der erste legt sie an und "
        "braucht eine Kurzfassung des Items",
        "write",
        AppendNote,
        DocumentOut,
        lambda s, d: document_out(
            s.documents.append_note(d.ref, d.project, d.topic, d.discussed, d.decided, d.open, d.summary)
        ),
        HttpBinding("POST", "/items/{ref}/notes"),
    ),
)

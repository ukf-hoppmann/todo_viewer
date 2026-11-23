"""Ein- und Ausgaben und Operationen des Plugins `backlog` (HTTP + MCP)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from viewer.core.domain.operations import HttpBinding, Operation
from viewer.plugins.backlog.application.documents import DocumentService, DocumentWrite
from viewer.plugins.backlog.application.editing import EditService
from viewer.plugins.backlog.application.items import IndexEntry, ItemDetail, ItemService
from viewer.plugins.backlog.application.notes_state import NotesState, NotesStateService
from viewer.plugins.backlog.application.ports import Document, TrashedDocument
from viewer.plugins.backlog.domain.model import Item, Progress
from viewer.plugins.backlog.domain.notes import Hint, checksum, entry_text, state_of


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
    #: Zustand des Kopfs der Notes (`current`, `stale`, `missing`); `null` ohne Notes.
    notes_state: str | None = None


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
    #: Zustand des Kopfs der Notes (`current`, `stale`, `missing`); `null` ohne Notes.
    notes_state: str | None = None


@dataclass(frozen=True)
class CreateItem:
    project: str
    type: str
    #: `title`, `goal`, `completion_criteria` sind Pflicht, `area` ist optional; dazu `priority`,
    #: `required_for_parent`, `summary`, `parent` (uid), `dependencies` (uids), `created` (JJJJ-MM-TT).
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
class DeleteDocument:
    ref: str
    name: str
    #: Die Version des Dokuments, das in den Papierkorb kommt.
    version: int
    project: str | None = None


@dataclass(frozen=True)
class DocumentDeleted:
    """Das Dokument liegt jetzt im Papierkorb; `trash_uid` ist sein Eintrag dort."""

    name: str
    trash_uid: str


@dataclass(frozen=True)
class GetDocument:
    ref: str
    name: str
    project: str | None = None


@dataclass(frozen=True)
class HintOut:
    """Ein Hinweis nach dem Schreiben, nie eine Ablehnung: `notes_state_stale`, `notes_state_long`,
    `notes_history_rewritten`."""

    code: str
    message: str


@dataclass(frozen=True)
class ItemDocumentOut:
    name: str
    kind: str
    content: str
    version: int
    updated_at: datetime
    #: Nur in schreibenden Antworten auf Notizen: Zustand des Kopfs danach (`current`, `stale`, `missing`).
    notes_state: str | None = None
    hints: list[HintOut] = field(default_factory=list)


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
    #: Neuer Kopf der Notizen, im selben Schritt nach dem Eintrag gesetzt und gestempelt.
    state: str | None = None
    #: Version des Kopfs (`state_revision`); nötig, wenn es schon einen Kopf gibt.
    state_version: int | None = None
    project: str | None = None


@dataclass(frozen=True)
class NotesRef:
    ref: str
    project: str | None = None


@dataclass(frozen=True)
class PutNotesState:
    ref: str
    #: Der neue Kopf (Text unter `## State`, ohne Überschrift und ohne Stempelzeile).
    content: str
    #: Die Version des Kopfs, die ersetzt wird.
    version: int
    project: str | None = None


@dataclass(frozen=True)
class ConfirmNotesState:
    ref: str
    #: Die Version des Kopfs, die bestätigt wird.
    version: int
    project: str | None = None


@dataclass(frozen=True)
class ListNotesEntries:
    ref: str
    #: Nur die letzten N Einträge; ohne Angabe alle.
    last: int | None = None
    project: str | None = None


@dataclass(frozen=True)
class StampOut:
    day: str
    topic: str
    checksum: str


@dataclass(frozen=True)
class EntryRefOut:
    day: str
    topic: str


@dataclass(frozen=True)
class NotesStateOut:
    """Der Kopf der Notes ohne Protokoll; `version` ist die Version des Kopfs, `checksum` die aktuelle Prüfsumme des
    Protokolls."""

    name: str
    content: str
    stamp: StampOut | None
    state: str
    checksum: str
    last_entry: EntryRefOut | None
    version: int
    hints: list[HintOut]


@dataclass(frozen=True)
class NotesEntryOut:
    position: int
    day: str
    topic: str
    #: Der Eintrag mit Überschriftszeile.
    text: str


def document_info(document: Document) -> DocumentInfo:
    return DocumentInfo(document.name, document.kind, document.revision, document.updated_at)


def document_out(document: Document) -> ItemDocumentOut:
    return ItemDocumentOut(document.name, document.kind, document.content, document.revision, document.updated_at)


def _hints(found: Sequence[Hint]) -> list[HintOut]:
    return [HintOut(h.code, h.message) for h in found]


def _deleted(snapshot: TrashedDocument) -> DocumentDeleted:
    return DocumentDeleted(snapshot.name, snapshot.uid)


def document_write_out(write: DocumentWrite) -> ItemDocumentOut:
    d = write.document
    return ItemDocumentOut(d.name, d.kind, d.content, d.revision, d.updated_at, write.notes_state, _hints(write.hints))


def notes_state_out(result: NotesState) -> NotesStateOut:
    notes, parts = result.notes, result.notes.parts
    last = parts.entries[-1] if parts.entries else None
    stamp = parts.stamp
    return NotesStateOut(
        notes.name,
        parts.state,
        StampOut(stamp.day, stamp.topic, stamp.checksum) if stamp else None,
        state_of(parts),
        checksum(parts.entries),
        EntryRefOut(last.day, last.topic) if last else None,
        notes.state_revision,
        _hints(result.hints),
    )


class BacklogServices:
    """Die Dienste des Plugins; `repository` ist auch für Tests und für andere Teile des Backlogs offen."""

    def __init__(
        self,
        items: ItemService,
        repository: Any,
        editing: EditService,
        documents: DocumentService,
        participant: Any,
        notes_state: NotesStateService,
    ) -> None:
        self.participant = participant
        self.items = items
        self.repository = repository
        self.editing = editing
        self.documents = documents
        self.notes_state = notes_state


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
        entry.notes_state,
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
        detail.notes_state,
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


@dataclass(frozen=True)
class IndexLines:
    """Der Index als Text für Agenten: eine Kopfzeile und eine Zeile je Item."""

    text: str
    count: int


INDEX_HEADER = "ID | Type | Status | Area | Title | Parent | Notes"


def _lines(services: BacklogServices, data: ListItems) -> IndexLines:
    entries = _list(services, data)
    labels = {entry.uid: entry.label for entry in _list(services, ListItems(projects=data.projects))}
    rows = [
        f"{e.label} | {e.type} | {e.status} | {e.area or '-'} | {e.title} | "
        f"{labels.get(e.parent_uid, e.parent_uid) if e.parent_uid else '-'} | {e.notes_state or '-'}"
        for e in entries
    ]
    return IndexLines("\n".join([INDEX_HEADER, *rows]), len(rows))


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
        "index_lines",
        "Wie list_items, aber als kompakter Text für Agenten: eine Zeile je Item `ID | Type | Status | Area | Title | "
        "Parent`",
        "read",
        ListItems,
        IndexLines,
        _lines,
        HttpBinding("GET", "/index"),
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
        "Legt ein Item an (Status Open); das Label vergibt der Server. Pflicht: title, goal, completion_criteria; "
        "area ist optional",
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
        ItemDocumentOut,
        lambda s, d: document_out(s.documents.get_document(d.ref, d.project, d.name)),
        HttpBinding("GET", "/items/{ref}/documents/{name}"),
    ),
    Operation(
        "put_document",
        "Ersetzt ein Dokument in `version` oder legt ein neues an (<LABEL>_notes.md, <LABEL>_spec[_<thema>].md)",
        "write",
        PutDocument,
        ItemDocumentOut,
        lambda s, d: document_write_out(
            s.documents.put_document(d.ref, d.project, d.name, d.content, d.version, d.summary)
        ),
        HttpBinding("PUT", "/items/{ref}/documents/{name}"),
    ),
    Operation(
        "delete_document",
        "Legt ein Dokument eines Items (Notiz oder Spec) in `version` in den Papierkorb. Mit der Notiz gehen ihr "
        "Kopf und die Kurzfassung des Items; wiederherstellen geht über den Papierkorb",
        "write",
        DeleteDocument,
        DocumentDeleted,
        lambda s, d: _deleted(s.documents.delete_document(d.ref, d.project, d.name, d.version)),
        HttpBinding("DELETE", "/items/{ref}/documents/{name}"),
    ),
    Operation(
        "append_note",
        "Hängt einen datierten Eintrag (Thema, Discussed, Decided, Open) an die Notizen; der erste legt sie an und "
        "braucht eine Kurzfassung des Items. Mit `state` wird danach der Kopf ersetzt und gestempelt (gibt es schon "
        "einen, mit `state_version`). Die Antwort nennt den Zustand des Kopfs und Hinweise",
        "write",
        AppendNote,
        ItemDocumentOut,
        lambda s, d: document_write_out(
            s.documents.append_note(
                d.ref, d.project, d.topic, d.discussed, d.decided, d.open, d.summary, d.state, d.state_version
            )
        ),
        HttpBinding("POST", "/items/{ref}/notes"),
    ),
    Operation(
        "get_notes_state",
        "Der Kopf (`## State`) der Notizen eines Items ohne Protokoll: Inhalt, Stempel, Zustand (`current`, `stale`, "
        "`missing`), aktuelle Prüfsumme, letzter Eintrag und Version des Kopfs",
        "read",
        NotesRef,
        NotesStateOut,
        lambda s, d: notes_state_out(s.notes_state.get(d.ref, d.project)),
        HttpBinding("GET", "/items/{ref}/notes/state"),
    ),
    Operation(
        "put_notes_state",
        "Ersetzt den Kopf der Notizen in `version` und stempelt ihn gegen den letzten Protokolleintrag",
        "write",
        PutNotesState,
        NotesStateOut,
        lambda s, d: notes_state_out(s.notes_state.put(d.ref, d.project, d.content, d.version)),
        HttpBinding("PUT", "/items/{ref}/notes/state"),
    ),
    Operation(
        "confirm_notes_state",
        "Bestätigt den Kopf der Notizen unverändert als aktuell: nur der Stempel zieht auf den letzten Eintrag nach",
        "write",
        ConfirmNotesState,
        NotesStateOut,
        lambda s, d: notes_state_out(s.notes_state.confirm(d.ref, d.project, d.version)),
        HttpBinding("POST", "/items/{ref}/notes/state/confirm"),
    ),
    Operation(
        "list_notes_entries",
        "Die Protokolleinträge der Notizen mit Position, mit `last` nur die letzten N",
        "read",
        ListNotesEntries,
        list[NotesEntryOut],
        lambda s, d: [
            NotesEntryOut(position, e.day, e.topic, entry_text(e))
            for position, e in s.notes_state.entries(d.ref, d.project, d.last)
        ],
        HttpBinding("GET", "/items/{ref}/notes/entries"),
    ),
)

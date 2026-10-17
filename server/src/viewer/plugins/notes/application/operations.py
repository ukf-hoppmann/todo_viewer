"""Ein- und Ausgaben und Operationen des Plugins `notes` (HTTP + MCP)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from viewer.core.domain.errors import InvalidInput
from viewer.core.domain.operations import HttpBinding, Operation
from viewer.plugins.notes.application.conversion import ConversionService
from viewer.plugins.notes.application.documents import DocumentService
from viewer.plugins.notes.application.notes import (
    DueEntry,
    IndexedNote,
    IndexedTopic,
    NoteDetail,
    NoteService,
    TriggerView,
)
from viewer.plugins.notes.application.notices import ItemNotice, NoticeService
from viewer.plugins.notes.application.ports import Document
from viewer.plugins.notes.application.settings import SettingsService
from viewer.plugins.notes.application.topics import TopicService
from viewer.plugins.notes.application.triggers import TriggerService
from viewer.plugins.notes.domain.model import Topic
from viewer.plugins.notes.domain.notices import Notice, decision_options
from viewer.plugins.notes.domain.topics import Choice


class NotesServices:
    """Die Dienste des Plugins."""

    def __init__(
        self,
        notes: NoteService,
        topics: TopicService,
        documents: DocumentService,
        settings: SettingsService,
        triggers: TriggerService,
        notices: NoticeService,
        conversion: ConversionService,
    ) -> None:
        self.notes = notes
        self.topics = topics
        self.documents = documents
        self.settings = settings
        self.triggers = triggers
        self.notices = notices
        self.conversion = conversion


# --- Ausgaben ---------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class TopicOut:
    uid: str
    project_uid: str
    label: str
    name: str
    parent_uid: str | None
    due_at: datetime | None
    archived: bool
    #: Das neutrale Topic „Archiviert“ des Projekts.
    system: bool
    #: Offene Notes im Topic und in den Unter-Topics, davon fällige.
    open_notes: int
    due_notes: int
    version: int


@dataclass(frozen=True)
class NoteIndexOut:
    uid: str
    project_uid: str
    label: str
    summary: str
    #: Der abgeleitete Status: `due`, wenn das Prüfdatum erreicht ist.
    status: str
    archived: bool
    topic_uid: str | None
    review_at: datetime | None
    version: int


@dataclass(frozen=True)
class NotesIndexOut:
    topics: list[TopicOut]
    notes: list[NoteIndexOut]


@dataclass(frozen=True)
class TopicRef:
    uid: str
    label: str
    name: str


@dataclass(frozen=True)
class TargetRef:
    """Das Element am anderen Ende eines Auslösers oder Hinweises."""

    uid: str
    label: str
    title: str
    kind: str
    deleted: bool


@dataclass(frozen=True)
class TriggerOut:
    uid: str
    kind: str
    #: Bei einem Ereignis: der Status, den das Item erreichen soll.
    status: str | None
    target: TargetRef | None
    fired_at: datetime | None
    #: Das Item hatte den Status schon, als der Auslöser angelegt wurde.
    already_met: bool
    #: Eingetreten (gefeuert oder Topic-Termin erreicht).
    arrived: bool


@dataclass(frozen=True)
class NoteNoticeOut:
    uid: str
    #: `item_completed`, `item_rejected`, `item_deleted`, `item_retyped` (an Notes) oder `note_dropped`,
    #: `note_promoted` (an Items).
    kind: str
    created_at: datetime
    source: TargetRef | None
    #: Die möglichen Entscheidungen.
    decisions: list[str]


@dataclass(frozen=True)
class NoteOut:
    uid: str
    project_uid: str
    label: str
    summary: str
    body: str | None
    status: str
    #: Der gespeicherte Status (ohne die Ableitung `due`).
    stored_status: str
    archived: bool
    topic_uid: str | None
    #: Von der Wurzel bis zum Topic der Note.
    path: list[TopicRef]
    review_at: datetime | None
    trigger_mode: str
    documents: list[str]
    version: int
    deleted: bool
    #: Warum die Note fällig ist (`trigger`, `notice`, `topic_due`, `review_expired`), sonst leer.
    reason: str | None
    triggers: list[TriggerOut]
    #: Die offenen Hinweise an die Note.
    notices: list[NoteNoticeOut]


@dataclass(frozen=True)
class ContentOut:
    topics: int
    active: int
    archived: int


@dataclass(frozen=True)
class TopicDone:
    uid: str
    #: Bei `delete_topic`: Zahl der in den Papierkorb gelegten Elemente (Topics und Notes).
    count: int = 0


@dataclass(frozen=True)
class DueNoteOut:
    uid: str
    project_uid: str
    label: str
    summary: str
    review_at: datetime | None
    #: Warum fällig: `trigger`, `notice`, `topic_due` oder `review_expired`.
    version: int
    reason: str
    #: Die Namen der Topics von der Wurzel bis zur Note.
    path: list[str]
    triggers: list[TriggerOut]
    notices: list[NoteNoticeOut]


@dataclass(frozen=True)
class DueOut:
    count: int
    notes: list[DueNoteOut]


@dataclass(frozen=True)
class SettingsOut:
    max_topic_depth: int
    review_days: int


@dataclass(frozen=True)
class DocumentInfo:
    name: str
    kind: str
    version: int
    updated_at: datetime


@dataclass(frozen=True)
class DocumentOut:
    name: str
    kind: str
    content: str
    version: int
    updated_at: datetime


# --- Eingaben ---------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class NotesIndexIn:
    #: Komma-getrennte Projekt-`uid`s; ohne Angabe alle Projekte.
    projects: str | None = None
    #: Komma-getrennte Status (`waiting`, `due`, `snoozed`, `done`, `dropped`, `promoted`); ohne Angabe alle.
    statuses: str | None = None
    query: str = ""


@dataclass(frozen=True)
class DueIn:
    projects: str | None = None


@dataclass(frozen=True)
class GetNote:
    ref: str
    project: str | None = None


@dataclass(frozen=True)
class CreateNote:
    project: str
    #: `summary` ist Pflicht; dazu `body`, `topic` (uid), `review_at` (ISO), `trigger_mode` (`any`/`all`).
    fields: dict[str, Any]


@dataclass(frozen=True)
class UpdateNote:
    ref: str
    version: int
    #: Geändert werden nur die genannten Felder (`summary`, `body`, `topic`, `review_at`, `trigger_mode`); `null`
    #: leert `body`, `topic` und `review_at`. Ein geänderter Text setzt ein neues Prüfdatum, wenn keines mitkommt.
    fields: dict[str, Any]
    project: str | None = None


@dataclass(frozen=True)
class NoteAction:
    ref: str
    version: int
    project: str | None = None


@dataclass(frozen=True)
class SnoozeNote:
    ref: str
    version: int
    #: Neues Prüfdatum (ISO); ohne Angabe heute + Prüf-Intervall.
    review_at: str | None = None
    #: Ein neuer Auslöser (`kind`, `target`, `status`); er ersetzt alle alten. Ohne ihn feuern die gefeuerten
    #: Auslöser wieder neu und ein vorbeigegangener Topic-Termin fällt weg.
    trigger: dict[str, Any] | None = None
    project: str | None = None


@dataclass(frozen=True)
class FinishNote:
    ref: str
    version: int
    #: `done` oder `dropped`.
    status: str
    project: str | None = None


@dataclass(frozen=True)
class CreateTopic:
    project: str
    name: str
    parent: str | None = None
    due_at: str | None = None


@dataclass(frozen=True)
class UpdateTopic:
    ref: str
    version: int
    #: `name` und `due_at` (`null` löscht den Termin).
    fields: dict[str, Any]
    project: str | None = None


@dataclass(frozen=True)
class MoveTopic:
    ref: str
    version: int
    #: `uid` des neuen Parents; `null` macht das Topic zur Wurzel.
    parent: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class TopicRefIn:
    ref: str
    project: str | None = None


@dataclass(frozen=True)
class TopicChoiceIn:
    """Löschen und Archivieren eines Topics mit Inhalt verlangen eine Wahl; ohne `active_notes` und ohne
    `keep_archived` liefert die Operation `topic_has_content` mit den Zahlen."""

    ref: str
    version: int
    #: Archivierte Notes behalten (sie wandern ins Topic „Archiviert“ des Projekts).
    keep_archived: bool = False
    #: Aktive Notes: `delete` (mit dem Topic), `move` (nach `move_to`) oder beim Archivieren `archive`.
    active_notes: str | None = None
    #: Ziel von `move`: `uid` eines Topics, oder leer für „Ohne Topic“.
    move_to: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class ReactivateTopic:
    ref: str
    version: int
    project: str | None = None


@dataclass(frozen=True)
class ListNoteDocuments:
    ref: str
    project: str | None = None


@dataclass(frozen=True)
class GetNoteDocument:
    ref: str
    name: str
    project: str | None = None


@dataclass(frozen=True)
class PutNoteDocument:
    ref: str
    name: str
    content: str
    #: Die Version, die ersetzt wird; ohne Angabe wird ein neues Dokument angelegt.
    version: int | None = None
    project: str | None = None


@dataclass(frozen=True)
class AppendNoteEntry:
    ref: str
    topic: str
    discussed: list[str] = field(default_factory=list)
    decided: list[str] = field(default_factory=list)
    open: list[str] = field(default_factory=list)
    project: str | None = None


@dataclass(frozen=True)
class AddTrigger:
    ref: str
    #: `event` (ein Item erreicht `status`; `target` ist seine uid oder ein Label) oder `topic_date` (der Termin des
    #: Topics der Note ist erreicht).
    kind: str
    target: str | None = None
    #: `In progress`, `Awaiting confirmation`, `Completed` oder `Rejected`.
    status: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class RemoveTrigger:
    uid: str


@dataclass(frozen=True)
class DecideNotice:
    uid: str
    #: Am Hinweis an eine Note: `keep`, `detach`, `drop`, `promote`; an ein Item: `acknowledge`.
    decision: str
    #: Die Version der Note, auf die sich die Entscheidung stützt (Standard: die gespeicherte).
    version: int | None = None
    #: Bei `promote`: Typ und Felder des Items wie bei `promote_note`.
    type: str | None = None
    fields: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DecisionOut:
    notice: NoteNoticeOut
    #: Die Note nach der Entscheidung (bei Hinweisen an Notes).
    note: NoteOut | None


@dataclass(frozen=True)
class ListItemNotices:
    ref: str
    project: str | None = None


@dataclass(frozen=True)
class PromoteNote:
    ref: str
    version: int
    #: Typ des neuen Items: `Epic`, `Story` oder `Task`.
    type: str
    #: Felder des Items: Pflicht `area`, `goal`, `completion_criteria`; Titel und Kurzfassung sind die der Note, wenn
    #: nichts gegeben ist.
    fields: dict[str, Any] = field(default_factory=dict)
    project: str | None = None


@dataclass(frozen=True)
class PromotedOut:
    note: NoteOut
    item_uid: str


@dataclass(frozen=True)
class DemoteItem:
    ref: str
    version: int
    #: Das Topic der neuen Note (uid).
    topic: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class DemotedOut:
    note: NoteOut
    item_uid: str


@dataclass(frozen=True)
class UpdateSettings:
    max_topic_depth: int | None = None
    review_days: int | None = None


@dataclass(frozen=True)
class NoSettingsInput:
    pass


# --- Umwandlung -------------------------------------------------------------------------------------------------


def _split(value: str | None) -> list[str]:
    return [part for part in (value or "").split(",") if part]


def topic_out(entry: IndexedTopic) -> TopicOut:
    t = entry.topic
    return TopicOut(
        t.uid,
        t.project_uid,
        t.label,
        t.name,
        t.parent_uid,
        t.due_at,
        t.archived_at is not None,
        t.system,
        entry.open_notes,
        entry.due_notes,
        t.revision,
    )


def _note_index(entry: IndexedNote) -> NoteIndexOut:
    n = entry.note
    return NoteIndexOut(
        n.uid, n.project_uid, n.label, n.summary, entry.status, n.archived, n.topic_uid, n.review_at, n.revision
    )


def _target(element: Any) -> TargetRef | None:
    if element is None:
        return None
    return TargetRef(element.uid, element.label, element.title, element.kind, element.deleted_at is not None)


def _trigger_out(view: TriggerView) -> TriggerOut:
    t = view.trigger
    return TriggerOut(t.uid, t.kind, t.status, _target(view.target), t.fired_at, t.already_met, view.arrived)


def _notice_out(notice: Notice, source: Any | None) -> NoteNoticeOut:
    return NoteNoticeOut(
        notice.uid, notice.kind, notice.created_at, _target(source), list(decision_options(notice.side))
    )


def note_out(detail: NoteDetail) -> NoteOut:
    n = detail.note
    return NoteOut(
        n.uid,
        n.project_uid,
        n.label,
        n.summary,
        n.body,
        detail.status,
        n.status,
        n.archived,
        n.topic_uid,
        [TopicRef(t.uid, t.label, t.name) for t in detail.path],
        n.review_at,
        n.trigger_mode,
        list(n.documents),
        n.revision,
        n.deleted_at is not None,
        detail.state.reason,
        [_trigger_out(view) for view in detail.triggers],
        [_notice_out(notice, detail.sources.get(notice.source_uid)) for notice in detail.notices],
    )


def _plain_topic(topic: Topic) -> TopicOut:
    return topic_out(IndexedTopic(topic, 0, 0))


def _choice(data: TopicChoiceIn) -> Choice | None:
    if data.active_notes is None and not data.keep_archived:
        return None
    if data.active_notes not in (None, "delete", "move", "archive"):
        raise InvalidInput(
            "active_notes ist delete, move oder archive",
            details={"field": "active_notes", "allowed": ["delete", "move", "archive"]},
        )
    return Choice(data.keep_archived, data.active_notes, data.move_to or None)  # type: ignore[arg-type]


def _detail(services: NotesServices, uid: str) -> NoteOut:
    return note_out(services.notes.get(uid, None))


def _document_info(document: Document) -> DocumentInfo:
    return DocumentInfo(document.name, document.kind, document.revision, document.updated_at)


def _document_out(document: Document) -> DocumentOut:
    return DocumentOut(document.name, document.kind, document.content, document.revision, document.updated_at)


def _index(services: NotesServices, data: NotesIndexIn) -> NotesIndexOut:
    projects = _split(data.projects) if data.projects is not None else None
    result = services.notes.index(projects, _split(data.statuses), data.query)
    return NotesIndexOut([topic_out(t) for t in result.topics], [_note_index(n) for n in result.notes])


def _due_note(entry: DueEntry) -> DueNoteOut:
    n = entry.note
    return DueNoteOut(
        n.uid,
        n.project_uid,
        n.label,
        n.summary,
        n.review_at,
        n.revision,
        entry.state.reason or "review_expired",
        [topic.name for topic in entry.path],
        [_trigger_out(view) for view in entry.triggers],
        [_notice_out(notice, None) for notice in entry.notices],
    )


def _due(services: NotesServices, data: DueIn) -> DueOut:
    projects = _split(data.projects) if data.projects is not None else None
    entries = services.notes.due(projects)
    return DueOut(len(entries), [_due_note(entry) for entry in entries])


def _item_notice(entry: ItemNotice) -> NoteNoticeOut:
    return _notice_out(entry.notice, entry.source)


def _decided(services: NotesServices, data: DecideNotice) -> DecisionOut:
    result = services.notices.decide(data.uid, data.decision, data.version, data.type, data.fields)
    note = _detail(services, result.note_uid) if result.note_uid else None
    return DecisionOut(_notice_out(result.notice, None), note)


def _promoted(services: NotesServices, data: PromoteNote) -> PromotedOut:
    result = services.conversion.promote(data.ref, data.project, data.version, data.type, data.fields)
    return PromotedOut(_detail(services, result.note_uid), result.item_uid)


def _demoted(services: NotesServices, data: DemoteItem) -> DemotedOut:
    result = services.conversion.demote(data.ref, data.project, data.version, data.topic)
    return DemotedOut(_detail(services, result.note_uid), result.item_uid)


def _finish(services: NotesServices, data: FinishNote) -> NoteOut:
    if data.status not in ("done", "dropped"):
        raise InvalidInput("status ist done oder dropped", details={"field": "status", "allowed": ["done", "dropped"]})
    return _detail(services, services.notes.finish(data.ref, data.project, data.version, data.status))


def _settings(services: NotesServices, _data: Any) -> SettingsOut:
    current = services.settings.current()
    return SettingsOut(current.max_topic_depth, current.review_days)


OPERATIONS: tuple[Operation, ...] = (
    Operation(
        "notes_index",
        "Topics (mit Zählern) und Notes der Projekte als flache Liste; Filter nach Status (wartet, fällig, "
        "zurückgestellt, erledigt, verworfen, befördert) und Text. Projekte und Status komma-getrennt",
        "read",
        NotesIndexIn,
        NotesIndexOut,
        _index,
        HttpBinding("GET", "/index"),
    ),
    Operation(
        "get_note",
        "Eine Note mit Langtext, Topic-Pfad, Status und Dokumenten; `ref` ist die uid oder ein Label (mit `project`)",
        "read",
        GetNote,
        NoteOut,
        lambda s, d: note_out(s.notes.get(d.ref, d.project)),
        HttpBinding("GET", "/notes/{ref}"),
    ),
    Operation(
        "due_notes",
        "Die fälligen Notes (Prüfdatum erreicht) mit Zahl; gleiches Ergebnis wie der Zähler der Kopfzeile",
        "read",
        DueIn,
        DueOut,
        _due,
        HttpBinding("GET", "/due"),
    ),
    Operation(
        "create_note",
        "Legt eine Note an (Status wartet); das Label vergibt der Server. Pflicht: summary; Prüfdatum ohne Angabe "
        "heute + Prüf-Intervall",
        "write",
        CreateNote,
        NoteOut,
        lambda s, d: _detail(s, s.notes.create(d.project, d.fields)),
        HttpBinding("POST", "/notes"),
    ),
    Operation(
        "update_note",
        "Ändert Felder einer Note in Gebrauch mit Versionsprüfung (summary, body, topic, review_at, trigger_mode)",
        "write",
        UpdateNote,
        NoteOut,
        lambda s, d: _detail(s, s.notes.update(d.ref, d.project, d.version, d.fields)),
        HttpBinding("PUT", "/notes/{ref}"),
    ),
    Operation(
        "keep_note",
        "Behalten: die Note bleibt, wie sie ist, nur das Prüfdatum rückt um das Prüf-Intervall vor",
        "write",
        NoteAction,
        NoteOut,
        lambda s, d: _detail(s, s.notes.keep(d.ref, d.project, d.version)),
        HttpBinding("POST", "/notes/{ref}/keep"),
    ),
    Operation(
        "snooze_note",
        "Stellt eine Note zurück auf ein neues Prüfdatum (Standard: heute + Prüf-Intervall)",
        "write",
        SnoozeNote,
        NoteOut,
        lambda s, d: _detail(s, s.notes.snooze(d.ref, d.project, d.version, d.review_at, d.trigger)),
        HttpBinding("POST", "/notes/{ref}/snooze"),
    ),
    Operation(
        "finish_note",
        "Schließt eine Note als erledigt (done) oder verworfen (dropped) ab; sie liegt dann im Archiv",
        "write",
        FinishNote,
        NoteOut,
        _finish,
        HttpBinding("POST", "/notes/{ref}/finish"),
    ),
    Operation(
        "restore_note",
        "Holt eine Note aus dem Archiv zurück auf „wartet“ mit neuem Prüfdatum",
        "write",
        NoteAction,
        NoteOut,
        lambda s, d: _detail(s, s.notes.restore(d.ref, d.project, d.version)),
        HttpBinding("POST", "/notes/{ref}/restore"),
    ),
    Operation(
        "create_topic",
        "Legt ein Topic an (unter `parent`, sonst an der Wurzel des Projekts); die Tiefe ist begrenzt (Einstellung)",
        "write",
        CreateTopic,
        TopicDone,
        lambda s, d: TopicDone(s.topics.create(d.project, d.name, d.parent, d.due_at)),
        HttpBinding("POST", "/topics"),
    ),
    Operation(
        "update_topic",
        "Ändert Name und Termin (`due_at`) eines Topics mit Versionsprüfung",
        "write",
        UpdateTopic,
        TopicDone,
        lambda s, d: TopicDone(s.topics.update(d.ref, d.project, d.version, d.fields)),
        HttpBinding("PUT", "/topics/{ref}"),
    ),
    Operation(
        "move_topic",
        "Hängt ein Topic samt Unter-Topics unter einen anderen Parent (oder zur Wurzel), innerhalb der Tiefe",
        "write",
        MoveTopic,
        TopicDone,
        lambda s, d: TopicDone(s.topics.move(d.ref, d.project, d.version, d.parent)),
        HttpBinding("POST", "/topics/{ref}/move"),
    ),
    Operation(
        "topic_content",
        "Zahl der Unter-Topics sowie aktiven und archivierten Notes in einem Topic (für den Auswahldialog)",
        "read",
        TopicRefIn,
        ContentOut,
        lambda s, d: _content(s, d),
        HttpBinding("GET", "/topics/{ref}/content"),
    ),
    Operation(
        "archive_topic",
        "Archiviert ein Topic samt Unter-Topics. Mit Inhalt braucht es eine Wahl: archivierte Notes behalten, "
        "aktive Notes verschieben (`move`) oder mitarchivieren (`archive`)",
        "write",
        TopicChoiceIn,
        TopicDone,
        lambda s, d: TopicDone(s.topics.archive(d.ref, d.project, d.version, _choice(d))),
        HttpBinding("POST", "/topics/{ref}/archive"),
    ),
    Operation(
        "reactivate_topic",
        "Aktiviert ein archiviertes Topic samt Unter-Topics wieder; Notes, die nur seinetwegen archiviert waren, "
        "kommen zurück",
        "write",
        ReactivateTopic,
        TopicDone,
        lambda s, d: TopicDone(s.topics.reactivate(d.ref, d.project, d.version)),
        HttpBinding("POST", "/topics/{ref}/reactivate"),
    ),
    Operation(
        "delete_topic",
        "Legt ein Topic in den Papierkorb. Mit Inhalt braucht es eine Wahl: archivierte Notes behalten, aktive "
        "Notes verschieben (`move`) oder mit löschen (`delete`); nicht Gewähltes geht mit in den Papierkorb",
        "write",
        TopicChoiceIn,
        TopicDone,
        lambda s, d: _deleted(s, d),
        HttpBinding("POST", "/topics/{ref}/delete"),
    ),
    Operation(
        "list_note_documents",
        "Die Dokumente einer Note (Name, Art, Version)",
        "read",
        ListNoteDocuments,
        list[DocumentInfo],
        lambda s, d: [_document_info(doc) for doc in s.documents.list_documents(d.ref, d.project)],
        HttpBinding("GET", "/notes/{ref}/documents"),
    ),
    Operation(
        "get_note_document",
        "Ein Dokument einer Note mit Inhalt und Version",
        "read",
        GetNoteDocument,
        DocumentOut,
        lambda s, d: _document_out(s.documents.get_document(d.ref, d.project, d.name)),
        HttpBinding("GET", "/notes/{ref}/documents/{name}"),
    ),
    Operation(
        "put_note_document",
        "Ersetzt ein Dokument in `version` oder legt ein neues an (<LABEL>_notes.md, <LABEL>_spec[_<thema>].md)",
        "write",
        PutNoteDocument,
        DocumentOut,
        lambda s, d: _document_out(s.documents.put_document(d.ref, d.project, d.name, d.content, d.version)),
        HttpBinding("PUT", "/notes/{ref}/documents/{name}"),
    ),
    Operation(
        "append_note_entry",
        "Hängt einen datierten Eintrag (Thema, Discussed, Decided, Open) an die Notizen einer Note",
        "write",
        AppendNoteEntry,
        DocumentOut,
        lambda s, d: _document_out(s.documents.append_note(d.ref, d.project, d.topic, d.discussed, d.decided, d.open)),
        HttpBinding("POST", "/notes/{ref}/entries"),
    ),
    Operation(
        "add_trigger",
        "Legt einen Auslöser an: ein Item erreicht einen Status (`event`, mit `target` und `status`) oder der "
        "Termin des Topics der Note ist erreicht (`topic_date`). Erreicht er sein Ziel, wird die Note fällig; hat "
        "das Item den Status schon, feuert er sofort",
        "write",
        AddTrigger,
        NoteOut,
        lambda s, d: _detail(s, s.triggers.add(d.ref, d.project, d.kind, d.target, d.status)),
        HttpBinding("POST", "/notes/{ref}/triggers"),
    ),
    Operation(
        "remove_trigger",
        "Entfernt einen Auslöser einer Note in Gebrauch (mit seiner Verknüpfung)",
        "write",
        RemoveTrigger,
        NoteOut,
        lambda s, d: _detail(s, s.triggers.remove(d.uid)),
        HttpBinding("DELETE", "/triggers/{uid}"),
    ),
    Operation(
        "decide_notice",
        "Entscheidet einen offenen Hinweis: an einer Note keep (Prüfdatum rückt), detach (Verknüpfung zum Item "
        "entfernen), drop (Note verwerfen) oder promote (zum Item befördern); an einem Item acknowledge",
        "write",
        DecideNotice,
        DecisionOut,
        _decided,
        HttpBinding("POST", "/notices/{uid}/decide"),
    ),
    Operation(
        "list_item_notices",
        "Die offenen Hinweise an ein Item des Backlogs (eine Note, die auf es verweist, wurde verworfen oder "
        "befördert)",
        "read",
        ListItemNotices,
        list[NoteNoticeOut],
        lambda s, d: [_item_notice(entry) for entry in s.notices.list_for_item(d.ref, d.project)],
        HttpBinding("GET", "/items/{ref}/notices"),
    ),
    Operation(
        "promote_note",
        "Befördert eine Note zu einem Item (Epic, Story oder Task) im selben Projekt: Langtext, Notizen und Specs "
        "werden übernommen, die Note ist danach befördert (Archiv) und mit dem Item verknüpft (origin). Pflicht: type "
        "und die Felder area, goal, completion_criteria",
        "write",
        PromoteNote,
        PromotedOut,
        _promoted,
        HttpBinding("POST", "/notes/{ref}/promote"),
    ),
    Operation(
        "demote_item",
        "Stuft ein offenes Item (Status Open, ohne Kinder, von dem nichts abhängt) zu einer Note zurück; das Item wird "
        "abgelehnt (Rejected), Notizen und Specs wandern an die Note",
        "write",
        DemoteItem,
        DemotedOut,
        _demoted,
        HttpBinding("POST", "/items/{ref}/demote"),
    ),
    Operation(
        "get_notes_settings",
        "Prüf-Intervall (Tage) und größte Topic-Tiefe",
        "read",
        NoSettingsInput,
        SettingsOut,
        _settings,
        HttpBinding("GET", "/settings"),
        mcp=False,
    ),
    Operation(
        "update_notes_settings",
        "Ändert Prüf-Intervall und größte Topic-Tiefe",
        "write",
        UpdateSettings,
        SettingsOut,
        lambda s, d: _updated(s, d),
        HttpBinding("PUT", "/settings"),
        mcp=False,
    ),
)


def _content(services: NotesServices, data: TopicRefIn) -> ContentOut:
    found = services.topics.content_of(data.ref, data.project)
    return ContentOut(found.topics, found.active, found.archived)


def _deleted(services: NotesServices, data: TopicChoiceIn) -> TopicDone:
    count = services.topics.delete(data.ref, data.project, data.version, _choice(data))
    return TopicDone(data.ref, count)


def _updated(services: NotesServices, data: UpdateSettings) -> SettingsOut:
    changed = services.settings.update(data.max_topic_depth, data.review_days)
    return SettingsOut(changed.max_topic_depth, changed.review_days)

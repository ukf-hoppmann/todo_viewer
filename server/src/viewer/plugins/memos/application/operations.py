"""Ein- und Ausgaben und Operationen des Plugins `memos` (HTTP + MCP)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from viewer.core.domain.errors import InvalidInput
from viewer.core.domain.operations import HttpBinding, Operation
from viewer.plugins.memos.application.conversion import ConversionService
from viewer.plugins.memos.application.documents import DocumentService
from viewer.plugins.memos.application.due_watch import DueWatch
from viewer.plugins.memos.application.hints import HintService, ItemHint
from viewer.plugins.memos.application.memos import (
    DueEntry,
    IndexedMemo,
    IndexedTopic,
    MemoDetail,
    MemoService,
    TriggerView,
)
from viewer.plugins.memos.application.ports import Document
from viewer.plugins.memos.application.relocation import RelocationService
from viewer.plugins.memos.application.settings import SettingsService
from viewer.plugins.memos.application.topics import TopicService
from viewer.plugins.memos.application.triggers import TriggerService
from viewer.plugins.memos.domain.due import due_since
from viewer.plugins.memos.domain.hints import Hint, decision_options
from viewer.plugins.memos.domain.model import Topic
from viewer.plugins.memos.domain.topics import Choice


class MemosServices:
    """Die Dienste des Plugins."""

    def __init__(
        self,
        memos: MemoService,
        topics: TopicService,
        documents: DocumentService,
        settings: SettingsService,
        triggers: TriggerService,
        hints: HintService,
        conversion: ConversionService,
        relocation: RelocationService,
        participant: Any,
        due_watch: DueWatch,
    ) -> None:
        self.memos = memos
        self.topics = topics
        self.documents = documents
        self.settings = settings
        self.triggers = triggers
        self.hints = hints
        self.conversion = conversion
        self.relocation = relocation
        self.participant = participant
        self.due_watch = due_watch


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
    #: Offene Memos im Topic und in den Unter-Topics, davon fällige.
    open_memos: int
    due_memos: int
    version: int


@dataclass(frozen=True)
class MemoIndexOut:
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
class MemosIndexOut:
    topics: list[TopicOut]
    memos: list[MemoIndexOut]


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
class MemoHintOut:
    uid: str
    #: `item_completed`, `item_rejected`, `item_deleted`, `item_retyped` (an Memos) oder `memo_dropped`,
    #: `memo_promoted` (an Items).
    kind: str
    created_at: datetime
    source: TargetRef | None
    #: Die möglichen Entscheidungen.
    decisions: list[str]


@dataclass(frozen=True)
class MemoOut:
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
    #: Von der Wurzel bis zum Topic des Memos.
    path: list[TopicRef]
    review_at: datetime | None
    trigger_mode: str
    documents: list[str]
    version: int
    deleted: bool
    #: Warum das Memo fällig ist (`trigger`, `hint`, `topic_due`, `review_expired`), sonst leer.
    reason: str | None
    triggers: list[TriggerOut]
    #: Die offenen Hinweise an das Memo.
    hints: list[MemoHintOut]


@dataclass(frozen=True)
class ContentOut:
    topics: int
    active: int
    archived: int


@dataclass(frozen=True)
class TopicDone:
    uid: str
    #: Bei `delete_topic`: Zahl der in den Papierkorb gelegten Elemente (Topics und Memos).
    count: int = 0


@dataclass(frozen=True)
class DueMemoOut:
    uid: str
    project_uid: str
    label: str
    summary: str
    review_at: datetime | None
    #: Warum fällig: `trigger`, `hint`, `topic_due` oder `review_expired`.
    version: int
    reason: str
    #: Die Namen der Topics von der Wurzel bis zum Memo.
    path: list[str]
    triggers: list[TriggerOut]
    hints: list[MemoHintOut]
    #: Seit wann das Memo fällig ist (nach seinem Grund, siehe `due_since`).
    due_since: datetime | None


@dataclass(frozen=True)
class DueOut:
    count: int
    memos: list[DueMemoOut]


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
class MemosIndexIn:
    #: Komma-getrennte Projekt-`uid`s; ohne Angabe alle Projekte.
    projects: str | None = None
    #: Komma-getrennte Status (`waiting`, `due`, `snoozed`, `done`, `dropped`, `promoted`); ohne Angabe alle.
    statuses: str | None = None
    query: str = ""


@dataclass(frozen=True)
class DueIn:
    projects: str | None = None


@dataclass(frozen=True)
class GetMemo:
    ref: str
    project: str | None = None


@dataclass(frozen=True)
class CreateMemo:
    project: str
    #: `summary` ist Pflicht; dazu `body`, `topic` (uid), `review_at` (ISO), `trigger_mode` (`any`/`all`).
    fields: dict[str, Any]


@dataclass(frozen=True)
class UpdateMemo:
    ref: str
    version: int
    #: Geändert werden nur die genannten Felder (`summary`, `body`, `topic`, `review_at`, `trigger_mode`); `null`
    #: leert `body`, `topic` und `review_at`. Ein geänderter Text setzt ein neues Prüfdatum, wenn keines mitkommt.
    fields: dict[str, Any]
    project: str | None = None


@dataclass(frozen=True)
class MemoAction:
    ref: str
    version: int
    project: str | None = None


@dataclass(frozen=True)
class MoveMemo:
    ref: str
    version: int
    #: Das Zielprojekt (uid).
    target_project: str
    #: Das Topic im Zielprojekt (uid); ohne Angabe liegt das Memo ohne Topic.
    topic: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class SnoozeMemo:
    ref: str
    version: int
    #: Neues Prüfdatum (ISO); ohne Angabe heute + Prüf-Intervall.
    review_at: str | None = None
    #: Ein neuer Auslöser (`kind`, `target`, `status`); er ersetzt alle alten. Ohne ihn feuern die gefeuerten
    #: Auslöser wieder neu und ein vorbeigegangener Topic-Termin fällt weg.
    trigger: dict[str, Any] | None = None
    project: str | None = None


@dataclass(frozen=True)
class FinishMemo:
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
    """Löschen und Archivieren eines Topics mit Inhalt verlangen eine Wahl; ohne `active_memos` und ohne
    `keep_archived` liefert die Operation `topic_has_content` mit den Zahlen."""

    ref: str
    version: int
    #: Archivierte Memos behalten (sie wandern ins Topic „Archiviert“ des Projekts).
    keep_archived: bool = False
    #: Aktive Memos: `delete` (mit dem Topic), `move` (nach `move_to`) oder beim Archivieren `archive`.
    active_memos: str | None = None
    #: Ziel von `move`: `uid` eines Topics, oder leer für „Ohne Topic“.
    move_to: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class ReactivateTopic:
    ref: str
    version: int
    project: str | None = None


@dataclass(frozen=True)
class ListMemoDocuments:
    ref: str
    project: str | None = None


@dataclass(frozen=True)
class GetMemoDocument:
    ref: str
    name: str
    project: str | None = None


@dataclass(frozen=True)
class PutMemoDocument:
    ref: str
    name: str
    content: str
    #: Die Version, die ersetzt wird; ohne Angabe wird ein neues Dokument angelegt.
    version: int | None = None
    project: str | None = None


@dataclass(frozen=True)
class AppendMemoEntry:
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
    #: Topics des Memos ist erreicht).
    kind: str
    target: str | None = None
    #: `In progress`, `Awaiting confirmation`, `Completed` oder `Rejected`.
    status: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class RemoveTrigger:
    uid: str


@dataclass(frozen=True)
class DecideHint:
    uid: str
    #: Am Hinweis an ein Memo: `keep`, `detach`, `drop`, `promote`; an ein Item: `acknowledge`.
    decision: str
    #: Die Version des Memos, auf die sich die Entscheidung stützt (Standard: die gespeicherte).
    version: int | None = None
    #: Bei `promote`: Typ und Felder des Items wie bei `promote_memo`.
    type: str | None = None
    fields: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DecisionOut:
    hint: MemoHintOut
    #: Das Memo nach der Entscheidung (bei Hinweisen an Memos).
    memo: MemoOut | None


@dataclass(frozen=True)
class ListItemHints:
    ref: str
    project: str | None = None


@dataclass(frozen=True)
class PromoteMemo:
    ref: str
    version: int
    #: Typ des neuen Items: `Epic`, `Story` oder `Task`.
    type: str
    #: Felder des Items: Pflicht `goal`, `completion_criteria` (`area` ist optional); Titel und Kurzfassung sind die des
    #: Memos, wenn nichts gegeben ist.
    fields: dict[str, Any] = field(default_factory=dict)
    project: str | None = None


@dataclass(frozen=True)
class PromotedOut:
    memo: MemoOut
    item_uid: str


@dataclass(frozen=True)
class DemoteItem:
    ref: str
    version: int
    #: Das Topic der neuen Memo (uid).
    topic: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class DemotedOut:
    memo: MemoOut
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
        entry.open_memos,
        entry.due_memos,
        t.revision,
    )


def _memo_index(entry: IndexedMemo) -> MemoIndexOut:
    n = entry.memo
    return MemoIndexOut(
        n.uid, n.project_uid, n.label, n.summary, entry.status, n.archived, n.topic_uid, n.review_at, n.revision
    )


def _target(element: Any) -> TargetRef | None:
    if element is None:
        return None
    return TargetRef(element.uid, element.label, element.title, element.kind, element.deleted_at is not None)


def _trigger_out(view: TriggerView) -> TriggerOut:
    t = view.trigger
    return TriggerOut(t.uid, t.kind, t.status, _target(view.target), t.fired_at, t.already_met, view.arrived)


def _hint_out(hint: Hint, source: Any | None) -> MemoHintOut:
    return MemoHintOut(hint.uid, hint.kind, hint.created_at, _target(source), list(decision_options(hint.side)))


def memo_out(detail: MemoDetail) -> MemoOut:
    n = detail.memo
    return MemoOut(
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
        [_hint_out(hint, detail.sources.get(hint.source_uid)) for hint in detail.hints],
    )


def _plain_topic(topic: Topic) -> TopicOut:
    return topic_out(IndexedTopic(topic, 0, 0))


def _choice(data: TopicChoiceIn) -> Choice | None:
    if data.active_memos is None and not data.keep_archived:
        return None
    if data.active_memos not in (None, "delete", "move", "archive"):
        raise InvalidInput(
            "active_memos ist delete, move oder archive",
            details={"field": "active_memos", "allowed": ["delete", "move", "archive"]},
        )
    return Choice(data.keep_archived, data.active_memos, data.move_to or None)  # type: ignore[arg-type]


def _detail(services: MemosServices, uid: str) -> MemoOut:
    return memo_out(services.memos.get(uid, None))


def _document_info(document: Document) -> DocumentInfo:
    return DocumentInfo(document.name, document.kind, document.revision, document.updated_at)


def _document_out(document: Document) -> DocumentOut:
    return DocumentOut(document.name, document.kind, document.content, document.revision, document.updated_at)


def _index(services: MemosServices, data: MemosIndexIn) -> MemosIndexOut:
    projects = _split(data.projects) if data.projects is not None else None
    result = services.memos.index(projects, _split(data.statuses), data.query)
    return MemosIndexOut([topic_out(t) for t in result.topics], [_memo_index(n) for n in result.memos])


@dataclass(frozen=True)
class MemosIndexLines:
    """Der Index als Text für Agenten: Topics und Memos je als Tabelle mit Kopfzeile."""

    topics: str
    memos: str
    topic_count: int
    memo_count: int


def _lines(services: MemosServices, data: MemosIndexIn) -> MemosIndexLines:
    projects = _split(data.projects) if data.projects is not None else None
    result = services.memos.index(projects, _split(data.statuses), data.query)
    reasons = {e.memo.uid: e.state.reason or "review_expired" for e in services.memos.due(projects)}
    labels = {t.topic.uid: t.topic.label for t in result.topics}

    def day(value: Any) -> str:
        return value.date().isoformat() if value is not None else "-"

    topics = [
        f"{t.topic.label} | {t.topic.name} | {day(t.topic.due_at)} | {t.due_memos} | {t.open_memos}"
        for t in result.topics
    ]
    memos = [
        f"{n.memo.label} | {n.status} | {reasons.get(n.memo.uid, '-')} | {day(n.memo.review_at)} | "
        f"{labels.get(n.memo.topic_uid, '-') if n.memo.topic_uid else '-'} | {n.memo.summary}"
        for n in result.memos
    ]
    return MemosIndexLines(
        "\n".join(["Label | Name | Due at | Due | Memos", *topics]),
        "\n".join(["Label | Status | Reason | Review at | Topic | Summary", *memos]),
        len(topics),
        len(memos),
    )


def _due_memo(entry: DueEntry) -> DueMemoOut:
    n = entry.memo
    return DueMemoOut(
        n.uid,
        n.project_uid,
        n.label,
        n.summary,
        n.review_at,
        n.revision,
        entry.state.reason or "review_expired",
        [topic.name for topic in entry.path],
        [_trigger_out(view) for view in entry.triggers],
        [_hint_out(hint, None) for hint in entry.hints],
        due_since(
            entry.state,
            n,
            [view.trigger for view in entry.triggers],
            entry.path[-1] if entry.path else None,
            entry.hints,
        ),
    )


def _due(services: MemosServices, data: DueIn) -> DueOut:
    projects = _split(data.projects) if data.projects is not None else None
    entries = services.memos.due(projects)
    return DueOut(len(entries), [_due_memo(entry) for entry in entries])


def _item_hint(entry: ItemHint) -> MemoHintOut:
    return _hint_out(entry.hint, entry.source)


def _decided(services: MemosServices, data: DecideHint) -> DecisionOut:
    result = services.hints.decide(data.uid, data.decision, data.version, data.type, data.fields)
    memo = _detail(services, result.memo_uid) if result.memo_uid else None
    return DecisionOut(_hint_out(result.hint, None), memo)


def _promoted(services: MemosServices, data: PromoteMemo) -> PromotedOut:
    result = services.conversion.promote(data.ref, data.project, data.version, data.type, data.fields)
    return PromotedOut(_detail(services, result.memo_uid), result.item_uid)


def _demoted(services: MemosServices, data: DemoteItem) -> DemotedOut:
    result = services.conversion.demote(data.ref, data.project, data.version, data.topic)
    return DemotedOut(_detail(services, result.memo_uid), result.item_uid)


def _finish(services: MemosServices, data: FinishMemo) -> MemoOut:
    if data.status not in ("done", "dropped"):
        raise InvalidInput("status ist done oder dropped", details={"field": "status", "allowed": ["done", "dropped"]})
    return _detail(services, services.memos.finish(data.ref, data.project, data.version, data.status))


def _settings(services: MemosServices, _data: Any) -> SettingsOut:
    current = services.settings.current()
    return SettingsOut(current.max_topic_depth, current.review_days)


OPERATIONS: tuple[Operation, ...] = (
    Operation(
        "index",
        "Topics (mit Zählern) und Memos der Projekte als flache Liste; Filter nach Status (wartet, fällig, "
        "zurückgestellt, erledigt, verworfen, befördert) und Text. Projekte und Status komma-getrennt",
        "read",
        MemosIndexIn,
        MemosIndexOut,
        _index,
        HttpBinding("GET", "/index"),
    ),
    Operation(
        "index_lines",
        "Wie memos_index, aber als kompakter Text für Agenten: Topics `Label | Name | Due at | Due | Memos` und "
        "Memos `Label | Status | Reason | Review at | Topic | Summary`",
        "read",
        MemosIndexIn,
        MemosIndexLines,
        _lines,
        HttpBinding("GET", "/index/lines"),
    ),
    Operation(
        "get_memo",
        "Eine Memo mit Langtext, Topic-Pfad, Status und Dokumenten; `ref` ist die uid oder ein Label (mit `project`)",
        "read",
        GetMemo,
        MemoOut,
        lambda s, d: memo_out(s.memos.get(d.ref, d.project)),
        HttpBinding("GET", "/memos/{ref}"),
    ),
    Operation(
        "due_memos",
        "Die fälligen Memos (Prüfdatum erreicht) mit Zahl; gleiches Ergebnis wie der Zähler der Kopfzeile",
        "read",
        DueIn,
        DueOut,
        _due,
        HttpBinding("GET", "/due"),
    ),
    Operation(
        "create_memo",
        "Legt ein Memo an (Status wartet); das Label vergibt der Server. Pflicht: summary; Prüfdatum ohne Angabe "
        "heute + Prüf-Intervall",
        "write",
        CreateMemo,
        MemoOut,
        lambda s, d: _detail(s, s.memos.create(d.project, d.fields)),
        HttpBinding("POST", "/memos"),
    ),
    Operation(
        "update_memo",
        "Ändert Felder eines Memos in Gebrauch mit Versionsprüfung (summary, body, topic, review_at, trigger_mode)",
        "write",
        UpdateMemo,
        MemoOut,
        lambda s, d: _detail(s, s.memos.update(d.ref, d.project, d.version, d.fields)),
        HttpBinding("PUT", "/memos/{ref}"),
    ),
    Operation(
        "keep_memo",
        "Behalten: das Memo bleibt, wie es ist, nur das Prüfdatum rückt um das Prüf-Intervall vor",
        "write",
        MemoAction,
        MemoOut,
        lambda s, d: _detail(s, s.memos.keep(d.ref, d.project, d.version)),
        HttpBinding("POST", "/memos/{ref}/keep"),
    ),
    Operation(
        "move_memo",
        "Verschiebt ein Memo in ein anderes Projekt: dort entsteht eine neue Memo mit neuem Label (Texte, Status, "
        "Prüfdatum, Dokumente, Verweise und Ereignis-Auslöser werden übernommen), die alte kommt in den Papierkorb. "
        "Antwort ist die neue Memo",
        "write",
        MoveMemo,
        MemoOut,
        lambda s, d: _detail(s, s.relocation.move_to_project(d.ref, d.project, d.version, d.target_project, d.topic)),
        HttpBinding("POST", "/memos/{ref}/move"),
    ),
    Operation(
        "snooze_memo",
        "Stellt ein Memo zurück auf ein neues Prüfdatum (Standard: heute + Prüf-Intervall)",
        "write",
        SnoozeMemo,
        MemoOut,
        lambda s, d: _detail(s, s.memos.snooze(d.ref, d.project, d.version, d.review_at, d.trigger)),
        HttpBinding("POST", "/memos/{ref}/snooze"),
    ),
    Operation(
        "finish_memo",
        "Schließt ein Memo als erledigt (done) oder verworfen (dropped) ab; sie liegt dann im Archiv",
        "write",
        FinishMemo,
        MemoOut,
        _finish,
        HttpBinding("POST", "/memos/{ref}/finish"),
    ),
    Operation(
        "restore_memo",
        "Holt ein Memo aus dem Archiv zurück auf „wartet“ mit neuem Prüfdatum",
        "write",
        MemoAction,
        MemoOut,
        lambda s, d: _detail(s, s.memos.restore(d.ref, d.project, d.version)),
        HttpBinding("POST", "/memos/{ref}/restore"),
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
        "Zahl der Unter-Topics sowie aktiven und archivierten Memos in einem Topic (für den Auswahldialog)",
        "read",
        TopicRefIn,
        ContentOut,
        lambda s, d: _content(s, d),
        HttpBinding("GET", "/topics/{ref}/content"),
    ),
    Operation(
        "archive_topic",
        "Archiviert ein Topic samt Unter-Topics. Mit Inhalt braucht es eine Wahl: archivierte Memos behalten, "
        "aktive Memos verschieben (`move`) oder mitarchivieren (`archive`)",
        "write",
        TopicChoiceIn,
        TopicDone,
        lambda s, d: TopicDone(s.topics.archive(d.ref, d.project, d.version, _choice(d))),
        HttpBinding("POST", "/topics/{ref}/archive"),
    ),
    Operation(
        "reactivate_topic",
        "Aktiviert ein archiviertes Topic samt Unter-Topics wieder; Memos, die nur seinetwegen archiviert waren, "
        "kommen zurück",
        "write",
        ReactivateTopic,
        TopicDone,
        lambda s, d: TopicDone(s.topics.reactivate(d.ref, d.project, d.version)),
        HttpBinding("POST", "/topics/{ref}/reactivate"),
    ),
    Operation(
        "delete_topic",
        "Legt ein Topic in den Papierkorb. Mit Inhalt braucht es eine Wahl: archivierte Memos behalten, aktive "
        "Memos verschieben (`move`) oder mit löschen (`delete`); nicht Gewähltes geht mit in den Papierkorb",
        "write",
        TopicChoiceIn,
        TopicDone,
        lambda s, d: _deleted(s, d),
        HttpBinding("POST", "/topics/{ref}/delete"),
    ),
    Operation(
        "list_memo_documents",
        "Die Dokumente eines Memos (Name, Art, Version)",
        "read",
        ListMemoDocuments,
        list[DocumentInfo],
        lambda s, d: [_document_info(doc) for doc in s.documents.list_documents(d.ref, d.project)],
        HttpBinding("GET", "/memos/{ref}/documents"),
    ),
    Operation(
        "get_memo_document",
        "Ein Dokument eines Memos mit Inhalt und Version",
        "read",
        GetMemoDocument,
        DocumentOut,
        lambda s, d: _document_out(s.documents.get_document(d.ref, d.project, d.name)),
        HttpBinding("GET", "/memos/{ref}/documents/{name}"),
    ),
    Operation(
        "put_memo_document",
        "Ersetzt ein Dokument in `version` oder legt ein neues an (<LABEL>_notes.md, <LABEL>_spec[_<thema>].md)",
        "write",
        PutMemoDocument,
        DocumentOut,
        lambda s, d: _document_out(s.documents.put_document(d.ref, d.project, d.name, d.content, d.version)),
        HttpBinding("PUT", "/memos/{ref}/documents/{name}"),
    ),
    Operation(
        "append_memo_entry",
        "Hängt einen datierten Eintrag (Thema, Discussed, Decided, Open) an die Notizen eines Memos",
        "write",
        AppendMemoEntry,
        DocumentOut,
        lambda s, d: _document_out(s.documents.append_memo(d.ref, d.project, d.topic, d.discussed, d.decided, d.open)),
        HttpBinding("POST", "/memos/{ref}/entries"),
    ),
    Operation(
        "add_trigger",
        "Legt einen Auslöser an: ein Item erreicht einen Status (`event`, mit `target` und `status`) oder der "
        "Termin des Topics des Memos ist erreicht (`topic_date`). Erreicht er sein Ziel, wird das Memo fällig; hat "
        "das Item den Status schon, feuert er sofort",
        "write",
        AddTrigger,
        MemoOut,
        lambda s, d: _detail(s, s.triggers.add(d.ref, d.project, d.kind, d.target, d.status)),
        HttpBinding("POST", "/memos/{ref}/triggers"),
    ),
    Operation(
        "remove_trigger",
        "Entfernt einen Auslöser eines Memos in Gebrauch (mit seiner Verknüpfung)",
        "write",
        RemoveTrigger,
        MemoOut,
        lambda s, d: _detail(s, s.triggers.remove(d.uid)),
        HttpBinding("DELETE", "/triggers/{uid}"),
    ),
    Operation(
        "decide_hint",
        "Entscheidet einen offenen Hinweis: an einem Memo: keep (Prüfdatum rückt), detach (Verknüpfung zum Item "
        "entfernen), drop (Memo verwerfen) oder promote (zum Item befördern); an einem Item acknowledge",
        "write",
        DecideHint,
        DecisionOut,
        _decided,
        HttpBinding("POST", "/hints/{uid}/decide"),
    ),
    Operation(
        "list_item_hints",
        "Die offenen Hinweise an ein Item des Backlogs (ein Memo, die auf es verweist, wurde verworfen oder befördert)",
        "read",
        ListItemHints,
        list[MemoHintOut],
        lambda s, d: [_item_hint(entry) for entry in s.hints.list_for_item(d.ref, d.project)],
        HttpBinding("GET", "/items/{ref}/hints"),
    ),
    Operation(
        "promote_memo",
        "Befördert ein Memo zu einem Item (Epic, Story oder Task) im selben Projekt: Langtext, Notizen und Specs "
        "werden übernommen, das Memo ist danach befördert (Archiv) und mit dem Item verknüpft (origin). Pflicht: type "
        "und die Felder goal, completion_criteria (area ist optional)",
        "write",
        PromoteMemo,
        PromotedOut,
        _promoted,
        HttpBinding("POST", "/memos/{ref}/promote"),
    ),
    Operation(
        "demote_item",
        "Stuft ein offenes Item (Status Open, ohne Kinder, von dem nichts abhängt) zu einem Memo zurück; das Item wird "
        "abgelehnt (Rejected), Notizen und Specs wandern an das Memo",
        "write",
        DemoteItem,
        DemotedOut,
        _demoted,
        HttpBinding("POST", "/items/{ref}/demote"),
    ),
    Operation(
        "get_memos_settings",
        "Prüf-Intervall (Tage) und größte Topic-Tiefe",
        "read",
        NoSettingsInput,
        SettingsOut,
        _settings,
        HttpBinding("GET", "/settings"),
    ),
    Operation(
        "update_memos_settings",
        "Ändert Prüf-Intervall und größte Topic-Tiefe",
        "write",
        UpdateSettings,
        SettingsOut,
        lambda s, d: _updated(s, d),
        HttpBinding("PUT", "/settings"),
        mcp=False,
    ),
)


def _content(services: MemosServices, data: TopicRefIn) -> ContentOut:
    found = services.topics.content_of(data.ref, data.project)
    return ContentOut(found.topics, found.active, found.archived)


def _deleted(services: MemosServices, data: TopicChoiceIn) -> TopicDone:
    count = services.topics.delete(data.ref, data.project, data.version, _choice(data))
    return TopicDone(data.ref, count)


def _updated(services: MemosServices, data: UpdateSettings) -> SettingsOut:
    changed = services.settings.update(data.max_topic_depth, data.review_days)
    return SettingsOut(changed.max_topic_depth, changed.review_days)

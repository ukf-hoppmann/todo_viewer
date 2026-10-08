"""HTTP contract of the notes part of API v2. Topics and notes are addressed by project plus label.

Points in time are ISO timestamps with a time zone; they are returned in UTC.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictInt, model_validator

from todo_viewer.application.services import (
    DecisionResult,
    DueNote,
    IndexedTopic,
    LinkedNote,
    LinkInfo,
    NoteDocument,
    NotesIndex,
    NoteView,
    TrashContents,
)
from todo_viewer.domain.notes import (
    LinkTarget,
    NewTrigger,
    Notice,
    NoticeDecision,
    Reachability,
    TargetKind,
    Topic,
    Trigger,
    TriggerKind,
    decision_options,
    target_display,
)
from todo_viewer.domain.notes import NotesSettings as NotesSettingsValue

from .schemas import ItemOut


class TopicOut(BaseModel):
    project: str
    label: str
    name: str
    parent: str | None = Field(description="Label of the parent topic")
    due_at: datetime | None
    created: datetime | None
    deleted: datetime | None = Field(description="When the topic was moved to the trash; null if in use")

    @classmethod
    def of(cls, topic: Topic) -> TopicOut:
        return cls(project=topic.project, label=topic.label, name=topic.name, parent=topic.parent,
                   due_at=topic.due_at, created=topic.created, deleted=topic.deleted)


class TopicIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    parent: str | None = None
    due_at: AwareDatetime | None = None


class TopicEditIn(BaseModel):
    """Only the fields sent change; `due_at: null` removes the due date."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    due_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def _not_empty(self) -> TopicEditIn:
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        return self


class TopicMoveIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parent: str | None = Field(default=None, description="Label of the new parent; null makes it a root topic")


class NoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(description="One line; this is what the index shows")
    body: str | None = Field(default=None, description="The long text")
    topic: str | None = Field(default=None, description="Label of a topic of the same project")
    review_at: AwareDatetime | None = Field(default=None, description="Default: now plus `notes.review_days`")
    trigger_mode: Literal["any", "all"] = "any"


class NoteEditIn(BaseModel):
    """Only the fields sent change. null clears `body`, `topic`, and `review_at`."""

    model_config = ConfigDict(extra="forbid")

    version: str
    summary: str | None = None
    body: str | None = None
    topic: str | None = None
    review_at: AwareDatetime | None = None
    trigger_mode: Literal["any", "all"] | None = None

    @model_validator(mode="after")
    def _not_empty(self) -> NoteEditIn:
        if self.model_fields_set <= {"version"}:
            raise ValueError("at least one field to change is required")
        if "summary" in self.model_fields_set and self.summary is None:
            raise ValueError("summary cannot be cleared")
        if "trigger_mode" in self.model_fields_set and self.trigger_mode is None:
            raise ValueError("trigger_mode cannot be cleared")
        return self

    def cleared(self, field: str) -> bool:
        return field in self.model_fields_set and getattr(self, field) is None


class NoteMoveIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    project: str = Field(description="The project the note moves to")
    topic: str | None = Field(default=None, description="Label of a topic of the new project")


class NoteDocumentOut(BaseModel):
    name: str = Field(description="`<LABEL>_notes.md`, `<LABEL>_spec.md`, or `<LABEL>_spec_<topic>.md`")
    kind: Literal["notes", "spec"]
    content: str
    version: str = Field(description="Changes with the content; required to replace the document")

    @classmethod
    def of(cls, document: NoteDocument) -> NoteDocumentOut:
        return cls(name=document.name, kind=document.kind.value,
                   content=document.content, version=document.version)


class NoteDocumentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(description="The whole new text of the document")
    version: str | None = Field(description="Version last read; null to create a new document")


class NoteDocumentRefOut(BaseModel):
    name: str
    kind: Literal["notes", "spec"]


class TriggerIn(BaseModel):
    """A time trigger needs `at`; an event trigger `target` and `target_status`; a topic trigger the note's topic."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["time", "event", "topic_due"]
    at: AwareDatetime | None = Field(default=None, description="time: the moment it arrives")
    target: str | None = Field(default=None, description="event: label of the item that is watched")
    target_project: str | None = Field(default=None, description="event: its project; default: the note's project")
    target_status: str | None = Field(
        default=None, description="event: In progress, Awaiting confirmation, Completed, or Rejected")

    def new(self, project: str) -> NewTrigger:
        target = None if self.target is None else LinkTarget(TargetKind.ITEM, self.target_project or project,
                                                             self.target)
        return NewTrigger(TriggerKind(self.kind), at=self.at, target=target, target_status=self.target_status)


class NoteFinishIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    status: Literal["done", "dropped"]


class NoteSnoozeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    review_at: AwareDatetime | None = Field(default=None, description="Default: now plus `notes.review_days`")
    trigger: TriggerIn | None = Field(default=None, description="Replaces all old triggers")


class LinkIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["item", "topic", "note"] = Field(description="What the note points at")
    target: str = Field(description="Label of the item, topic, or note")
    target_project: str | None = Field(default=None, description="Its project; default: the note's project")
    role: Literal["reference", "origin"] = "reference"


class LinkOut(BaseModel):
    id: int
    note: str = Field(description="Label of the note the link starts at")
    project: str = Field(description="Project of that note")
    kind: str
    target_project: str
    target: str = Field(description="Label of the item, topic, or note it points at")
    target_display: str = Field(description="The target as 'project · label'")
    role: str = Field(description="reference, origin, or trigger (the link of an event trigger)")
    reachable: bool = Field(description="False if the project of the target item is not registered or its backlog "
                                        "cannot be read. Computed on every read, never stored")
    unreachable_reason: str | None = Field(description="project_not_registered or source_unreadable; null if reachable")

    @classmethod
    def of(cls, info: LinkInfo) -> LinkOut:
        link = info.link
        return cls(id=link.id, note=link.note, project=link.project, kind=link.target.kind.value,
                   target_project=link.target.project, target=link.target.label,
                   target_display=target_display(link.target.project, link.target.label), role=link.role.value,
                   reachable=info.reachability.reachable, unreachable_reason=info.reachability.reason)


class LinkedNoteOut(BaseModel):
    """A note that points at something; the long text stays out, read the note for it."""

    project: str
    label: str
    summary: str
    status: str
    role: str
    link_id: int

    @classmethod
    def of(cls, linked: LinkedNote) -> LinkedNoteOut:
        note = linked.view.note
        return cls(project=note.project, label=note.label, summary=note.summary,
                   status=linked.view.evaluation.status.value, role=linked.link.role.value, link_id=linked.link.id)


class TriggerOut(BaseModel):
    id: int
    kind: str
    at: datetime | None
    target_project: str | None
    target: str | None = Field(description="Event: label of the item that is watched")
    target_display: str | None = Field(description="Event: the item as 'project · label'")
    reachable: bool | None = Field(description="Event: false if the project of the watched item cannot be reached; "
                                               "null for other triggers and where links were not checked")
    unreachable_reason: str | None = Field(description="project_not_registered or source_unreadable")
    target_status: str | None
    fired_at: datetime | None
    already_met: bool

    @classmethod
    def of(cls, trigger: Trigger, reachability: Mapping[LinkTarget, Reachability] | None = None) -> TriggerOut:
        target = trigger.target
        reach = None if target is None or reachability is None else reachability.get(target)
        return cls(id=trigger.id, kind=trigger.kind.value, at=trigger.at,
                   target_project=None if target is None else target.project,
                   target=None if target is None else target.label,
                   target_display=None if target is None else target_display(target.project, target.label),
                   reachable=None if reach is None else reach.reachable,
                   unreachable_reason=None if reach is None else reach.reason, target_status=trigger.target_status,
                   fired_at=trigger.fired_at, already_met=trigger.already_met)


class NoticeCounterpartOut(BaseModel):
    kind: str = Field(description="item for a notice to a note, note for a notice to an item")
    project: str
    label: str


class NoticeOut(BaseModel):
    """A notice that a linked item or note changed. It stays open until someone decides."""

    id: int
    side: Literal["note", "item"] = Field(description="Who is told: the note, or the item")
    project: str = Field(description="Project of the one who is told")
    label: str = Field(description="Label of the one who is told: a note label, or an item ID")
    cause: str = Field(description="item_completed, item_rejected, item_deleted, item_retyped, "
                                   "project_unreachable, note_dropped, or note_promoted")
    counterpart: NoticeCounterpartOut = Field(description="The other end: the item for a note, the note for an item")
    created_at: datetime
    decided_at: datetime | None = Field(description="null while the notice is open")
    decision: str | None = Field(description="keep, detach, drop, promote, or acknowledge; null while open")
    options: list[str] = Field(description="What can be chosen: keep, detach, drop, promote for a note; "
                                           "acknowledge for an item")

    @classmethod
    def of(cls, notice: Notice) -> NoticeOut:
        target = notice.counterpart
        return cls(id=notice.id, side=notice.side.value, project=notice.project,
                   label=notice.label, cause=notice.cause.value,
                   counterpart=NoticeCounterpartOut(kind=target.kind.value, project=target.project,
                                                    label=target.label),
                   created_at=notice.created_at, decided_at=notice.decided_at,
                   decision=None if notice.decision is None else notice.decision.value,
                   options=[d.value for d in decision_options(notice.side)])


class PromoteFieldsIn(BaseModel):
    """What the new item needs beyond the note: type, area, goal, completion criteria, and the optional rest."""

    model_config = ConfigDict(extra="forbid")

    item_type: Literal["Epic", "Story", "Task"]
    title: str | None = Field(default=None, description="Default: the note's summary")
    summary: str | None = Field(default=None, description="Default: the note's summary")
    area: str
    goal: str
    completion_criteria: str
    parent: str | None = None
    required_for_parent: str | None = Field(default=None, description="Yes or No; required with a parent")
    priority: str | None = Field(default=None, description="Default: Normal")
    dependencies: list[str] | None = None

    def given(self) -> dict[str, object]:
        """The item fields sent, without the type and the note's version."""
        return {name: getattr(self, name) for name in PromoteFieldsIn.model_fields
                if name != "item_type" and name in self.model_fields_set}


class PromoteIn(PromoteFieldsIn):
    version: str = Field(description="The note's version as last read; a changed note answers 409")


class NoticeDecisionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: NoticeDecision
    version: str | None = Field(default=None, description="Version of the note the decision is based on; "
                                                          "default: the stored one")
    promotion: PromoteFieldsIn | None = Field(
        default=None, description="With decision `promote`: the fields of the item the note becomes; the note is "
                                  "promoted first, then the notice is decided")


class NoteOut(BaseModel):
    project: str
    label: str
    version: str = Field(description="Changes with every change of the note; required for edits")
    summary: str
    body: str | None
    status: str = Field(description="The effective status: `due` is derived from the triggers and the review date")
    stored_status: str = Field(description="The stored status (waiting, snoozed, done, dropped, promoted)")
    reason: str | None = Field(description="Why the note is due: trigger, notice, review_expired, or topic_due")
    topic: str | None
    review_at: datetime | None
    trigger_mode: str
    triggers: list[TriggerOut]
    open_notices: list[NoticeOut] = Field(description="Notices that nobody has decided yet; they make the note due")
    archived: bool
    deleted: datetime | None
    created: datetime | None
    updated: datetime | None

    @classmethod
    def of(cls, view: NoteView) -> NoteOut:
        note = view.note
        return cls(project=note.project, label=note.label, version=note.version, summary=note.summary,
                   body=note.body, status=view.evaluation.status.value, stored_status=note.status.value,
                   reason=None if view.evaluation.reason is None else view.evaluation.reason.value,
                   topic=note.topic, review_at=note.review_at, trigger_mode=note.trigger_mode.value,
                   triggers=[TriggerOut.of(t, view.reachability) for t in view.triggers],
                   open_notices=[NoticeOut.of(n) for n in view.open_notices], archived=note.archived,
                   deleted=note.deleted, created=note.created, updated=note.updated)


class NoticeDecisionOut(BaseModel):
    notice: NoticeOut
    note: NoteOut | None = Field(description="The note after the decision; null for a notice to an item")
    item: ItemOut | None = Field(default=None, description="The item the note became, for decision `promote`")

    @classmethod
    def of(cls, result: DecisionResult, item: ItemOut | None = None) -> NoticeDecisionOut:
        return cls(notice=NoticeOut.of(result.notice),
                   note=None if result.note is None else NoteOut.of(result.note), item=item)


class PromoteOut(BaseModel):
    note: NoteOut = Field(description="The note, now promoted and archived")
    item: ItemOut = Field(description="The item the note became; the note links to it with role `origin`")


class DemoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(description="The item's version as last read; a changed item answers 409")
    topic: str | None = Field(default=None, description="Label of a topic of the item's project for the new note")


class DemoteOut(BaseModel):
    item: ItemOut = Field(description="The item, now Rejected with the resolution 'zur Notiz zurückgestuft'")
    note: NoteOut = Field(description="The new note; it links to the item with role `origin`")


class TrashOut(BaseModel):
    topics: list[TopicOut]
    notes: list[NoteOut]

    @classmethod
    def of(cls, trash: TrashContents) -> TrashOut:
        return cls(topics=[TopicOut.of(t) for t in trash.topics], notes=[NoteOut.of(n) for n in trash.notes])


class NotesSettingsOut(BaseModel):
    max_topic_depth: int = Field(description="How many levels topics may nest (`notes.max_topic_depth`)")
    review_days: int = Field(description="Days until a note must be looked at again (`notes.review_days`)")

    @classmethod
    def of(cls, settings: NotesSettingsValue) -> NotesSettingsOut:
        return cls(max_topic_depth=settings.max_topic_depth, review_days=settings.review_days)


class NotesSettingsIn(BaseModel):
    """Only the options sent change. Whole numbers: depth 1 to 10, review days 1 to 3650."""

    model_config = ConfigDict(extra="forbid")

    max_topic_depth: StrictInt | None = None
    review_days: StrictInt | None = None

    @model_validator(mode="after")
    def _given(self) -> NotesSettingsIn:
        if not self.model_fields_set:
            raise ValueError("at least one option is required")
        if any(getattr(self, name) is None for name in self.model_fields_set):
            raise ValueError("an option cannot be cleared")
        return self


class IndexNoteOut(BaseModel):
    """A note without its long text; read the note for that."""

    project: str
    label: str
    summary: str
    status: str = Field(description="waiting, due, snoozed, done, dropped, or promoted")
    reason: str | None = Field(description="Why the note is due: trigger, notice, review_expired, or topic_due")
    review_at: datetime | None = Field(description="When the note must be looked at again at the latest")
    topic: str | None
    archived: bool

    @classmethod
    def of(cls, view: NoteView) -> IndexNoteOut:
        note = view.note
        return cls(project=note.project, label=note.label, summary=note.summary, status=view.evaluation.status.value,
                   reason=None if view.evaluation.reason is None else view.evaluation.reason.value,
                   review_at=note.review_at, topic=note.topic, archived=note.archived)


class IndexTopicOut(BaseModel):
    project: str
    label: str
    name: str
    parent: str | None
    path: list[str] = Field(description="The names from the root topic down to this one")
    due_at: datetime | None
    due: bool = Field(description="The due date has passed")
    note_count: int = Field(description="Open notes directly in this topic")

    @classmethod
    def of(cls, indexed: IndexedTopic) -> IndexTopicOut:
        topic = indexed.topic
        return cls(project=topic.project, label=topic.label, name=topic.name, parent=topic.parent,
                   path=list(indexed.path), due_at=topic.due_at, due=indexed.due, note_count=indexed.note_count)


class NotesIndexOut(BaseModel):
    topics: list[IndexTopicOut]
    notes: list[IndexNoteOut]

    @classmethod
    def of(cls, index: NotesIndex) -> NotesIndexOut:
        return cls(topics=[IndexTopicOut.of(t) for t in index.topics], notes=[IndexNoteOut.of(n) for n in index.notes])


class DueCountOut(BaseModel):
    count: int = Field(description="Due notes in all projects")
    by_project: dict[str, int]


class DueNoteOut(IndexNoteOut):
    topic_path: list[str] = Field(description="The names of the topic and its parents; empty without a topic")
    triggers: list[TriggerOut] = Field(description="The triggers that have arrived")
    actions: list[Literal["keep", "snooze", "done", "dropped", "detach", "drop", "promote"]] = Field(
        description="What can be done with the note: keep, snooze, or close it as done or dropped; for the reason "
                    "notice: keep, detach, drop, or promote (decide the notice)")

    @classmethod
    def of_due(cls, due: DueNote) -> DueNoteOut:
        base = IndexNoteOut.of(due.view)
        return cls(**base.model_dump(), topic_path=list(due.topic_path),
                   triggers=[TriggerOut.of(t, due.view.reachability) for t in due.fired], actions=list(due.actions))  # type: ignore[arg-type]

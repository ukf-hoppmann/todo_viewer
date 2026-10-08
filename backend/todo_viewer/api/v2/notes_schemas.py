"""HTTP contract of the notes part of API v2. Topics and notes are addressed by project plus label.

Points in time are ISO timestamps with a time zone; they are returned in UTC.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from todo_viewer.application.services import LinkedNote, NoteDocument, NoteView, TrashContents
from todo_viewer.domain.notes import Link, LinkTarget, NewTrigger, TargetKind, Topic, Trigger, TriggerKind


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
    role: str = Field(description="reference, origin, or trigger (the link of an event trigger)")

    @classmethod
    def of(cls, link: Link) -> LinkOut:
        return cls(id=link.id, note=link.note, project=link.project, kind=link.target.kind.value,
                   target_project=link.target.project, target=link.target.label, role=link.role.value)


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
    target_status: str | None
    fired_at: datetime | None
    already_met: bool

    @classmethod
    def of(cls, trigger: Trigger) -> TriggerOut:
        target = trigger.target
        return cls(id=trigger.id, kind=trigger.kind.value, at=trigger.at,
                   target_project=None if target is None else target.project,
                   target=None if target is None else target.label, target_status=trigger.target_status,
                   fired_at=trigger.fired_at, already_met=trigger.already_met)


class NoteOut(BaseModel):
    project: str
    label: str
    version: str = Field(description="Changes with every change of the note; required for edits")
    summary: str
    body: str | None
    status: str = Field(description="The effective status: `due` is derived from the triggers and the review date")
    stored_status: str = Field(description="The stored status (waiting, snoozed, done, dropped, promoted)")
    reason: str | None = Field(description="Why the note is due: trigger, review_expired, or topic_due")
    topic: str | None
    review_at: datetime | None
    trigger_mode: str
    triggers: list[TriggerOut]
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
                   triggers=[TriggerOut.of(t) for t in view.triggers], archived=note.archived,
                   deleted=note.deleted, created=note.created, updated=note.updated)


class TrashOut(BaseModel):
    topics: list[TopicOut]
    notes: list[NoteOut]

    @classmethod
    def of(cls, trash: TrashContents) -> TrashOut:
        return cls(topics=[TopicOut.of(t) for t in trash.topics], notes=[NoteOut.of(n) for n in trash.notes])

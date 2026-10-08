"""Topics, notes, and links of API v2. Everything is addressed by project (name) plus label."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from todo_viewer.domain.notes import NoteStatus, TriggerMode

from ..dependencies import Notes, Topics
from .notes_schemas import (
    NoteEditIn,
    NoteFinishIn,
    NoteIn,
    NoteMoveIn,
    NoteOut,
    NoteSnoozeIn,
    TopicEditIn,
    TopicIn,
    TopicMoveIn,
    TopicOut,
    TrashOut,
    TriggerIn,
)
from .schemas import ErrorOut, VersionIn

ERRORS: dict[int | str, dict[str, Any]] = {
    status: {"model": ErrorOut} for status in (400, 403, 404, 409)
}

router = APIRouter(prefix="/api/v2/projects/{project}", responses=ERRORS)


@router.post("/notes", tags=["notes"], status_code=201)
def create_note(project: str, body: NoteIn, notes: Notes) -> NoteOut:
    """Creates an open note. Without `review_at` it must be looked at again after `notes.review_days`."""
    return NoteOut.of(notes.create(project, body.summary, body.body, body.topic, body.review_at,
                                   TriggerMode(body.trigger_mode)))


@router.get("/notes/{label}", tags=["notes"])
def get_note(project: str, label: str, notes: Notes) -> NoteOut:
    """One note, with its triggers and its state right now (`status` is `due` when a trigger arrived or the review
    date passed). Also finds archived notes and notes in the trash."""
    return NoteOut.of(notes.show(project, label))


@router.patch("/notes/{label}", tags=["notes"])
def edit_note(project: str, label: str, body: NoteEditIn, notes: Notes) -> NoteOut:
    """Changes the fields sent, in `version`; 409 version_conflict if the note changed in the meantime.

    A changed text sets a new review date unless `review_at` is sent. null clears `body`, `topic`, `review_at`.
    Closed notes and notes in the trash cannot be changed (409 note_closed / note_deleted).
    """
    mode = None if body.trigger_mode is None else TriggerMode(body.trigger_mode)
    return NoteOut.of(notes.edit(
        project, label, body.version, summary=body.summary, body=body.body, clear_body=body.cleared("body"),
        topic=body.topic, clear_topic=body.cleared("topic"), review_at=body.review_at,
        clear_review_at=body.cleared("review_at"),
        trigger_mode=mode))


@router.post("/notes/{label}/keep", tags=["notes"])
def keep_note(project: str, label: str, body: VersionIn, notes: Notes) -> NoteOut:
    """The owner looked at the note and keeps it as it is: only the review date moves."""
    return NoteOut.of(notes.keep(project, label, body.version))


@router.post("/notes/{label}/move", tags=["notes"])
def move_note(project: str, label: str, body: NoteMoveIn, notes: Notes) -> NoteOut:
    """Moves the note to another project: it is created there with a new label (triggers, links, and documents come
    along) and the old one goes to the trash. The answer is the new note; its `label` is the new one.
    """
    return NoteOut.of(notes.move_to_project(project, label, body.version, body.project, body.topic))


@router.post("/notes/{label}/triggers", tags=["notes"], status_code=201)
def add_trigger(project: str, label: str, body: TriggerIn, notes: Notes) -> NoteOut:
    """Adds a trigger that makes the note due and returns the note. An event trigger also links the note to the
    item; if the item has the status already, the trigger fires at once and is marked `already_met`."""
    notes.add_trigger(project, label, body.new(project))
    return NoteOut.of(notes.show(project, label))


@router.delete("/notes/{label}/triggers/{trigger_id}", tags=["notes"])
def remove_trigger(project: str, label: str, trigger_id: int, notes: Notes) -> NoteOut:
    """Removes the trigger and the link of an event trigger; returns the note."""
    return NoteOut.of(notes.remove_trigger(project, label, trigger_id))


@router.post("/notes/{label}/finish", tags=["notes"])
def finish_note(project: str, label: str, body: NoteFinishIn, notes: Notes) -> NoteOut:
    """Closes the note as `done` or `dropped`; it moves to the archive and cannot be changed until restored."""
    return NoteOut.of(notes.finish(project, label, body.version, NoteStatus(body.status)))


@router.post("/notes/{label}/snooze", tags=["notes"])
def snooze_note(project: str, label: str, body: NoteSnoozeIn, notes: Notes) -> NoteOut:
    """Back to waiting with a new review date. Fired triggers are reset; a given `trigger` replaces all old ones,
    and without it the triggers that cannot arrive again (time, topic) are removed."""
    trigger = None if body.trigger is None else body.trigger.new(project)
    return NoteOut.of(notes.snooze(project, label, body.version, body.review_at, trigger))


@router.delete("/notes/{label}", tags=["notes"])
def delete_note(project: str, label: str, notes: Notes) -> NoteOut:
    """Moves the note to the trash. Removing it for good is not possible over HTTP; the owner does that."""
    return NoteOut.of(notes.delete_note(project, label))


@router.post("/notes/{label}/restore", tags=["notes"])
def restore_note(project: str, label: str, notes: Notes) -> NoteOut:
    """From the archive or the trash back to waiting, with a new review date. Refused (409 topic_deleted) while its
    topic is in the trash."""
    return NoteOut.of(notes.restore_note(project, label))


@router.get("/trash", tags=["trash"])
def trash(project: str, notes: Notes) -> TrashOut:
    """The topics and notes of the project in the trash."""
    return TrashOut.of(notes.trash(project))


@router.get("/topics", tags=["topics"])
def list_topics(project: str, topics: Topics, include_deleted: bool = False) -> list[TopicOut]:
    """The topics of a project; with `include_deleted` the ones in the trash as well."""
    return [TopicOut.of(t) for t in topics.list(project, include_deleted)]


@router.post("/topics", tags=["topics"], status_code=201)
def create_topic(project: str, body: TopicIn, topics: Topics) -> TopicOut:
    """Creates a topic, optionally below `parent`. Refused beyond `notes.max_topic_depth` (400 topic_too_deep)."""
    return TopicOut.of(topics.create(project, body.name, body.parent, body.due_at))


@router.get("/topics/{label}", tags=["topics"])
def get_topic(project: str, label: str, topics: Topics) -> TopicOut:
    return TopicOut.of(topics.get(project, label))


@router.patch("/topics/{label}", tags=["topics"])
def edit_topic(project: str, label: str, body: TopicEditIn, topics: Topics) -> TopicOut:
    """Renames the topic and/or sets its due date; `due_at: null` removes the date."""
    clear = "due_at" in body.model_fields_set and body.due_at is None
    return TopicOut.of(topics.edit(project, label, body.name, body.due_at, clear))


@router.post("/topics/{label}/move", tags=["topics"])
def move_topic(project: str, label: str, body: TopicMoveIn, topics: Topics) -> TopicOut:
    """Moves the topic with its subtree below `parent` (null: to the top).

    Refused when it would make a loop (400 topic_loop) or the subtree would exceed the depth limit
    (400 topic_too_deep).
    """
    return TopicOut.of(topics.move(project, label, body.parent))


@router.delete("/topics/{label}", tags=["topics"])
def delete_topic(project: str, label: str, notes: Notes, cascade: bool = False) -> TrashOut:
    """Moves the topic to the trash and returns the trash.

    A topic with sub-topics or notes needs `cascade=true`; they go with it. Otherwise 409 topic_has_content lists
    them in `details.items`.
    """
    return TrashOut.of(notes.delete_topic(project, label, cascade))


@router.post("/topics/{label}/restore", tags=["topics"])
def restore_topic(project: str, label: str, notes: Notes) -> TrashOut:
    """Takes the topic and what was deleted with it out of the trash; their notes get a new review date."""
    return TrashOut.of(notes.restore_topic(project, label))

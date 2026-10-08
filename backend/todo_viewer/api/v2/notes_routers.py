"""Topics, notes, and links of API v2. Everything is addressed by project (name) plus label."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from todo_viewer.application.services import LinkInfo, NoteService
from todo_viewer.domain.notes import (
    LinkRole,
    LinkTarget,
    NoteStatus,
    NoticeDecision,
    NoticeSide,
    Reachability,
    TargetKind,
    TriggerMode,
)

from ..dependencies import Conversion, NoteDocuments, NoteIndex, Notes, NotesSettings, Topics
from .notes_schemas import (
    DueCountOut,
    DueNoteOut,
    LinkedNoteOut,
    LinkIn,
    LinkOut,
    NoteDocumentIn,
    NoteDocumentOut,
    NoteDocumentRefOut,
    NoteEditIn,
    NoteFinishIn,
    NoteIn,
    NoteMoveIn,
    NoteOut,
    NotesIndexOut,
    NoteSnoozeIn,
    NotesSettingsIn,
    NotesSettingsOut,
    NoticeDecisionIn,
    NoticeDecisionOut,
    NoticeOut,
    PromoteIn,
    PromoteOut,
    TopicEditIn,
    TopicIn,
    TopicMoveIn,
    TopicOut,
    TrashOut,
    TriggerIn,
)
from .schemas import ErrorOut, ItemOut, NotesEntryIn, VersionIn

ERRORS: dict[int | str, dict[str, Any]] = {
    status: {"model": ErrorOut} for status in (400, 403, 404, 409)
}

router = APIRouter(prefix="/api/v2/projects/{project}", responses=ERRORS)
global_router = APIRouter(prefix="/api/v2/notes", responses=ERRORS)
notices_router = APIRouter(prefix="/api/v2/notices", responses=ERRORS)


@notices_router.get("", tags=["notices"])
def list_notices(notes: Notes, project: str, label: str, side: NoticeSide = NoticeSide.NOTE,
                 open_only: bool = Query(False, alias="open")) -> list[NoticeOut]:
    """The notices of one note (`side=note`, `label` is the note label) or one item (`side=item`, `label` is the
    item ID) in `project`, oldest first. With `open=true` only those nobody has decided yet."""
    return [NoticeOut.of(n) for n in notes.notices(project, label, side, open_only)]


@notices_router.post("/{notice_id}/decision", tags=["notices"])
def decide_notice(notice_id: int, body: NoticeDecisionIn, notes: Notes, conversion: Conversion) -> NoticeDecisionOut:
    """Decides an open notice. For a note: keep (the link stays, the review date moves), detach (the link to the
    item goes), drop (the note is dropped), promote (send `promotion` with the item's fields: the note is promoted
    as `POST /api/v2/notes/{project}/{label}/promote` does, then the notice is decided; without `promotion` it is
    refused). For an item: acknowledge. Answers with the notice and, for a note, the note as it is now, and for
    promote the new item. Errors: notice_already_decided (409), decision_not_available (409), version_conflict
    (409), notice_not_found (404), and those of promote."""
    if body.decision is NoticeDecision.PROMOTE and body.promotion is not None:
        promoted, result = conversion.promote_noticed(notice_id, body.version, body.promotion.item_type,
                                                      body.promotion.given())
        return NoticeDecisionOut.of(result, ItemOut.of(promoted.source, promoted.item.item,
                                                       promoted.item.archive_supported))
    return NoticeDecisionOut.of(notes.decide(notice_id, body.decision, body.version))


@global_router.post("/{project}/{label}/promote", tags=["notes"])
def promote_note(project: str, label: str, body: PromoteIn, conversion: Conversion) -> PromoteOut:
    """Turns the note in `version` into a Task, Story, or Epic of the same project. The item is created like any
    other (every backlog check applies, e.g. parent_closed); title and summary default to the note's summary. The
    note's long text becomes the first entry of the item's notes, its notes and specs move to the item, the note is
    promoted and archived, and it keeps a link with role `origin` to the item.

    A call that stopped halfway can be repeated with the same version: the `origin` link shows that the item exists,
    so only the missing steps run and no second item is created. promote_origin_missing (409) if that item is gone."""
    done = conversion.promote(project, label, body.version, body.item_type, body.given())
    return PromoteOut(note=NoteOut.of(done.note),
                      item=ItemOut.of(done.source, done.item.item, done.item.archive_supported))


@global_router.get("/index", tags=["notes-index"])
def notes_index(index: NoteIndex, project: str | None = None, topic: str | None = None,
                status: NoteStatus | None = None, due: bool = False, linked_item: str | None = None,
                linked_project: str | None = None, archived: bool = False) -> NotesIndexOut:
    """Topics and notes with only label, status, due reason, review date, and summary: no long texts.

    Without filters: the open notes of all projects. `project` keeps one project; `topic` (needs `project`) keeps
    the notes in that topic and its sub-topics and the topics of that subtree; `status` is the effective status
    (waiting, due, snoozed, done, dropped, promoted); `due=true` keeps the due notes; `linked_item` (in
    `linked_project`, default `project`) keeps the notes that point at the item by a link or an event trigger.
    `archived=true` reads the archive instead; a closed `status` does so by itself.
    """
    return NotesIndexOut.of(index.index(project, topic, status, due, linked_item, linked_project, archived))


@global_router.get("/due/count", tags=["notes-index"])
def due_count(index: NoteIndex) -> DueCountOut:
    """How many notes are due in all projects: a cheap call for the red exclamation mark."""
    by_project = index.due_count()
    return DueCountOut(count=sum(by_project.values()), by_project=by_project)


@global_router.get("/due", tags=["notes-index"])
def due_notes(index: NoteIndex) -> list[DueNoteOut]:
    """The due notes of all projects with the reason, the topic path, the triggers that arrived, and the actions
    that are possible, ordered by project and label."""
    return [DueNoteOut.of_due(d) for d in index.due()]


@global_router.get("/settings", tags=["notes-settings"])
def get_settings(settings: NotesSettings) -> NotesSettingsOut:
    """The global notes options."""
    return NotesSettingsOut.of(settings.current())


@global_router.put("/settings", tags=["notes-settings"])
def put_settings(body: NotesSettingsIn, settings: NotesSettings) -> NotesSettingsOut:
    """Changes the options sent and saves them in config.json; they apply from the next request on, no restart.

    Topics that are nested deeper than a lowered `max_topic_depth` stay; only new topics and moves are checked.
    """
    return NotesSettingsOut.of(settings.update(body.max_topic_depth, body.review_days))


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
    """Closes the note as `done` or `dropped`; it moves to the archive and cannot be changed until restored.

    Dropping a note puts a notice on every item it references (`GET /api/v2/notices?side=item`); `done` tells
    nobody."""
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


@router.get("/notes/{label}/links", tags=["links"])
def list_links(project: str, label: str, notes: Notes) -> list[LinkOut]:
    """The links that start at the note, among them the links of its event triggers (role `trigger`). Each item link
    says whether its project can be reached; an unreachable one adds a notice to the note the first time."""
    return [LinkOut.of(info) for info in notes.link_infos(project, label)]


@router.post("/notes/{label}/links", tags=["links"], status_code=201)
def add_link(project: str, label: str, body: LinkIn, notes: Notes) -> LinkOut:
    """Links an open note to an item, a topic, or another note. The target must exist (404 link_target_not_found);
    an item may be in another project (`target_project`), which must be registered (404 link_project_unknown).
    The same link twice is 409 link_exists."""
    target = LinkTarget(TargetKind(body.kind), body.target_project or project, body.target)
    return LinkOut.of(LinkInfo(notes.add_link(project, label, target, LinkRole(body.role)), Reachability(True)))


@router.delete("/notes/{label}/links/{link_id}", tags=["links"])
def remove_link(project: str, label: str, link_id: int, notes: Notes) -> list[LinkOut]:
    """Removes a link and returns the ones left. The link of an event trigger goes with its trigger."""
    notes.remove_link(project, label, link_id)
    return [LinkOut.of(info) for info in notes.link_infos(project, label)]


@router.get("/notes/{label}/backlinks", tags=["links"])
def notes_linking_to_note(project: str, label: str, notes: Notes) -> list[LinkedNoteOut]:
    """The notes (of all projects) that point at this note."""
    notes.show(project, label)
    return _linked(notes, TargetKind.NOTE, project, label)


@router.get("/topics/{label}/notes", tags=["links"])
def notes_linking_to_topic(project: str, label: str, notes: Notes, topics: Topics) -> list[LinkedNoteOut]:
    """The notes (of all projects) that point at this topic; notes in the trash are left out."""
    topics.get(project, label)
    return _linked(notes, TargetKind.TOPIC, project, label)


@router.get("/items/{label}/notes", tags=["links"])
def notes_linking_to_item(project: str, label: str, notes: Notes) -> list[LinkedNoteOut]:
    """The notes (of all projects) that point at this item of the project, by link or by event trigger."""
    return _linked(notes, TargetKind.ITEM, project, label)


def _linked(notes: NoteService, kind: TargetKind, project: str, label: str) -> list[LinkedNoteOut]:
    return [LinkedNoteOut.of(n) for n in notes.notes_linking_to(LinkTarget(kind, project, label))]


@router.get("/notes/{label}/documents", tags=["note-documents"])
def list_documents(project: str, label: str, documents: NoteDocuments) -> list[NoteDocumentRefOut]:
    """The names of the notes and specs of the note; read one via `/documents/{name}`."""
    return [NoteDocumentRefOut(name=name, kind=kind.value)
            for name, kind in documents.names(project, label)]


@router.get("/notes/{label}/documents/{name}", tags=["note-documents"])
def read_document(project: str, label: str, name: str, documents: NoteDocuments) -> NoteDocumentOut:
    """A notes or spec document of the note, with its version. Names of other notes: 403 forbidden."""
    return NoteDocumentOut.of(documents.read(project, label, name))


@router.put("/notes/{label}/documents/{name}", tags=["note-documents"])
def write_document(project: str, label: str, name: str, body: NoteDocumentIn,
                   documents: NoteDocuments) -> NoteDocumentOut:
    """Replaces a document in `version` with the whole new text, or creates it with version null. 409
    version_conflict if it changed in the meantime. New dated notes entries: POST …/notes."""
    return NoteDocumentOut.of(documents.write(project, label, name, body.content, body.version))


@router.post("/notes/{label}/notes", tags=["note-documents"])
def append_notes(project: str, label: str, body: NotesEntryIn, documents: NoteDocuments) -> NoteDocumentOut:
    """Appends a dated Discussed/Decided/Open entry to `<LABEL>_notes.md` (created on first use)."""
    return NoteDocumentOut.of(documents.append_notes(project, label, body.topic, body.discussed, body.decided,
                                                    body.open))


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

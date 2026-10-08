from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import UTC, datetime

from todo_viewer.domain.errors import InvalidValueError, SourceGoneError, ValueRequiredError, VersionConflictError
from todo_viewer.domain.note_lifecycle import (
    check_delete_note,
    check_editable,
    check_movable,
    check_purge_note,
    finish_changes,
    keep_changes,
    plan_topic_delete,
    plan_topic_purge,
    plan_topic_restore,
    restore_note_changes,
    snooze_changes,
)
from todo_viewer.domain.notes import (
    EVENT_STATUSES,
    FINISHED_STATUSES,
    LinkRole,
    LinkTarget,
    NewNote,
    NewTrigger,
    Note,
    NoteChanges,
    NoteEvaluation,
    NotesSettings,
    NoteStatus,
    TargetKind,
    Topic,
    Trigger,
    TriggerKind,
    TriggerMode,
    default_review_at,
    evaluate,
    event_hit,
    trigger_arrived,
)
from todo_viewer.domain.source import Source

from ..ports import BacklogRepository, Clock, NoteRepository, SourceRepository


def _now() -> datetime:
    return datetime.now(UTC)


def _summary(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        raise ValueRequiredError("summary")
    return stripped


@dataclass(frozen=True)
class NoteView:
    """A note as stored, with its triggers and what they say about it right now."""

    note: Note
    triggers: tuple[Trigger, ...]
    evaluation: NoteEvaluation


@dataclass(frozen=True)
class TrashContents:
    topics: list[Topic]
    notes: list[NoteView]


class NoteService:
    """Reads notes with their derived state (due, reason) and moves them through their lifecycle.

    Time triggers are evaluated whenever notes are read; event triggers arrive in `item_status_changed`, which the
    use case that changes an item's status calls. There is no background timer.
    """

    def __init__(self, notes: NoteRepository, sources: SourceRepository, backlogs: BacklogRepository,
                 settings: NotesSettings | None = None, clock: Clock = _now):
        self._notes = notes
        self._sources = sources
        self._backlogs = backlogs
        self._settings = settings or NotesSettings()
        self._clock = clock

    # --- reading ---

    def show(self, project: str, label: str) -> NoteView:
        return self._view(self._notes.get_note(project, label))

    def overview(self, project: str, archived: bool = False) -> list[NoteView]:
        """The notes in use, or (with `archived`) the archive. Notes in the trash are in `trash`."""
        return [self._view(n) for n in self._notes.list_notes(project, archived=archived)]

    def due(self, project: str) -> list[NoteView]:
        return [v for v in self.overview(project) if v.evaluation.status is NoteStatus.DUE]

    def trash(self, project: str) -> TrashContents:
        return TrashContents(
            [t for t in self._notes.list_topics(project, include_deleted=True) if t.deleted is not None],
            [self._view(n) for n in self._notes.list_notes(project, include_deleted=True) if n.deleted is not None])

    # --- creating and editing ---

    def create(self, project: str, summary: str, body: str | None = None, topic: str | None = None,
               review_at: datetime | None = None, trigger_mode: TriggerMode = TriggerMode.ANY) -> NoteView:
        self._source(project)
        review = review_at or self._new_review_date()
        return self._view(self._notes.create_note(project, NewNote(_summary(summary), body, topic, review,
                                                                   trigger_mode)))

    def edit(self, project: str, label: str, version: str, summary: str | None = None,
             body: str | None = None, clear_body: bool = False, topic: str | None = None,
             clear_topic: bool = False, review_at: datetime | None = None, clear_review_at: bool = False,
             trigger_mode: TriggerMode | None = None) -> NoteView:
        """Changes the given fields of an open note. A changed text sets a new review date unless one is given."""
        current = self._notes.get_note(project, label)
        check_editable(current)
        summary = None if summary is None else _summary(summary)
        changed = ((summary is not None and summary != current.summary)
                   or (body is not None and body != current.body) or (clear_body and current.body is not None))
        if review_at is None and not clear_review_at and changed:
            review_at = self._new_review_date()
        changes = NoteChanges(summary=summary, body=body, clear_body=clear_body, topic=topic,
                              clear_topic=clear_topic, review_at=review_at, clear_review_at=clear_review_at,
                              trigger_mode=trigger_mode)
        return self._view(self._notes.update_note(project, label, version, changes))

    def move_to_project(self, project: str, label: str, version: str, target_project: str,
                        target_topic: str | None = None) -> NoteView:
        """Creates the note in `target_project` with a new label and puts the old one in the trash.

        The topic belongs to the old project and is not taken along; `target_topic` is one of the new project.
        Triggers, links, and documents come along. Returns the new note.
        """
        note = self._notes.get_note(project, label)
        check_movable(note, target_project)
        if note.version != version:
            raise VersionConflictError(label)
        self._source(target_project)
        return self._view(self._notes.move_note(project, label, target_project, target_topic, self._clock()))

    def keep(self, project: str, label: str, version: str) -> NoteView:
        """The owner looked at the note and keeps it as it is: only the review date moves."""
        note = self._notes.get_note(project, label)
        return self._view(self._notes.update_note(project, label, version,
                                                  keep_changes(note, self._clock(), self._settings.review_days)))

    # --- triggers ---

    def add_trigger(self, project: str, label: str, new: NewTrigger) -> Trigger:
        """An event whose target already has the status fires at once and is marked `already_met`."""
        note = self._notes.get_note(project, label)
        if new.kind is TriggerKind.TIME and new.at is None:
            raise ValueRequiredError("at")
        if new.kind is TriggerKind.TOPIC_DUE and note.topic is None:
            raise ValueRequiredError("topic")
        if new.kind is TriggerKind.EVENT:
            new = self._checked_event(new)
        return self._notes.add_trigger(project, label, new)

    def snooze(self, project: str, label: str, version: str, review_at: datetime | None = None,
               trigger: NewTrigger | None = None) -> NoteView:
        """Back to waiting: fired triggers are reset, a new trigger replaces all old ones.

        A time or topic trigger that has passed cannot arrive a second time; without a new trigger it is removed,
        or the note would be due again at once.
        """
        note = self._notes.get_note(project, label)
        now = self._clock()
        self._notes.update_note(project, label, version, snooze_changes(note, now, self._settings.review_days,
                                                                        review_at))
        topic_due = self._topic_due(note)
        if trigger is not None:
            for old in self._notes.triggers_of(project, label):
                self._notes.remove_trigger(project, label, old.id)
            self.add_trigger(project, label, trigger)
        else:
            for old in self._notes.reset_triggers(project, label):
                if old.kind is not TriggerKind.EVENT and trigger_arrived(old, now, topic_due):
                    self._notes.remove_trigger(project, label, old.id)
        return self.show(project, label)

    def item_status_changed(self, project: str, item_id: str, status: str) -> None:
        """Marks the event triggers on this item that wait for `status` as fired, in all projects."""
        now = self._clock()
        for link in self._notes.links_to(LinkTarget(TargetKind.ITEM, project, item_id)):
            if link.role is not LinkRole.TRIGGER:
                continue
            note = self._notes.get_note(link.project, link.note)
            if note.deleted is not None or note.status in FINISHED_STATUSES:
                continue
            for trigger in self._notes.triggers_of(link.project, link.note):
                if trigger.link_id == link.id and event_hit(trigger, status):
                    self._notes.mark_fired(link.project, link.note, trigger.id, now)

    # --- lifecycle, archive, trash ---

    def finish(self, project: str, label: str, version: str, target: NoteStatus) -> NoteView:
        """Done, dropped, or promoted: the note moves to the archive."""
        note = self._notes.get_note(project, label)
        return self._view(self._notes.update_note(project, label, version, finish_changes(note, target)))

    def delete_note(self, project: str, label: str) -> NoteView:
        check_delete_note(self._notes.get_note(project, label))
        return self._view(self._notes.delete_note(project, label, self._clock()))

    def restore_note(self, project: str, label: str) -> NoteView:
        """From the archive or the trash back to waiting, with a new review date."""
        note = self._notes.get_note(project, label)
        changes = restore_note_changes(note, self._notes.list_topics(project, include_deleted=True), self._clock(),
                                       self._settings.review_days)
        if note.deleted is not None:
            note = self._notes.restore_note(project, label)
        return self._view(self._notes.update_note(project, label, note.version, changes))

    def purge_note(self, project: str, label: str) -> None:
        """Removes a note in the trash for good. Reserved for the owner: no HTTP route calls it for Claude."""
        check_purge_note(self._notes.get_note(project, label))
        self._notes.purge_note(project, label)

    def delete_topic(self, project: str, label: str, cascade: bool) -> TrashContents:
        plan = plan_topic_delete(self._notes.list_topics(project, include_deleted=True),
                                 self._notes.list_notes(project, include_deleted=True), label, cascade)
        self._notes.trash_topics(project, plan.topics, plan.notes, self._clock())
        return self.trash(project)

    def restore_topic(self, project: str, label: str) -> TrashContents:
        """The topic and what was deleted with it come back; their notes get a new review date."""
        plan = plan_topic_restore(self._notes.list_topics(project, include_deleted=True),
                                  self._notes.list_notes(project, include_deleted=True), label)
        self._notes.restore_topics(project, plan.topics, plan.notes)
        for note_label in plan.notes:
            note = self._notes.get_note(project, note_label)
            self._notes.update_note(project, note_label, note.version,
                                    NoteChanges(review_at=self._new_review_date()))
        return self.trash(project)

    def purge_topic(self, project: str, label: str) -> None:
        """Removes a topic in the trash and its notes in the trash for good (owner only, like `purge_note`)."""
        plan = plan_topic_purge(self._notes.list_topics(project, include_deleted=True),
                                self._notes.list_notes(project, include_deleted=True), label)
        self._notes.purge_topics(project, plan.topics, plan.notes)

    # --- helpers ---

    def _new_review_date(self) -> datetime:
        return default_review_at(self._clock(), self._settings.review_days)

    def _topic_due(self, note: Note) -> datetime | None:
        return None if note.topic is None else self._notes.get_topic(note.project, note.topic).due_at

    def _view(self, note: Note) -> NoteView:
        triggers = self._notes.triggers_of(note.project, note.label)
        return NoteView(note, tuple(triggers), evaluate(note, triggers, self._topic_due(note), self._clock()))

    def _source(self, project: str) -> Source:
        found = next((s for s in self._sources.all() if s.project == project), None)
        if found is None:
            raise SourceGoneError()
        return found

    def _checked_event(self, new: NewTrigger) -> NewTrigger:
        if new.target is None:
            raise ValueRequiredError("target")
        if new.target_status not in EVENT_STATUSES:
            raise InvalidValueError("target_status", tuple(EVENT_STATUSES))
        if new.target.kind is not TargetKind.ITEM:
            raise InvalidValueError("target", (TargetKind.ITEM.value,))
        item = self._backlogs.get(self._source(new.target.project), new.target.label)
        if item.status == new.target_status:
            return dataclasses.replace(new, fired_at=self._clock(), already_met=True)
        return new

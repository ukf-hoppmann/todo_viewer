from __future__ import annotations

import dataclasses
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

import structlog

from todo_viewer.domain.errors import (
    DecisionNotAvailableError,
    InvalidValueError,
    ItemNotFoundError,
    LinkExistsError,
    LinkNotFoundError,
    LinkTargetNotFoundError,
    NoteLifecycleError,
    NoteNotFoundError,
    SourceGoneError,
    TopicNotFoundError,
    TriggerNotFoundError,
    ValueRequiredError,
    VersionConflictError,
)
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
    Link,
    LinkRole,
    LinkTarget,
    NewNote,
    NewNotice,
    NewTrigger,
    Note,
    NoteChanges,
    NoteEvaluation,
    NotesSettings,
    NoteStatus,
    Notice,
    NoticeCause,
    NoticeDecision,
    NoticeSide,
    TargetKind,
    Topic,
    Trigger,
    TriggerKind,
    TriggerMode,
    check_decision,
    default_review_at,
    evaluate,
    event_hit,
    item_status_notice_cause,
    trigger_arrived,
)
from todo_viewer.domain.source import Source

from ..ports import BacklogRepository, Clock, NoteRepository, SourceRepository

log = structlog.get_logger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


def _summary(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        raise ValueRequiredError("summary")
    return stripped


# Closing a note this way tells the items it references; `done` tells nobody.
_NOTE_CLOSED_CAUSES = {NoteStatus.DROPPED: NoticeCause.NOTE_DROPPED, NoteStatus.PROMOTED: NoticeCause.NOTE_PROMOTED}


@dataclass(frozen=True)
class NoteView:
    """A note as stored, with its triggers and what they say about it right now."""

    note: Note
    triggers: tuple[Trigger, ...]
    evaluation: NoteEvaluation
    open_notices: tuple[Notice, ...] = ()


@dataclass(frozen=True)
class DecisionResult:
    """The notice after the decision and, for a notice to a note, the note as it is now."""

    notice: Notice
    note: NoteView | None


@dataclass(frozen=True)
class LinkedNote:
    """A note that points at something, with the link it does it by."""

    link: Link
    view: NoteView


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
                 settings: Callable[[], NotesSettings] | None = None, clock: Clock = _now):
        self._notes = notes
        self._sources = sources
        self._backlogs = backlogs
        self._settings = settings or NotesSettings
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
                                                  keep_changes(note, self._clock(), self._settings().review_days)))

    # --- links ---

    def links_of(self, project: str, label: str) -> list[Link]:
        self._notes.get_note(project, label)
        return self._notes.links_of(project, label)

    def add_link(self, project: str, label: str, target: LinkTarget, role: LinkRole = LinkRole.REFERENCE) -> Link:
        """Links an open note to an item, a topic, or another note. The target must exist; a link exists once."""
        note = self._notes.get_note(project, label)
        check_editable(note)
        if role is LinkRole.TRIGGER:
            raise InvalidValueError("role", (LinkRole.REFERENCE.value, LinkRole.ORIGIN.value))
        if target.kind is TargetKind.NOTE and (target.project, target.label) == (project, label):
            raise InvalidValueError("target", ("another note",))
        self._check_target(target)
        if any(link.target == target and link.role is role for link in self._notes.links_of(project, label)):
            raise LinkExistsError(label)
        return self._notes.add_link(project, label, target, role)

    def remove_link(self, project: str, label: str, link_id: int) -> list[Link]:
        """Removes a link of an open note and returns the links that are left. The link of an event trigger goes
        with its trigger."""
        note = self._notes.get_note(project, label)
        check_editable(note)
        found = next((link for link in self._notes.links_of(project, label) if link.id == link_id), None)
        if found is None:
            raise LinkNotFoundError(link_id)
        if found.role is LinkRole.TRIGGER:
            raise NoteLifecycleError("link_belongs_to_trigger", label)
        self._notes.remove_link(project, label, link_id)
        return self._notes.links_of(project, label)

    def notes_linking_to(self, target: LinkTarget) -> list[LinkedNote]:
        """The notes (in all projects, not those in the trash) that point at the target."""
        if target.kind is TargetKind.ITEM:
            self._source(target.project)
        found = []
        for link in self._notes.links_to(target):
            note = self._notes.get_note(link.project, link.note)
            if note.deleted is None:
                found.append(LinkedNote(link, self._view(note)))
        return found

    # --- triggers ---

    def add_trigger(self, project: str, label: str, new: NewTrigger) -> Trigger:
        """An event whose target already has the status fires at once and is marked `already_met`."""
        note = self._notes.get_note(project, label)
        check_editable(note)
        return self._notes.add_trigger(project, label, self._checked_trigger(note, new))

    def remove_trigger(self, project: str, label: str, trigger_id: int) -> NoteView:
        """Removes a trigger of an open note, with the link that belongs to it."""
        note = self._notes.get_note(project, label)
        check_editable(note)
        if all(t.id != trigger_id for t in self._notes.triggers_of(project, label)):
            raise TriggerNotFoundError(trigger_id)
        self._notes.remove_trigger(project, label, trigger_id)
        return self._view(note)

    def snooze(self, project: str, label: str, version: str, review_at: datetime | None = None,
               trigger: NewTrigger | None = None) -> NoteView:
        """Back to waiting: fired triggers are reset, a new trigger replaces all old ones.

        A time or topic trigger that has passed cannot arrive a second time; without a new trigger it is removed,
        or the note would be due again at once. A new trigger is checked before anything changes.
        """
        note = self._notes.get_note(project, label)
        now = self._clock()
        changes = snooze_changes(note, now, self._settings().review_days, review_at)
        checked = None if trigger is None else self._checked_trigger(note, trigger)
        self._notes.update_note(project, label, version, changes)
        topic_due = self._topic_due(note)
        if checked is not None:
            for old in self._notes.triggers_of(project, label):
                self._notes.remove_trigger(project, label, old.id)
            self._notes.add_trigger(project, label, checked)
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
        cause = item_status_notice_cause(status)
        if cause is not None:
            self._tell_notes(LinkTarget(TargetKind.ITEM, project, item_id), cause)

    def item_deleted(self, project: str, item_id: str) -> None:
        """Tells the notes that reference the item that it is in the trash now."""
        self._tell_notes(LinkTarget(TargetKind.ITEM, project, item_id), NoticeCause.ITEM_DELETED)

    def item_retyped(self, project: str, old_id: str, new_id: str) -> None:
        """Tells the notes that reference the item that it has a new id. Their links point at `new_id` already."""
        self._tell_notes(LinkTarget(TargetKind.ITEM, project, new_id), NoticeCause.ITEM_RETYPED)

    # --- notices ---

    def add_notice(self, new: NewNotice) -> Notice:
        """Tells a note or an item that the other end changed. An open notice of the same kind stays the only one."""
        return self._notes.add_notice(new)

    def notice(self, notice_id: int) -> Notice:
        return self._notes.get_notice(notice_id)

    def notices(self, project: str, label: str, side: NoticeSide, open_only: bool = True) -> list[Notice]:
        """The notices of a note (side `note`) or of an item (side `item`), oldest first."""
        if side is NoticeSide.NOTE:
            self._notes.get_note(project, label)
        return self._notes.notices_of(project, label, side, open_only)

    def decide(self, notice_id: int, decision: NoticeDecision, version: str | None = None) -> DecisionResult:
        """Decides an open notice. The effect is applied first; a failure leaves the notice open.

        Notice to a note: `keep` moves the review date, `detach` removes the reference link to the item, `drop`
        drops the note, `promote` only records a promotion that `ConversionService` ran (it is refused for a note that
        is not promoted). Notice to an item: `acknowledge`. `version` is the note's
        version the decision is based on (default: the stored one).
        """
        notice = self._notes.get_notice(notice_id)
        check_decision(notice, decision)
        if notice.side is NoticeSide.ITEM:
            return DecisionResult(self._notes.decide_notice(notice_id, decision, self._clock()), None)
        note = self._notes.get_note(notice.project, notice.label)
        if decision is NoticeDecision.PROMOTE and note.status is not NoteStatus.PROMOTED:
            raise DecisionNotAvailableError(decision.value)  # the promotion workflow decides it, after the note ran it
        expected = version or note.version
        if note.version != expected:
            raise VersionConflictError(note.label)
        if decision is NoticeDecision.KEEP:
            self._notes.update_note(note.project, note.label, expected,
                                    keep_changes(note, self._clock(), self._settings().review_days))
        elif decision is NoticeDecision.DETACH:
            check_editable(note)
            for link in self._notes.links_of(note.project, note.label):
                if link.target == notice.counterpart and link.role is LinkRole.REFERENCE:
                    self._notes.remove_link(note.project, note.label, link.id)
        elif decision is NoticeDecision.DROP:
            self.finish(note.project, note.label, expected, NoteStatus.DROPPED)
        decided = self._notes.decide_notice(notice_id, decision, self._clock())
        return DecisionResult(decided, self.show(note.project, note.label))

    # --- lifecycle, archive, trash ---

    def finish(self, project: str, label: str, version: str, target: NoteStatus) -> NoteView:
        """Done, dropped, or promoted: the note moves to the archive."""
        note = self._notes.get_note(project, label)
        view = self._view(self._notes.update_note(project, label, version, finish_changes(note, target)))
        cause = _NOTE_CLOSED_CAUSES.get(target)
        if cause is not None:
            self._tell_items(note, cause)
        return view

    def delete_note(self, project: str, label: str) -> NoteView:
        check_delete_note(self._notes.get_note(project, label))
        return self._view(self._notes.delete_note(project, label, self._clock()))

    def restore_note(self, project: str, label: str) -> NoteView:
        """From the archive or the trash back to waiting, with a new review date."""
        note = self._notes.get_note(project, label)
        changes = restore_note_changes(note, self._notes.list_topics(project, include_deleted=True), self._clock(),
                                       self._settings().review_days)
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

    def _tell_items(self, note: Note, cause: NoticeCause) -> None:
        """A notice for every item the note references. The note is closed already: a failure here is logged and
        never reaches the caller, and it does not stop the other items."""
        try:
            links = [link for link in self._notes.links_of(note.project, note.label)
                     if link.role is LinkRole.REFERENCE and link.target.kind is TargetKind.ITEM]
        except Exception:
            log.exception("notice_links_failed", project=note.project, note=note.label, cause=cause.value)
            return
        about = LinkTarget(TargetKind.NOTE, note.project, note.label)
        for link in links:
            try:
                self._notes.add_notice(NewNotice(NoticeSide.ITEM, link.target.project, link.target.label, cause,
                                                 about))
            except Exception:
                log.exception("notice_failed", project=link.target.project, item=link.target.label,
                              note=note.label, cause=cause.value)

    def _tell_notes(self, item: LinkTarget, cause: NoticeCause) -> None:
        """A notice for every open note in use that references the item. The item change is written already:
        a failure here is logged and never reaches the caller, and it does not stop the other notes."""
        try:
            links = [link for link in self._notes.links_to(item) if link.role is LinkRole.REFERENCE]
        except Exception:
            log.exception("notice_links_failed", project=item.project, item=item.label, cause=cause.value)
            return
        for link in links:
            try:
                note = self._notes.get_note(link.project, link.note)
                if note.deleted is None and note.status not in FINISHED_STATUSES:
                    self._notes.add_notice(NewNotice(NoticeSide.NOTE, link.project, link.note, cause, item))
            except Exception:
                log.exception("notice_failed", project=link.project, note=link.note, item=item.label,
                              cause=cause.value)

    def _new_review_date(self) -> datetime:
        return default_review_at(self._clock(), self._settings().review_days)

    def _topic_due(self, note: Note) -> datetime | None:
        return None if note.topic is None else self._notes.get_topic(note.project, note.topic).due_at

    def _view(self, note: Note) -> NoteView:
        triggers = self._notes.triggers_of(note.project, note.label)
        open_notices = self._notes.notices_of(note.project, note.label, NoticeSide.NOTE, open_only=True)
        evaluation = evaluate(note, triggers, self._topic_due(note), self._clock(), len(open_notices))
        return NoteView(note, tuple(triggers), evaluation, tuple(open_notices))

    def _source(self, project: str) -> Source:
        found = next((s for s in self._sources.all() if s.project == project), None)
        if found is None:
            raise SourceGoneError()
        return found

    def _check_target(self, target: LinkTarget) -> None:
        try:
            if target.kind is TargetKind.ITEM:
                self._backlogs.get(self._source(target.project), target.label)
            elif target.kind is TargetKind.TOPIC:
                self._source(target.project)
                if self._notes.get_topic(target.project, target.label).deleted is not None:
                    raise TopicNotFoundError(target.label)
            else:
                self._source(target.project)
                if self._notes.get_note(target.project, target.label).deleted is not None:
                    raise NoteNotFoundError(target.label)
        except (ItemNotFoundError, TopicNotFoundError, NoteNotFoundError, SourceGoneError) as gone:
            raise LinkTargetNotFoundError(target.kind.value, target.project, target.label) from gone

    def _checked_trigger(self, note: Note, new: NewTrigger) -> NewTrigger:
        if new.kind is TriggerKind.TIME and new.at is None:
            raise ValueRequiredError("at")
        if new.kind is TriggerKind.TOPIC_DUE and note.topic is None:
            raise ValueRequiredError("topic")
        return self._checked_event(new) if new.kind is TriggerKind.EVENT else new

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

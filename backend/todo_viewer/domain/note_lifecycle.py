"""Lifecycle of notes: finishing (archive), snoozing, the trash, and the cascade over topics.

Pure rules that return the change to make; the service applies them. `due` is derived (see `evaluate`) and never
stored, so the stored statuses are waiting, snoozed, and the three closing ones.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from .errors import NoteLifecycleError, TopicNotFoundError
from .notes import FINISHED_STATUSES, Note, NoteChanges, NoteStatus, Topic, default_review_at


def _active(note: Note) -> None:
    if note.deleted is not None:
        raise NoteLifecycleError("note_deleted", note.label)
    if note.status in FINISHED_STATUSES:
        raise NoteLifecycleError("note_closed", note.label)


def finish_changes(note: Note, target: NoteStatus) -> NoteChanges:
    """Closing as done, dropped, or promoted puts the note in the archive."""
    if target not in FINISHED_STATUSES:
        raise NoteLifecycleError("note_target_invalid", note.label)
    _active(note)
    return NoteChanges(status=target, archived=True)


def snooze_changes(note: Note, now: datetime, review_days: int, review_at: datetime | None = None) -> NoteChanges:
    """Back to waiting with a new review date; the caller also resets the fired triggers."""
    _active(note)
    return NoteChanges(status=NoteStatus.SNOOZED, review_at=review_at or default_review_at(now, review_days))


def keep_changes(note: Note, now: datetime, review_days: int) -> NoteChanges:
    """"Keep": the note stays as it is, only its review date moves."""
    _active(note)
    return NoteChanges(review_at=default_review_at(now, review_days))


def restore_note_changes(note: Note, topics: Sequence[Topic], now: datetime, review_days: int) -> NoteChanges:
    """Archive or trash back to waiting, with a new review date. Not into a topic that is in the trash."""
    if not note.archived and note.deleted is None:
        raise NoteLifecycleError("note_not_restorable", note.label)
    gone = next((t.label for t in topics if t.label == note.topic and t.deleted is not None), None)
    if gone is not None:
        raise NoteLifecycleError("topic_deleted", note.label, (gone,))
    return NoteChanges(status=NoteStatus.WAITING, archived=False, review_at=default_review_at(now, review_days))


def check_delete_note(note: Note) -> None:
    if note.deleted is not None:
        raise NoteLifecycleError("note_deleted", note.label)


def check_purge_note(note: Note) -> None:
    if note.deleted is None:
        raise NoteLifecycleError("note_not_deleted", note.label)


# --- topics ---

@dataclass(frozen=True)
class TopicPlan:
    """The topics and notes (labels) one trash operation on a topic touches, the topic itself first."""

    topics: tuple[str, ...]
    notes: tuple[str, ...]


def _subtree(topics: Sequence[Topic], label: str, same: datetime | None = None) -> list[Topic]:
    """`label` and its descendants in list order; with `same`, only those deleted at that moment."""
    by_label = {t.label: t for t in topics}
    found = {label}
    grew = True
    while grew:
        grew = False
        for t in topics:
            if t.label not in found and t.parent in found and (same is None or t.deleted == same):
                found.add(t.label)
                grew = True
    return [by_label[label], *(t for t in topics if t.label in found and t.label != label)]


def _find(topics: Sequence[Topic], label: str) -> Topic:
    found = next((t for t in topics if t.label == label), None)
    if found is None:
        raise TopicNotFoundError(label)
    return found


def plan_topic_delete(topics: Sequence[Topic], notes: Sequence[Note], label: str, cascade: bool) -> TopicPlan:
    """A topic with sub-topics or notes only goes to the trash with the cascade, together with them."""
    if _find(topics, label).deleted is not None:
        raise NoteLifecycleError("topic_deleted", label)
    live = [t for t in topics if t.deleted is None]
    tree = _subtree(live, label)
    labels = {t.label for t in tree}
    inside = [n for n in notes if n.topic in labels and n.deleted is None]
    content = tuple([t.label for t in tree[1:]] + [n.label for n in inside])
    if content and not cascade:
        raise NoteLifecycleError("topic_has_content", label, content)
    return TopicPlan(tuple(t.label for t in tree), tuple(n.label for n in inside))


def plan_topic_restore(topics: Sequence[Topic], notes: Sequence[Note], label: str) -> TopicPlan:
    """Brings back the topic and what was deleted with it, but only below a topic that exists."""
    topic = _find(topics, label)
    if topic.deleted is None:
        raise NoteLifecycleError("topic_not_deleted", label)
    parent = next((t for t in topics if t.label == topic.parent), None)
    if parent is not None and parent.deleted is not None:
        raise NoteLifecycleError("topic_deleted", label, (parent.label,))
    tree = _subtree(topics, label, topic.deleted)
    labels = {t.label for t in tree}
    return TopicPlan(tuple(t.label for t in tree),
                     tuple(n.label for n in notes if n.topic in labels and n.deleted == topic.deleted))


def plan_topic_purge(topics: Sequence[Topic], notes: Sequence[Note], label: str) -> TopicPlan:
    """What goes for good: the topic in the trash, the sub-topics in the trash, and their notes in the trash."""
    if _find(topics, label).deleted is None:
        raise NoteLifecycleError("topic_not_deleted", label)
    tree = [t for t in _subtree(topics, label) if t.deleted is not None]
    labels = {t.label for t in tree}
    return TopicPlan(tuple(t.label for t in tree),
                     tuple(n.label for n in notes if n.topic in labels and n.deleted is not None))

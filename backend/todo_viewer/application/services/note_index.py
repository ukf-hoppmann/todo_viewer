from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from todo_viewer.domain.errors import SourceGoneError, ValueRequiredError
from todo_viewer.domain.notes import (
    FINISHED_STATUSES,
    LinkTarget,
    NoteStatus,
    TargetKind,
    Topic,
    Trigger,
    subtree_labels,
    topic_path,
    utc,
)

from ..ports import Clock, NoteRepository, SourceRepository
from .notes import NoteService, NoteView

# What the owner can do with a note that is due; the UI and Claude offer exactly these.
DUE_ACTIONS = ("keep", "snooze", "done", "dropped")


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class IndexedTopic:
    topic: Topic
    path: tuple[str, ...]
    due: bool
    note_count: int  # open notes directly in this topic


@dataclass(frozen=True)
class NotesIndex:
    topics: list[IndexedTopic]
    notes: list[NoteView]


@dataclass(frozen=True)
class DueNote:
    view: NoteView
    topic_path: tuple[str, ...]
    fired: tuple[Trigger, ...]
    actions: tuple[str, ...] = DUE_ACTIONS


class NoteIndexService:
    """What a reader needs to pick notes without loading their long texts: the index, the due counter, the due list.

    Time triggers are evaluated whenever this is asked (see `NoteService`); nothing runs in the background.
    """

    def __init__(self, notes: NoteService, repo: NoteRepository, sources: SourceRepository, clock: Clock = _now):
        self._notes = notes
        self._repo = repo
        self._sources = sources
        self._clock = clock

    def index(self, project: str | None = None, topic: str | None = None, status: NoteStatus | None = None,
              due: bool = False, linked_item: str | None = None, linked_project: str | None = None,
              archived: bool = False) -> NotesIndex:
        """Open notes (with `archived`: the archive; a closed `status` reads the archive too) and the topics.

        `topic` includes its sub-topics and needs `project`; `linked_item` (in `linked_project`, default `project`)
        keeps the notes that point at the item by a link or by an event trigger.
        """
        projects = self._projects(project)
        if topic is not None and project is None:
            raise ValueRequiredError("project")
        target = self._linked(linked_item, linked_project or project)
        keep_topics = None if topic is None else self._topic_labels(project or "", topic)
        reading_archive = archived or (status in FINISHED_STATUSES)
        linked = None if target is None else {(n.view.note.project, n.view.note.label)
                                              for n in self._notes.notes_linking_to(target)}
        topics: list[IndexedTopic] = []
        notes: list[NoteView] = []
        for name in projects:
            all_topics = self._repo.list_topics(name)
            views = self._notes.overview(name, archived=reading_archive)
            notes += [v for v in views if self._wanted(v, keep_topics, status, due, linked)]
            counts = self._counts(name, views if not reading_archive else self._notes.overview(name))
            topics += [IndexedTopic(t, topic_path(all_topics, t.label), self._topic_due(t), counts.get(t.label, 0))
                       for t in all_topics if keep_topics is None or t.label in keep_topics]
        return NotesIndex(topics, notes)

    def due(self) -> list[DueNote]:
        """The notes that are due in all projects, with the reason, the triggers that arrived, and the actions."""
        found = []
        for name in self._projects(None):
            topics = self._repo.list_topics(name)
            for view in self._notes.due(name):
                topic = view.note.topic
                fired = tuple(t for t in view.triggers if t.id in view.evaluation.fired)
                found.append(DueNote(view, () if topic is None else topic_path(topics, topic), fired))
        return found

    def due_count(self) -> dict[str, int]:
        """The number of due notes per project, for the red exclamation mark."""
        return {name: len(self._notes.due(name)) for name in self._projects(None)}

    # --- helpers ---

    def _projects(self, project: str | None) -> list[str]:
        names = list(dict.fromkeys(s.project for s in self._sources.all()))
        if project is None:
            return names
        if project not in names:
            raise SourceGoneError(f"Project '{project}' not found.")
        return [project]

    def _topic_labels(self, project: str, topic: str) -> frozenset[str]:
        topics = self._repo.list_topics(project)
        self._repo.get_topic(project, topic)
        return subtree_labels(topics, topic)

    def _linked(self, item: str | None, project: str | None) -> LinkTarget | None:
        if item is None:
            return None
        if project is None:
            raise ValueRequiredError("linked_project")
        return LinkTarget(TargetKind.ITEM, project, item)

    def _topic_due(self, topic: Topic) -> bool:
        return topic.due_at is not None and utc(topic.due_at) <= utc(self._clock())

    @staticmethod
    def _wanted(view: NoteView, topics: frozenset[str] | None, status: NoteStatus | None, due: bool,
                linked: set[tuple[str, str]] | None) -> bool:
        note = view.note
        return ((topics is None or note.topic in topics)
                and (status is None or view.evaluation.status is status)
                and (not due or view.evaluation.status is NoteStatus.DUE)
                and (linked is None or (note.project, note.label) in linked))

    @staticmethod
    def _counts(project: str, views: list[NoteView]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for view in views:
            note = view.note
            if note.topic is not None and not note.archived and note.project == project:
                counts[note.topic] = counts.get(note.topic, 0) + 1
        return counts


__all__ = ["DUE_ACTIONS", "DueNote", "IndexedTopic", "NoteIndexService", "NotesIndex"]

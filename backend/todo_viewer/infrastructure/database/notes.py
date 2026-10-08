"""Topics, notes, links, triggers, and the documents of notes in the central database.

Only storage: which trigger has arrived and what a status means is decided in `domain` and `application`.
"""
from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa

from todo_viewer.domain.documents import content_version
from todo_viewer.domain.errors import (
    DocumentNotFoundError,
    NoteNotFoundError,
    TopicNotFoundError,
    VersionConflictError,
)
from todo_viewer.domain.notes import (
    Link,
    LinkRole,
    LinkTarget,
    NewNote,
    NewTrigger,
    Note,
    NoteChanges,
    NoteStatus,
    TargetKind,
    Topic,
    Trigger,
    TriggerKind,
    TriggerMode,
    check_new_topic,
    check_note_document_name,
    check_topic_move,
    format_label,
    utc,
)

from .engine import Database
from .schema import note_counters, note_documents, note_links, note_triggers, notes, projects, topics


def _now() -> datetime:
    return datetime.now(UTC)


def _text(moment: datetime | None) -> str | None:
    return None if moment is None else utc(moment).isoformat()


def _moment(text: str | None) -> datetime | None:
    return None if text is None else datetime.fromisoformat(text)


class DatabaseNoteRepository:
    def __init__(self, db: Database, clock: Any = _now):
        self._db = db
        self._clock = clock

    # --- topics ---

    def create_topic(self, project: str, name: str, parent: str | None, due_at: datetime | None,
                     max_depth: int) -> Topic:
        with self._db.begin() as conn:
            _ensure_project(conn, project)
            label = _next_label(conn, project, "topic")
            if parent is not None:
                _topic_uid(conn, project, parent)
            check_new_topic(_parents(conn, project), parent, max_depth, label)
            conn.execute(sa.insert(topics).values(
                uid=str(uuid.uuid4()), project_id=project, label=label, name=name,
                parent_uid=None if parent is None else _topic_uid(conn, project, parent),
                due_at=_text(due_at), created=_text(self._clock())))
            return _topic(conn, project, label)

    def get_topic(self, project: str, label: str) -> Topic:
        with self._db.begin() as conn:
            return _topic(conn, project, label)

    def list_topics(self, project: str, include_deleted: bool = False) -> list[Topic]:
        with self._db.begin() as conn:
            query = sa.select(topics.c.label).where(topics.c.project_id == project).order_by(topics.c.created,
                                                                                          topics.c.label)
            if not include_deleted:
                query = query.where(topics.c.deleted.is_(None))
            labels: list[str] = list(conn.execute(query).scalars())
            return [_topic(conn, project, label) for label in labels]

    def update_topic(self, project: str, label: str, name: str, due_at: datetime | None) -> Topic:
        with self._db.begin() as conn:
            uid = _topic_uid(conn, project, label)
            conn.execute(sa.update(topics).where(topics.c.uid == uid).values(name=name, due_at=_text(due_at)))
            return _topic(conn, project, label)

    def move_topic(self, project: str, label: str, parent: str | None, max_depth: int) -> Topic:
        with self._db.begin() as conn:
            uid = _topic_uid(conn, project, label)
            parent_uid = None if parent is None else _topic_uid(conn, project, parent)
            check_topic_move(_parents(conn, project), label, parent, max_depth)
            conn.execute(sa.update(topics).where(topics.c.uid == uid).values(parent_uid=parent_uid))
            return _topic(conn, project, label)

    # --- notes ---

    def create_note(self, project: str, new: NewNote) -> Note:
        with self._db.begin() as conn:
            _ensure_project(conn, project)
            label = _next_label(conn, project, "note")
            topic_uid = None if new.topic is None else _topic_uid(conn, project, new.topic)
            now = _text(self._clock())
            conn.execute(sa.insert(notes).values(
                uid=str(uuid.uuid4()), project_id=project, label=label, summary=new.summary, body=new.body,
                status=NoteStatus.WAITING.value, topic_uid=topic_uid, review_at=_text(new.review_at),
                trigger_mode=new.trigger_mode.value, created=now, updated=now, archived=False))
            return _note(conn, project, label)

    def get_note(self, project: str, label: str) -> Note:
        with self._db.begin() as conn:
            return _note(conn, project, label)

    def list_notes(self, project: str, include_deleted: bool = False, archived: bool | None = None) -> list[Note]:
        with self._db.begin() as conn:
            query = sa.select(notes.c.label).where(notes.c.project_id == project).order_by(notes.c.created,
                                                                                         notes.c.label)
            if not include_deleted:
                query = query.where(notes.c.deleted.is_(None))
            if archived is not None:
                query = query.where(notes.c.archived.is_(archived))
            found: list[str] = list(conn.execute(query).scalars())
            return [_note(conn, project, label) for label in found]

    def update_note(self, project: str, label: str, expected_version: str, changes: NoteChanges) -> Note:
        with self._db.begin() as conn:
            current = _note(conn, project, label)
            if current.version != expected_version:
                raise VersionConflictError(label)
            values: dict[str, Any] = {"updated": _text(self._clock())}
            if changes.summary is not None:
                values["summary"] = changes.summary
            if changes.clear_body:
                values["body"] = None
            elif changes.body is not None:
                values["body"] = changes.body
            if changes.status is not None:
                values["status"] = changes.status.value
            if changes.clear_topic:
                values["topic_uid"] = None
            elif changes.topic is not None:
                values["topic_uid"] = _topic_uid(conn, project, changes.topic)
            if changes.clear_review_at:
                values["review_at"] = None
            elif changes.review_at is not None:
                values["review_at"] = _text(changes.review_at)
            if changes.trigger_mode is not None:
                values["trigger_mode"] = changes.trigger_mode.value
            if changes.archived is not None:
                values["archived"] = changes.archived
            conn.execute(sa.update(notes).where(notes.c.uid == _note_uid(conn, project, label)).values(**values))
            return _note(conn, project, label)

    def delete_note(self, project: str, label: str, at: datetime) -> Note:
        with self._db.begin() as conn:
            conn.execute(sa.update(notes).where(notes.c.uid == _note_uid(conn, project, label))
                         .values(deleted=_text(at)))
            return _note(conn, project, label)

    def restore_note(self, project: str, label: str) -> Note:
        with self._db.begin() as conn:
            conn.execute(sa.update(notes).where(notes.c.uid == _note_uid(conn, project, label)).values(deleted=None))
            return _note(conn, project, label)

    def move_note(self, project: str, label: str, target_project: str, target_topic: str | None,
                  at: datetime) -> Note:
        with self._db.begin() as conn:
            old_uid = _note_uid(conn, project, label)
            old = conn.execute(sa.select(notes).where(notes.c.uid == old_uid)).one()
            _ensure_project(conn, target_project)
            topic_uid = None if target_topic is None else _topic_uid(conn, target_project, target_topic)
            new_label = _next_label(conn, target_project, "note")
            new_uid = str(uuid.uuid4())
            conn.execute(sa.insert(notes).values(
                uid=new_uid, project_id=target_project, label=new_label, summary=old.summary, body=old.body,
                status=old.status, topic_uid=topic_uid, review_at=old.review_at, trigger_mode=old.trigger_mode,
                created=old.created, updated=_text(self._clock()), archived=old.archived))
            link_ids = _copy_links(conn, old_uid, new_uid)
            for row in conn.execute(sa.select(note_triggers).where(note_triggers.c.note_uid == old_uid)
                                    .order_by(note_triggers.c.id)):
                conn.execute(sa.insert(note_triggers).values(
                    note_uid=new_uid, kind=row.kind, at=row.at, link_id=link_ids.get(row.link_id),
                    target_status=row.target_status, fired_at=row.fired_at, already_met=row.already_met))
            for doc in conn.execute(sa.select(note_documents).where(note_documents.c.note_uid == old_uid)):
                conn.execute(sa.insert(note_documents).values(
                    note_uid=new_uid, name=doc.name.replace(label, new_label, 1), content=doc.content))
            # Other notes that point at the moved one follow it.
            conn.execute(sa.update(note_links).where(
                note_links.c.target_kind == TargetKind.NOTE.value, note_links.c.target_project == project,
                note_links.c.target_label == label, note_links.c.note_uid != old_uid)
                .values(target_project=target_project, target_label=new_label))
            conn.execute(sa.update(notes).where(notes.c.uid == old_uid).values(deleted=_text(at)))
            return _note(conn, target_project, new_label)

    # --- links ---

    def add_link(self, project: str, label: str, target: LinkTarget, role: LinkRole) -> Link:
        with self._db.begin() as conn:
            return _link(conn, project, label, _insert_link(conn, _note_uid(conn, project, label), target, role))

    def remove_link(self, project: str, label: str, link_id: int) -> None:
        with self._db.begin() as conn:
            uid = _note_uid(conn, project, label)
            conn.execute(sa.delete(note_links).where(note_links.c.id == link_id, note_links.c.note_uid == uid))

    def links_of(self, project: str, label: str) -> list[Link]:
        with self._db.begin() as conn:
            uid = _note_uid(conn, project, label)
            ids: list[int] = list(conn.execute(sa.select(note_links.c.id).where(note_links.c.note_uid == uid)
                               .order_by(note_links.c.id)).scalars())
            return [_link(conn, project, label, i) for i in ids]

    def links_to(self, target: LinkTarget) -> list[Link]:
        with self._db.begin() as conn:
            rows = conn.execute(
                sa.select(note_links.c.id, notes.c.project_id, notes.c.label)
                .join(notes, notes.c.uid == note_links.c.note_uid)
                .where(note_links.c.target_kind == target.kind.value, note_links.c.target_project == target.project,
                       note_links.c.target_label == target.label).order_by(note_links.c.id)).all()
            return [_link(conn, r.project_id, r.label, r.id) for r in rows]

    def relink_item(self, project: str, old_label: str, new_label: str) -> None:
        with self._db.begin() as conn:
            conn.execute(sa.update(note_links).where(
                note_links.c.target_kind == TargetKind.ITEM.value, note_links.c.target_project == project,
                note_links.c.target_label == old_label).values(target_label=new_label))

    # --- triggers ---

    def add_trigger(self, project: str, label: str, new: NewTrigger) -> Trigger:
        with self._db.begin() as conn:
            uid = _note_uid(conn, project, label)
            link_id = None
            if new.kind is TriggerKind.EVENT and new.target is not None:
                link_id = _insert_link(conn, uid, new.target, LinkRole.TRIGGER)
            result = conn.execute(sa.insert(note_triggers).values(
                note_uid=uid, kind=new.kind.value, at=_text(new.at), link_id=link_id,
                target_status=new.target_status, fired_at=_text(new.fired_at), already_met=new.already_met))
            return _trigger(conn, label, _new_id(result))

    def triggers_of(self, project: str, label: str) -> list[Trigger]:
        with self._db.begin() as conn:
            uid = _note_uid(conn, project, label)
            ids: list[int] = list(conn.execute(sa.select(note_triggers.c.id).where(note_triggers.c.note_uid == uid)
                               .order_by(note_triggers.c.id)).scalars())
            return [_trigger(conn, label, i) for i in ids]

    def mark_fired(self, project: str, label: str, trigger_id: int, at: datetime) -> Trigger:
        with self._db.begin() as conn:
            uid = _note_uid(conn, project, label)
            conn.execute(sa.update(note_triggers).where(note_triggers.c.id == trigger_id,
                                                        note_triggers.c.note_uid == uid)
                         .values(fired_at=_text(at)))
            return _trigger(conn, label, trigger_id)

    def remove_trigger(self, project: str, label: str, trigger_id: int) -> None:
        with self._db.begin() as conn:
            uid = _note_uid(conn, project, label)
            link_id = conn.execute(sa.select(note_triggers.c.link_id).where(
                note_triggers.c.id == trigger_id, note_triggers.c.note_uid == uid)).scalar()
            conn.execute(sa.delete(note_triggers).where(note_triggers.c.id == trigger_id,
                                                        note_triggers.c.note_uid == uid))
            if link_id is not None:
                conn.execute(sa.delete(note_links).where(note_links.c.id == link_id))

    def reset_triggers(self, project: str, label: str) -> list[Trigger]:
        with self._db.begin() as conn:
            uid = _note_uid(conn, project, label)
            conn.execute(sa.update(note_triggers).where(note_triggers.c.note_uid == uid)
                         .values(fired_at=None, already_met=False))
            ids: list[int] = list(conn.execute(sa.select(note_triggers.c.id).where(note_triggers.c.note_uid == uid)
                                               .order_by(note_triggers.c.id)).scalars())
            return [_trigger(conn, label, i) for i in ids]

    # --- trash and purge ---

    def trash_topics(self, project: str, topics_: Sequence[str], notes_: Sequence[str], at: datetime) -> None:
        with self._db.begin() as conn:
            for label in topics_:
                conn.execute(sa.update(topics).where(topics.c.uid == _topic_uid(conn, project, label))
                             .values(deleted=_text(at)))
            for label in notes_:
                conn.execute(sa.update(notes).where(notes.c.uid == _note_uid(conn, project, label))
                             .values(deleted=_text(at)))

    def restore_topics(self, project: str, topics_: Sequence[str], notes_: Sequence[str]) -> None:
        with self._db.begin() as conn:
            for label in topics_:
                conn.execute(sa.update(topics).where(topics.c.uid == _topic_uid(conn, project, label))
                             .values(deleted=None))
            for label in notes_:
                conn.execute(sa.update(notes).where(notes.c.uid == _note_uid(conn, project, label))
                             .values(deleted=None))

    def purge_note(self, project: str, label: str) -> None:
        with self._db.begin() as conn:
            _purge_note(conn, project, label)

    def purge_topics(self, project: str, topics_: Sequence[str], notes_: Sequence[str]) -> None:
        with self._db.begin() as conn:
            for label in notes_:
                _purge_note(conn, project, label)
            for label in topics_:
                uid = _topic_uid(conn, project, label)
                conn.execute(sa.update(notes).where(notes.c.topic_uid == uid).values(topic_uid=None))
                conn.execute(sa.update(topics).where(topics.c.parent_uid == uid).values(parent_uid=None))
                conn.execute(sa.delete(note_links).where(
                    note_links.c.target_kind == TargetKind.TOPIC.value, note_links.c.target_project == project,
                    note_links.c.target_label == label))
                conn.execute(sa.delete(topics).where(topics.c.uid == uid))


class DatabaseNoteDocumentStore:
    def __init__(self, db: Database):
        self._db = db

    def names(self, project: str, label: str) -> list[str]:
        with self._db.begin() as conn:
            uid = _note_uid(conn, project, label)
            return list(conn.execute(sa.select(note_documents.c.name).where(note_documents.c.note_uid == uid)
                                     .order_by(note_documents.c.name)).scalars())

    def read(self, project: str, label: str, name: str) -> str:
        check_note_document_name(label, name)
        with self._db.begin() as conn:
            content = _content(conn, _note_uid(conn, project, label), name)
        if content is None:
            raise DocumentNotFoundError(name)
        return content

    def write(self, project: str, label: str, name: str, content: str, expected_version: str | None) -> None:
        check_note_document_name(label, name)
        with self._db.begin() as conn:
            uid = _note_uid(conn, project, label)
            current = _content(conn, uid, name)
            if current is None:
                if expected_version is not None:
                    raise VersionConflictError(name)
                conn.execute(sa.insert(note_documents).values(note_uid=uid, name=name, content=content))
                return
            if expected_version is None or content_version(current) != expected_version:
                raise VersionConflictError(name)
            conn.execute(sa.update(note_documents).where(note_documents.c.note_uid == uid,
                                                         note_documents.c.name == name).values(content=content))

    def append(self, project: str, label: str, name: str, text: str, header: str) -> str:
        check_note_document_name(label, name)
        with self._db.begin() as conn:
            uid = _note_uid(conn, project, label)
            current = _content(conn, uid, name)
            if current is None:
                content = f"{header}\n{text}"
                conn.execute(sa.insert(note_documents).values(note_uid=uid, name=name, content=content))
            else:
                content = f"{current.rstrip()}\n\n{text}"
                conn.execute(sa.update(note_documents).where(note_documents.c.note_uid == uid,
                                                             note_documents.c.name == name).values(content=content))
            return content

    def delete_document(self, project: str, label: str, name: str) -> None:
        check_note_document_name(label, name)
        with self._db.begin() as conn:
            uid = _note_uid(conn, project, label)
            conn.execute(sa.delete(note_documents).where(note_documents.c.note_uid == uid,
                                                         note_documents.c.name == name))


# --- helpers ---

def _purge_note(conn: sa.Connection, project: str, label: str) -> None:
    uid = _note_uid(conn, project, label)
    conn.execute(sa.delete(note_triggers).where(note_triggers.c.note_uid == uid))
    conn.execute(sa.delete(note_links).where(note_links.c.note_uid == uid))
    conn.execute(sa.delete(note_links).where(
        note_links.c.target_kind == TargetKind.NOTE.value, note_links.c.target_project == project,
        note_links.c.target_label == label))
    conn.execute(sa.delete(note_documents).where(note_documents.c.note_uid == uid))
    conn.execute(sa.delete(notes).where(notes.c.uid == uid))


def _ensure_project(conn: sa.Connection, project: str) -> None:
    if conn.execute(sa.select(projects.c.id).where(projects.c.id == project)).first() is None:
        conn.execute(sa.insert(projects).values(id=project))


def _next_label(conn: sa.Connection, project: str, kind: str) -> str:
    last = conn.execute(sa.select(note_counters.c.last).where(
        note_counters.c.project_id == project, note_counters.c.kind == kind)).scalar()
    number = (last or 0) + 1
    if last is None:
        conn.execute(sa.insert(note_counters).values(project_id=project, kind=kind, last=number))
    else:
        conn.execute(sa.update(note_counters).where(note_counters.c.project_id == project,
                                                    note_counters.c.kind == kind).values(last=number))
    return format_label(kind, number)


def _topic_uid(conn: sa.Connection, project: str, label: str) -> str:
    uid: str | None = conn.execute(sa.select(topics.c.uid).where(
        topics.c.project_id == project, topics.c.label == label)).scalar()
    if uid is None:
        raise TopicNotFoundError(label)
    return uid


def _note_uid(conn: sa.Connection, project: str, label: str) -> str:
    uid: str | None = conn.execute(sa.select(notes.c.uid).where(
        notes.c.project_id == project, notes.c.label == label)).scalar()
    if uid is None:
        raise NoteNotFoundError(label)
    return uid


def _parents(conn: sa.Connection, project: str) -> dict[str, str | None]:
    parent = topics.alias("parent")
    rows = conn.execute(sa.select(topics.c.label, parent.c.label.label("parent_label"))
                        .select_from(topics.outerjoin(parent, parent.c.uid == topics.c.parent_uid))
                        .where(topics.c.project_id == project)).all()
    return {r.label: r.parent_label for r in rows}


def _topic(conn: sa.Connection, project: str, label: str) -> Topic:
    parent = topics.alias("parent")
    row = conn.execute(sa.select(topics, parent.c.label.label("parent_label"))
                       .select_from(topics.outerjoin(parent, parent.c.uid == topics.c.parent_uid))
                       .where(topics.c.project_id == project, topics.c.label == label)).first()
    if row is None:
        raise TopicNotFoundError(label)
    return Topic(project=project, label=row.label, name=row.name, parent=row.parent_label,
                 due_at=_moment(row.due_at), created=_moment(row.created), deleted=_moment(row.deleted))


def _note(conn: sa.Connection, project: str, label: str) -> Note:
    row = conn.execute(sa.select(notes, topics.c.label.label("topic_label"))
                       .select_from(notes.outerjoin(topics, topics.c.uid == notes.c.topic_uid))
                       .where(notes.c.project_id == project, notes.c.label == label)).first()
    if row is None:
        raise NoteNotFoundError(label)
    return Note(project=project, label=row.label, summary=row.summary, body=row.body,
                status=NoteStatus(row.status), topic=row.topic_label, review_at=_moment(row.review_at),
                trigger_mode=TriggerMode(row.trigger_mode), created=_moment(row.created),
                updated=_moment(row.updated), archived=bool(row.archived), deleted=_moment(row.deleted))


def _new_id(result: sa.CursorResult[Any]) -> int:
    key = result.inserted_primary_key
    assert key is not None
    return int(key[0])


def _insert_link(conn: sa.Connection, note_uid: str, target: LinkTarget, role: LinkRole) -> int:
    result = conn.execute(sa.insert(note_links).values(
        note_uid=note_uid, target_kind=target.kind.value, target_project=target.project,
        target_label=target.label, role=role.value))
    return _new_id(result)


def _link(conn: sa.Connection, project: str, label: str, link_id: int) -> Link:
    row = conn.execute(sa.select(note_links).where(note_links.c.id == link_id)).one()
    return Link(note=label, project=project, id=row.id, role=LinkRole(row.role),
                target=LinkTarget(TargetKind(row.target_kind), row.target_project, row.target_label))


def _copy_links(conn: sa.Connection, old_uid: str, new_uid: str) -> dict[int, int]:
    """Copies the links of a note to another one; returns old link id -> new link id."""
    copied = {}
    for row in conn.execute(sa.select(note_links).where(note_links.c.note_uid == old_uid).order_by(note_links.c.id)):
        copied[row.id] = _insert_link(conn, new_uid, LinkTarget(TargetKind(row.target_kind), row.target_project,
                                                                row.target_label), LinkRole(row.role))
    return copied


def _trigger(conn: sa.Connection, label: str, trigger_id: int) -> Trigger:
    row = conn.execute(sa.select(note_triggers).where(note_triggers.c.id == trigger_id)).one()
    target = None
    if row.link_id is not None:
        link = conn.execute(sa.select(note_links).where(note_links.c.id == row.link_id)).one()
        target = LinkTarget(TargetKind(link.target_kind), link.target_project, link.target_label)
    return Trigger(id=row.id, note=label, kind=TriggerKind(row.kind), at=_moment(row.at), target=target,
                   target_status=row.target_status, fired_at=_moment(row.fired_at),
                   already_met=bool(row.already_met), link_id=row.link_id)


def _content(conn: sa.Connection, note_uid: str, name: str) -> str | None:
    content: str | None = conn.execute(sa.select(note_documents.c.content).where(
        note_documents.c.note_uid == note_uid, note_documents.c.name == name)).scalar()
    return content

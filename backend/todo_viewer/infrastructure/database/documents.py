"""Notes and specs in the central database, attached to the item's uid; a new id does not move them."""
from __future__ import annotations

from collections.abc import Mapping

import sqlalchemy as sa

from todo_viewer.domain.documents import content_version
from todo_viewer.domain.editing import ID_RE
from todo_viewer.domain.errors import (
    DocumentForbiddenError,
    DocumentNotFoundError,
    ItemFolderExistsError,
    ItemNotFoundError,
    VersionConflictError,
)
from todo_viewer.domain.source import Source

from .engine import Database
from .schema import documents, items

DOCUMENT_SUFFIXES = (".md", ".markdown", ".txt")


class DatabaseDocumentStore:
    def __init__(self, db: Database):
        self._db = db

    def read(self, source: Source, item_id: str, name: str) -> str:
        _check(item_id, name)
        with self._db.begin() as conn:
            uid = _uid(conn, source, item_id)
            content = None if uid is None else _content(conn, uid, name)
        if content is None:
            raise DocumentNotFoundError(name)
        return content

    def write(self, source: Source, item_id: str, name: str, content: str, expected_version: str | None) -> None:
        """Replaces the document if it still has `expected_version`; None means it must not exist yet."""
        _check(item_id, name)
        with self._db.begin() as conn:
            uid = _existing_item(conn, source, item_id)
            current = _content(conn, uid, name)
            if current is None:
                if expected_version is not None:
                    raise VersionConflictError(name)
                conn.execute(sa.insert(documents).values(item_uid=uid, name=name, content=content))
                return
            if expected_version is None or content_version(current) != expected_version:
                raise VersionConflictError(name)
            conn.execute(sa.update(documents).where(documents.c.item_uid == uid, documents.c.name == name)
                         .values(content=content))

    def append(self, source: Source, item_id: str, name: str, text: str, header: str) -> str:
        """Appends `text` after a blank line; a new document starts with `header`. Returns the new content."""
        _check(item_id, name)
        with self._db.begin() as conn:
            uid = _existing_item(conn, source, item_id)
            current = _content(conn, uid, name)
            if current is None:
                content = f"{header}\n{text}"
                conn.execute(sa.insert(documents).values(item_uid=uid, name=name, content=content))
            else:
                content = f"{current.rstrip()}\n\n{text}"
                conn.execute(sa.update(documents).where(documents.c.item_uid == uid, documents.c.name == name)
                             .values(content=content))
            return content

    def delete_documents(self, source: Source, item_id: str) -> None:
        _check_id(item_id)
        with self._db.begin() as conn:
            uid = _uid(conn, source, item_id)
            if uid is not None:
                conn.execute(sa.delete(documents).where(documents.c.item_uid == uid))

    def delete_document(self, source: Source, item_id: str, name: str) -> None:
        _check(item_id, name)
        with self._db.begin() as conn:
            uid = _uid(conn, source, item_id)
            if uid is not None:
                conn.execute(sa.delete(documents).where(documents.c.item_uid == uid, documents.c.name == name))

    def relabel_documents(self, source: Source, old_id: str, new_id: str, renames: Mapping[str, str]) -> None:
        """Renames documents of the item; they stay attached to it when its id changes.

        During a retype the item may still carry either id (the documents move before the id changes,
        and move back if the id cannot be changed), so it is looked up by both.
        """
        _check_id(old_id)
        _check_id(new_id)
        for name in (*renames, *renames.values()):
            _check_name(name)
        with self._db.begin() as conn:
            uid = _uid(conn, source, old_id) or _uid(conn, source, new_id)
            if uid is None or not _names(conn, uid):
                return
            other = _uid(conn, source, new_id)
            if other is not None and other != uid and _names(conn, other):
                raise ItemFolderExistsError(new_id)
            stored = {row.name: row.content for row in conn.execute(
                sa.select(documents.c.name, documents.c.content).where(documents.c.item_uid == uid))}
            conn.execute(sa.delete(documents).where(documents.c.item_uid == uid))
            conn.execute(sa.insert(documents), [dict(item_uid=uid, name=renames.get(n, n), content=c)
                                                for n, c in stored.items()])


def _uid(conn: sa.Connection, source: Source, item_id: str) -> str | None:
    uid: str | None = conn.execute(sa.select(items.c.uid).where(
        items.c.project_id == source.id, items.c.label == item_id)).scalar()
    return uid


def _existing_item(conn: sa.Connection, source: Source, item_id: str) -> str:
    uid = _uid(conn, source, item_id)
    if uid is None:
        raise ItemNotFoundError(item_id)
    return uid


def _content(conn: sa.Connection, uid: str, name: str) -> str | None:
    content: str | None = conn.execute(sa.select(documents.c.content).where(
        documents.c.item_uid == uid, documents.c.name == name)).scalar()
    return content


def _names(conn: sa.Connection, uid: str) -> list[str]:
    return list(conn.execute(sa.select(documents.c.name).where(documents.c.item_uid == uid)).scalars())


def _check(item_id: str, name: str) -> None:
    _check_id(item_id)
    _check_name(name)


def _check_id(item_id: str) -> None:
    if not ID_RE.match(item_id) or item_id in {".", ".."}:
        raise DocumentForbiddenError()


def _check_name(name: str) -> None:
    """Documents are markdown or text files named without a path."""
    if not name or "/" in name or "\\" in name or not name.lower().endswith(DOCUMENT_SUFFIXES):
        raise DocumentForbiddenError()

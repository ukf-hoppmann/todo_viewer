"""The state of every item and document after the last sync, kept in the central database."""
from __future__ import annotations

from collections.abc import Collection, Mapping

import sqlalchemy as sa

from todo_viewer.domain.sync import EntryKey, EntryState

from .engine import Database
from .schema import sync_entries


class DatabaseSyncStateStore:
    def __init__(self, db: Database):
        self._db = db

    def load(self, project_id: str, folder: str) -> dict[EntryKey, EntryState]:
        with self._db.begin() as conn:
            rows = conn.execute(sa.select(sync_entries).where(sync_entries.c.project_id == project_id,
                                                              sync_entries.c.folder == folder)).all()
        return {EntryKey(r.kind, r.label, r.name): EntryState(r.database_version, r.markdown_version) for r in rows}

    def save(self, project_id: str, folder: str, put: Mapping[EntryKey, EntryState],
             remove: Collection[EntryKey]) -> None:
        if not put and not remove:
            return
        with self._db.begin() as conn:
            for key in [*remove, *put]:
                conn.execute(sa.delete(sync_entries).where(
                    sync_entries.c.project_id == project_id, sync_entries.c.folder == folder,
                    sync_entries.c.kind == key.kind, sync_entries.c.label == key.label,
                    sync_entries.c.name == key.name))
            if put:
                conn.execute(sa.insert(sync_entries), [
                    dict(project_id=project_id, folder=folder, kind=k.kind, label=k.label, name=k.name,
                         database_version=v.database, markdown_version=v.markdown) for k, v in put.items()])

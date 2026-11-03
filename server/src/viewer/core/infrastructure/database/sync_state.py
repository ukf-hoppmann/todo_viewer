from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import datetime

from sqlalchemy import text

from viewer.core.infrastructure.database.engine import SqliteDatabase


class SqlSyncStateStore:
    """Hash jedes Eintrags beim letzten Sync in `core_sync_state(project_uid, uid, hash, synced_at)`."""

    def __init__(self, database: SqliteDatabase) -> None:
        self._database = database

    def load(self, project: str) -> dict[str, str]:
        with self._database.transaction() as tx:
            rows = tx.connection.execute(
                text("SELECT uid, hash FROM core_sync_state WHERE project_uid = :project"), {"project": project}
            ).all()
        return {uid: digest for uid, digest in rows}

    def save(self, project: str, hashes: Mapping[str, str], at: datetime) -> None:
        if not hashes:
            return
        with self._database.transaction() as tx:
            tx.connection.execute(
                text(
                    "INSERT INTO core_sync_state(project_uid, uid, hash, synced_at) "
                    "VALUES (:project, :uid, :hash, :at) "
                    "ON CONFLICT(project_uid, uid) DO UPDATE SET hash = excluded.hash, synced_at = excluded.synced_at"
                ),
                [
                    {"project": project, "uid": uid, "hash": digest, "at": at.isoformat()}
                    for uid, digest in hashes.items()
                ],
            )

    def forget(self, project: str, uids: Collection[str]) -> None:
        if not uids:
            return
        with self._database.transaction() as tx:
            tx.connection.execute(
                text("DELETE FROM core_sync_state WHERE project_uid = :project AND uid = :uid"),
                [{"project": project, "uid": uid} for uid in uids],
            )

    def last_synced(self, project: str) -> datetime | None:
        with self._database.transaction() as tx:
            value = tx.connection.execute(
                text("SELECT MAX(synced_at) FROM core_sync_state WHERE project_uid = :project"), {"project": project}
            ).scalar()
        return datetime.fromisoformat(value) if value else None

    def synced_times(self, project: str) -> dict[str, datetime]:
        with self._database.transaction() as tx:
            rows = tx.connection.execute(
                text("SELECT uid, synced_at FROM core_sync_state WHERE project_uid = :project"), {"project": project}
            ).all()
        return {uid: datetime.fromisoformat(at) for uid, at in rows if at}

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Connection, text

from viewer.core.application.ports import Transaction
from viewer.core.domain.errors import VersionConflict
from viewer.core.infrastructure.database import SqlTransaction
from viewer.plugins.backlog.application.ports import Notes
from viewer.plugins.backlog.domain.notes import Entry, NotesParts, Stamp


def _conn(tx: Transaction) -> Connection:
    assert isinstance(tx, SqlTransaction)
    return tx.connection


def _stamp(parts: NotesParts) -> dict[str, str | None]:
    stamp = parts.stamp
    return {
        "sd": stamp.day if stamp else None,
        "st": stamp.topic if stamp else None,
        "sc": stamp.checksum if stamp else None,
    }


class SqlNotesRepository:
    """Notes eines Items in `backlog_notes` (Vorspann, Kopf, Stempel) und `backlog_notes_entries` (Protokoll)."""

    def get(self, tx: Transaction, item_uid: str) -> Notes | None:
        connection = _conn(tx)
        row = connection.execute(text("SELECT * FROM backlog_notes WHERE item_uid = :u"), {"u": item_uid}).first()
        if row is None:
            return None
        entries = connection.execute(
            text("SELECT day, topic, body FROM backlog_notes_entries WHERE item_uid = :u ORDER BY position"),
            {"u": item_uid},
        ).all()
        stamp = Stamp(row.stamp_day, row.stamp_topic, row.stamp_checksum) if row.stamp_day is not None else None
        parts = NotesParts(row.preamble, row.state, stamp, tuple(Entry(e.day, e.topic, e.body) for e in entries))
        return Notes(
            row.item_uid, row.name, parts, row.state_revision, row.revision, datetime.fromisoformat(row.updated_at)
        )

    def names(self, tx: Transaction, item_uids: Sequence[str]) -> dict[str, str]:
        if not item_uids:
            return {}
        marks = {f"n{n}": uid for n, uid in enumerate(item_uids)}
        rows = _conn(tx).execute(
            text(
                "SELECT item_uid, name FROM backlog_notes WHERE item_uid IN ("
                + ", ".join(f":{name}" for name in marks)
                + ")"
            ),
            marks,
        )
        return {row.item_uid: row.name for row in rows}

    def insert(self, tx: Transaction, notes: Notes) -> None:
        _conn(tx).execute(
            text(
                "INSERT INTO backlog_notes(item_uid, name, preamble, state, stamp_day, stamp_topic, stamp_checksum, "
                "state_revision, revision, updated_at) VALUES (:u, :n, :p, :s, :sd, :st, :sc, :sr, :r, :t)"
            ),
            {
                "u": notes.item_uid,
                "n": notes.name,
                "p": notes.parts.preamble,
                "s": notes.parts.state,
                **_stamp(notes.parts),
                "sr": notes.state_revision,
                "r": notes.revision,
                "t": notes.updated_at.isoformat(),
            },
        )
        self._write_entries(tx, notes.item_uid, notes.parts.entries)

    def save(
        self, tx: Transaction, item_uid: str, parts: NotesParts, *, expected: int, state_changed: bool, at: datetime
    ) -> int:
        result = _conn(tx).execute(
            text(
                "UPDATE backlog_notes SET preamble = :p, state = :s, stamp_day = :sd, stamp_topic = :st, "
                "stamp_checksum = :sc, state_revision = state_revision + :inc, revision = revision + 1, "
                "updated_at = :t WHERE item_uid = :u AND revision = :r"
            ),
            {
                "p": parts.preamble,
                "s": parts.state,
                **_stamp(parts),
                "inc": 1 if state_changed else 0,
                "t": at.isoformat(),
                "u": item_uid,
                "r": expected,
            },
        )
        if result.rowcount != 1:
            raise VersionConflict("Die Notizen wurden inzwischen geändert", details={"expected": expected})
        _conn(tx).execute(text("DELETE FROM backlog_notes_entries WHERE item_uid = :u"), {"u": item_uid})
        self._write_entries(tx, item_uid, parts.entries)
        return expected + 1

    def rename(self, tx: Transaction, item_uid: str, new: str) -> None:
        _conn(tx).execute(text("UPDATE backlog_notes SET name = :n WHERE item_uid = :u"), {"n": new, "u": item_uid})

    def delete(self, tx: Transaction, item_uid: str) -> None:
        _conn(tx).execute(text("DELETE FROM backlog_notes WHERE item_uid = :u"), {"u": item_uid})

    @staticmethod
    def _write_entries(tx: Transaction, item_uid: str, entries: Sequence[Entry]) -> None:
        for position, entry in enumerate(entries):
            _conn(tx).execute(
                text(
                    "INSERT INTO backlog_notes_entries(item_uid, position, day, topic, body) "
                    "VALUES (:u, :i, :d, :o, :b)"
                ),
                {"u": item_uid, "i": position, "d": entry.day, "o": entry.topic, "b": entry.body},
            )

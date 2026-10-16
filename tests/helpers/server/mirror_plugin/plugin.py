"""Test-Plugin mit Codec und Teilnehmer auf echten SQLite-Tabellen: Referenz für die Plugins mit Spiegel.

Tabellen (Präfix `mirror_test_`): Einträge, Verweise auf `uid`, jedes je vergebene Label und Label-Zähler.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from typing import Any

from sqlalchemy import Connection, text
from sync_fakes import KINDS, LineCodec
from viewer.core.application.plugin import PluginContext, PluginDefinition
from viewer.core.application.ports import Database, Transaction
from viewer.core.application.sync import MirrorBinding, SyncChanges
from viewer.core.domain.errors import InvalidInput
from viewer.core.domain.plugin import Migration
from viewer.core.domain.sync import MirrorEntry
from viewer.core.infrastructure.database import SqlTransaction


def _conn(tx: Transaction) -> Connection:
    assert isinstance(tx, SqlTransaction)
    return tx.connection


def _v1(connection: Connection) -> None:
    for statement in (
        "CREATE TABLE mirror_test_entries (uid TEXT PRIMARY KEY, project TEXT NOT NULL, kind TEXT NOT NULL,"
        " label TEXT NOT NULL, title TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1, UNIQUE (project, label))",
        "CREATE TABLE mirror_test_labels (project TEXT NOT NULL, label TEXT NOT NULL,"
        " uid TEXT NOT NULL REFERENCES mirror_test_entries(uid) ON DELETE CASCADE, PRIMARY KEY (project, label))",
        "CREATE TABLE mirror_test_refs (uid TEXT NOT NULL REFERENCES mirror_test_entries(uid) ON DELETE CASCADE,"
        " field TEXT NOT NULL, position INTEGER NOT NULL,"
        " target_uid TEXT NOT NULL REFERENCES mirror_test_entries(uid), PRIMARY KEY (uid, field, position))",
        "CREATE TABLE mirror_test_counters (project TEXT NOT NULL, prefix TEXT NOT NULL, n INTEGER NOT NULL,"
        " PRIMARY KEY (project, prefix))",
    ):
        connection.exec_driver_sql(statement)


class SqlParticipant:
    def __init__(self, database: Database) -> None:
        self._database = database

    def load(self, project: str) -> list[MirrorEntry]:
        with self._database.transaction() as tx:
            c = _conn(tx)
            rows = c.execute(
                text("SELECT uid, kind, label, title FROM mirror_test_entries WHERE project = :p ORDER BY label"),
                {"p": project},
            ).all()
            refs = c.execute(
                text(
                    "SELECT r.uid, r.field, t.label FROM mirror_test_refs r JOIN mirror_test_entries t "
                    "ON t.uid = r.target_uid WHERE t.project = :p ORDER BY r.uid, r.field, r.position"
                ),
                {"p": project},
            ).all()
        by_uid: dict[str, dict[str, list[str]]] = {}
        for uid, field, label in refs:
            by_uid.setdefault(uid, {}).setdefault(field, []).append(label)
        return [
            MirrorEntry(kind, label, {"title": title}, {k: tuple(v) for k, v in by_uid.get(uid, {}).items()}, uid)
            for uid, kind, label, title in rows
        ]

    def resolve_labels(self, project: str, labels: Collection[str]) -> Mapping[str, str]:
        with self._database.transaction() as tx:
            rows = (
                _conn(tx)
                .execute(
                    text(
                        "SELECT l.label, e.label FROM mirror_test_labels l JOIN mirror_test_entries e ON e.uid = l.uid "
                        "WHERE l.project = :p"
                    ),
                    {"p": project},
                )
                .all()
            )
        known = {old: current for old, current in rows}
        return {label: known[label] for label in labels if label in known}

    def assign_labels(self, project: str, entries: Sequence[MirrorEntry], tx: Transaction) -> Mapping[str, str]:
        c = _conn(tx)
        result: dict[str, str] = {}
        for entry in entries:
            prefix = KINDS[entry.kind]
            c.execute(
                text(
                    "INSERT INTO mirror_test_counters(project, prefix, n) VALUES (:p, :x, 1) "
                    "ON CONFLICT(project, prefix) DO UPDATE SET n = n + 1"
                ),
                {"p": project, "x": prefix},
            )
            n = c.execute(
                text("SELECT n FROM mirror_test_counters WHERE project = :p AND prefix = :x"),
                {"p": project, "x": prefix},
            ).scalar_one()
            result[str(entry.placeholder)] = f"{prefix}-{n:03d}"
        return result

    def apply(self, project: str, changes: SyncChanges, tx: Transaction) -> None:
        c = _conn(tx)
        for entry in changes.created:
            c.execute(
                text("INSERT INTO mirror_test_entries(uid, project, kind, label, title) VALUES (:u, :p, :k, :l, :t)"),
                {"u": entry.uid, "p": project, "k": entry.kind, "l": entry.label, "t": entry.fields["title"]},
            )
            c.execute(
                text("INSERT INTO mirror_test_labels(project, label, uid) VALUES (:p, :l, :u)"),
                {"p": project, "l": entry.label, "u": entry.uid},
            )
        for entry in changes.updated:
            c.execute(
                text("UPDATE mirror_test_entries SET title = :t, revision = revision + 1 WHERE uid = :u"),
                {"t": entry.fields["title"], "u": entry.uid},
            )
            c.execute(text("DELETE FROM mirror_test_refs WHERE uid = :u"), {"u": entry.uid})
        for entry in changes.deleted:
            c.execute(text("DELETE FROM mirror_test_refs WHERE uid = :u OR target_uid = :u"), {"u": entry.uid})
            c.execute(text("DELETE FROM mirror_test_entries WHERE uid = :u"), {"u": entry.uid})
        for entry in (*changes.created, *changes.updated):  # Verweise zuletzt: Ziele können im selben Lauf entstehen
            for field, labels in entry.refs.items():
                for position, label in enumerate(labels):
                    target = c.execute(
                        text("SELECT uid FROM mirror_test_labels WHERE project = :p AND label = :l"),
                        {"p": project, "l": label},
                    ).scalar()
                    if target is None:
                        raise InvalidInput(f"Unbekannter Verweis {label}", details={"label": label})
                    c.execute(
                        text("INSERT INTO mirror_test_refs(uid, field, position, target_uid) VALUES (:u, :f, :n, :t)"),
                        {"u": entry.uid, "f": field, "n": position, "t": target},
                    )


class MirrorTestServices:
    def __init__(self, context: PluginContext) -> None:
        self.database = context.database
        self.participant = SqlParticipant(context.database)

    def seed(self, project: str, kind: str, title: str, uid: str, **refs: tuple[str, ...]) -> str:
        """Legt einen Eintrag mit dem nächsten Label an (Testaufbau, wie ihn später das Plugin selbst tut)."""
        entry = MirrorEntry(kind, None, {"title": title}, refs, uid, placeholder="seed")
        with self.database.transaction() as tx:
            label = self.participant.assign_labels(project, [entry], tx)["seed"]
            self.participant.apply(
                project, SyncChanges(created=(MirrorEntry(kind, label, {"title": title}, refs, uid),)), tx
            )
        return label

    def titles(self, project: str) -> dict[str, str]:
        return {e.label or "": e.fields["title"] for e in self.participant.load(project)}


def _build(context: PluginContext) -> MirrorTestServices:
    return MirrorTestServices(context)


def _mirror(services: Any) -> MirrorBinding:
    return MirrorBinding("mirror-test", LineCodec(), services.participant)


MIRROR_PLUGIN = PluginDefinition(id="mirror-test", build=_build, migrations=(Migration(1, _v1),), mirror=_mirror)

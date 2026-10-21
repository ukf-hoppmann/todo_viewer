"""Item-Notes in eigenen Tabellen: Migration 3 von `backlog` zerlegt die Notes-Dokumente, das Repository speichert
Kopf und Protokoll mit eigenen Versionen."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from migration_helpers import ordered, plugin, versions
from sqlalchemy import text
from viewer.core.domain.errors import VersionConflict
from viewer.core.infrastructure.database import MigrationRunner, SqliteDatabase
from viewer.plugins.backlog.application.ports import Notes
from viewer.plugins.backlog.domain.notes import Entry, NotesParts, Stamp, assemble
from viewer.plugins.backlog.infrastructure.database.notes import SqlNotesRepository
from viewer.plugins.backlog.infrastructure.database.schema import MIGRATIONS
from viewer.plugins.workspace.infrastructure.database.schema import MIGRATIONS as WORKSPACE

NOW = "2026-10-20T12:00:00+00:00"
AT = datetime(2026, 10, 20, 12, tzinfo=UTC)

PLAIN = "# STORY-001 — Login\n\n## 2026-10-01 — A\n\n### Discussed\n\n- a\n"
WITH_STATE = (
    "# STORY-002 — Alt\n\n## State\n\n- Goal/Status: x\n\n"
    "State confirmed after entry 2026-10-01 — A (0123456789ab)\n\n## 2026-10-01 — A\n\n- a\n"
)
PREAMBLE = "# STORY-003 — Vorspann\n\n## Summary\n\nAlt.\n\n## 2026-10-01 — A\n\n- a\n"
NO_ENTRIES = "# STORY-004 — Ohne\n\n## Discussed (2026-09-25)\n\n- a\n"
NO_TITLE = "## 2026-10-01 — A\n\n- a\n"
CRLF = "# STORY-006 — CRLF\r\n\r\n## 2026-10-01 — A\r\n\r\n- a\r\n"


def _defs(backlog_versions: int):  # type: ignore[no-untyped-def]
    return ordered(
        plugin("workspace", migrations=WORKSPACE),
        plugin("backlog", requires=("workspace",), migrations=MIGRATIONS[:backlog_versions]),
    )


def _items_with_documents(database: SqliteDatabase, documents: dict[str, tuple[str, str]]) -> None:
    """Legt je Label ein Item mit einem Notes-Dokument (Name, Inhalt) und eine Spec an."""
    with database.engine.begin() as connection:
        project: str = connection.execute(text("SELECT uid FROM workspace_projects")).scalar_one()
        connection.execute(
            text("INSERT INTO workspace_element_kinds(kind, owner, label_prefix) VALUES ('story', 'backlog', 'STORY')")
        )
        for label, (name, content) in documents.items():
            uid = label.lower()
            connection.execute(
                text(
                    "INSERT INTO workspace_elements(uid, project_uid, kind, label, created_at, updated_at) "
                    "VALUES (:u, :p, 'story', :l, :n, :n)"
                ),
                {"u": uid, "p": project, "l": label, "n": NOW},
            )
            connection.execute(
                text(
                    "INSERT INTO backlog_items(uid, type, title, status, priority, created) "
                    "VALUES (:u, 'Story', 'Titel', 'Open', 'Normal', '2026-10-01')"
                ),
                {"u": uid},
            )
            for doc_name, kind, doc_content, revision in (
                (name, "notes", content, 4),
                (f"{label}_spec.md", "spec", "# Spec\n", 2),
            ):
                connection.execute(
                    text(
                        "INSERT INTO backlog_documents(item_uid, name, kind, content, revision, updated_at) "
                        "VALUES (:u, :n, :k, :c, :r, :t)"
                    ),
                    {"u": uid, "n": doc_name, "k": kind, "c": doc_content, "r": revision, "t": NOW},
                )


def _body(content: str) -> str:
    """Der Text ohne Titelzeile: die Titelzeile kommt immer aus dem Item."""
    return content.split("\n", 1)[1] if content.startswith("# ") else content


def test_an_empty_database_reaches_version_3(runner: MigrationRunner, database: SqliteDatabase) -> None:
    runner.run(_defs(len(MIGRATIONS)))

    assert versions(database)["backlog"] == 3
    with database.engine.begin() as connection:
        tables = {row[0] for row in connection.execute(text("SELECT name FROM sqlite_master WHERE type = 'table'"))}
    assert {"backlog_notes", "backlog_notes_entries"} <= tables


def test_migration_3_splits_notes_documents_without_losing_text(
    runner: MigrationRunner, database: SqliteDatabase
) -> None:
    documents = {
        "STORY-001": ("STORY-001_notes.md", PLAIN),
        "STORY-002": ("STORY-002_notes.md", WITH_STATE),
        "STORY-003": ("STORY-003_notes.md", PREAMBLE),
        "STORY-004": ("STORY-004_notes.md", NO_ENTRIES),
        "STORY-005": ("STORY-005_notes.md", NO_TITLE),
        "STORY-006": ("STORY-006_notes.md", CRLF),
    }
    runner.run(_defs(2))
    _items_with_documents(database, documents)

    assert runner.run(_defs(3)) == [("backlog", 3)]

    repository = SqlNotesRepository()
    with database.transaction() as tx:
        for label, (name, content) in documents.items():
            notes = repository.get(tx, label.lower())
            assert notes is not None
            assert notes.name == name
            assert notes.revision == 4 and notes.state_revision == 1
            assert _body(assemble("X", notes.parts)) == _body(content), label
        state = repository.get(tx, "story-002")
        crlf = repository.get(tx, "story-006")
    assert state is not None and state.parts.state == "- Goal/Status: x"
    assert state.parts.stamp == Stamp("2026-10-01", "A", "0123456789ab")
    assert crlf is not None and crlf.parts.entries == ()  # kein verlustfreier Rundlauf: alles in den Vorspann
    with database.engine.begin() as connection:
        left = connection.execute(text("SELECT kind, count(*) FROM backlog_documents GROUP BY kind")).all()
    assert [tuple(row) for row in left] == [("spec", 6)]


def _empty_item(runner: MigrationRunner, database: SqliteDatabase) -> None:
    runner.run(_defs(2))
    _items_with_documents(database, {"STORY-001": ("STORY-001_notes.md", PLAIN)})
    runner.run(_defs(3))


def test_saving_needs_the_current_revision_and_counts_state_changes(
    runner: MigrationRunner, database: SqliteDatabase
) -> None:
    _empty_item(runner, database)
    repository = SqlNotesRepository()
    with database.transaction() as tx:
        notes = repository.get(tx, "story-001")
        assert notes is not None
        entries = (*notes.parts.entries, Entry("2026-10-02", "B", "\n- b\n"))
        assert (
            repository.save(
                tx, "story-001", NotesParts("\n", "", None, entries), expected=4, state_changed=False, at=AT
            )
            == 5
        )
        parts = NotesParts("\n", "- Goal/Status: y", Stamp("2026-10-02", "B", "aaaaaaaaaaaa"), entries)
        assert repository.save(tx, "story-001", parts, expected=5, state_changed=True, at=AT) == 6
        with pytest.raises(VersionConflict):
            repository.save(tx, "story-001", parts, expected=5, state_changed=False, at=AT)
        stored = repository.get(tx, "story-001")
    assert stored is not None
    assert stored.parts == parts
    assert (stored.revision, stored.state_revision) == (6, 2)


def test_insert_rename_names_and_delete(runner: MigrationRunner, database: SqliteDatabase) -> None:
    _empty_item(runner, database)
    repository = SqlNotesRepository()
    with database.transaction() as tx:
        repository.delete(tx, "story-001")
        assert repository.get(tx, "story-001") is None
        parts = NotesParts("\n", "", None, (Entry("2026-10-01", "A", "\n- a\n"),))
        repository.insert(tx, Notes("story-001", "STORY-001_notes.md", parts, 1, 1, AT))
        repository.rename(tx, "story-001", "TASK-009_notes.md")
        assert repository.names(tx, ["story-001", "other"]) == {"story-001": "TASK-009_notes.md"}
        stored = repository.get(tx, "story-001")
    assert stored is not None and stored.parts == parts and stored.updated_at == AT


def test_saving_the_state_can_also_check_its_own_version(runner: MigrationRunner, database: SqliteDatabase) -> None:
    _empty_item(runner, database)
    repository = SqlNotesRepository()
    with database.transaction() as tx:
        notes = repository.get(tx, "story-001")
        assert notes is not None
        parts = NotesParts("\n", "- Goal/Status: y", None, notes.parts.entries)
        with pytest.raises(VersionConflict):
            repository.save(tx, "story-001", parts, expected=4, expected_state=2, state_changed=True, at=AT)
        assert repository.save(tx, "story-001", parts, expected=4, expected_state=1, state_changed=True, at=AT) == 5


def test_parts_for_many_items_names_only_items_with_notes(runner: MigrationRunner, database: SqliteDatabase) -> None:
    _empty_item(runner, database)
    repository = SqlNotesRepository()
    with database.transaction() as tx:
        stored = repository.get(tx, "story-001")
        found = repository.parts_for(tx, ["story-001", "unknown"])
        empty = repository.parts_for(tx, [])
    assert stored is not None
    assert found == {"story-001": stored.parts}
    assert empty == {}

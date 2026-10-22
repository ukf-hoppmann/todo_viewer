"""Gelöschte Dokumente liegen als Schnappschuss in `backlog_trashed_documents` (Migration 4 von `backlog`)."""

from __future__ import annotations

from datetime import UTC, datetime

from migration_helpers import ordered, plugin, versions
from sqlalchemy import text
from viewer.core.infrastructure.database import MigrationRunner, SqliteDatabase
from viewer.plugins.backlog.application.ports import TrashedDocument
from viewer.plugins.backlog.infrastructure.database.schema import MIGRATIONS
from viewer.plugins.backlog.infrastructure.database.trashed_documents import SqlTrashedDocumentRepository
from viewer.plugins.workspace.infrastructure.database.schema import MIGRATIONS as WORKSPACE

NOW = "2026-10-22T12:00:00+00:00"
AT = datetime(2026, 10, 22, 12, tzinfo=UTC)


def _defs():  # type: ignore[no-untyped-def]
    return ordered(
        plugin("workspace", migrations=WORKSPACE),
        plugin("backlog", requires=("workspace",), migrations=MIGRATIONS),
    )


def _item(database: SqliteDatabase, label: str) -> tuple[str, str]:
    """Legt ein Item an und gibt (item_uid, project_uid) zurück."""
    with database.engine.begin() as connection:
        project: str = connection.execute(text("SELECT uid FROM workspace_projects")).scalar_one()
        connection.execute(
            text(
                "INSERT OR IGNORE INTO workspace_element_kinds(kind, owner, label_prefix) "
                "VALUES ('story', 'backlog', 'STORY')"
            )
        )
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
    return uid, project


def _snapshot(uid: str, item_uid: str, name: str, kind: str = "spec", summary: str | None = None) -> TrashedDocument:
    return TrashedDocument(uid, item_uid, name, kind, f"# {name}\n", summary, AT)


def test_an_empty_database_reaches_version_4_with_the_trash_table(
    runner: MigrationRunner, database: SqliteDatabase
) -> None:
    runner.run(_defs())

    assert versions(database)["backlog"] == 4
    with database.engine.begin() as connection:
        tables = {row[0] for row in connection.execute(text("SELECT name FROM sqlite_master WHERE type = 'table'"))}
    assert "backlog_trashed_documents" in tables


def test_snapshots_are_stored_read_and_removed(runner: MigrationRunner, database: SqliteDatabase) -> None:
    runner.run(_defs())
    item, _ = _item(database, "STORY-001")
    repository = SqlTrashedDocumentRepository()

    with database.transaction() as tx:
        repository.insert(tx, _snapshot("d1", item, "STORY-001_notes.md", "notes", "Kurz"))
        found = repository.get(tx, "d1")
        missing = repository.get(tx, "nein")
        repository.delete(tx, "d1")
        gone = repository.get(tx, "d1")

    assert found == _snapshot("d1", item, "STORY-001_notes.md", "notes", "Kurz")
    assert missing is None and gone is None


def test_listing_filters_by_project_and_text_and_puts_the_newest_first(
    runner: MigrationRunner, database: SqliteDatabase
) -> None:
    runner.run(_defs())
    first, project = _item(database, "STORY-001")
    second, _ = _item(database, "STORY-002")
    repository = SqlTrashedDocumentRepository()
    older = TrashedDocument("d1", first, "STORY-001_spec.md", "spec", "x", None, datetime(2026, 10, 21, tzinfo=UTC))
    newer = TrashedDocument("d2", second, "STORY-002_spec_api.md", "spec", "y", None, AT)

    with database.transaction() as tx:
        repository.insert(tx, older)
        repository.insert(tx, newer)
        everything = repository.list_deleted(tx, None, "")
        in_project = repository.list_deleted(tx, [project], "")
        elsewhere = repository.list_deleted(tx, ["anderes"], "")
        by_label = repository.list_deleted(tx, None, "story-001")
        by_name = repository.list_deleted(tx, None, "spec_api")

    assert [(d.document.uid, d.item_label, d.project_uid) for d in everything] == [
        ("d2", "STORY-002", project),
        ("d1", "STORY-001", project),
    ]
    assert [d.document.uid for d in in_project] == ["d2", "d1"]
    assert elsewhere == []
    assert [d.document.uid for d in by_label] == ["d1"]
    assert [d.document.uid for d in by_name] == ["d2"]


def test_the_snapshots_of_an_item_go_with_it(runner: MigrationRunner, database: SqliteDatabase) -> None:
    runner.run(_defs())
    item, _ = _item(database, "STORY-001")
    repository = SqlTrashedDocumentRepository()
    with database.transaction() as tx:
        repository.insert(tx, _snapshot("d1", item, "STORY-001_spec.md"))

    with database.engine.begin() as connection:
        connection.execute(text("DELETE FROM backlog_items WHERE uid = :u"), {"u": item})

    with database.transaction() as tx:
        assert repository.get(tx, "d1") is None

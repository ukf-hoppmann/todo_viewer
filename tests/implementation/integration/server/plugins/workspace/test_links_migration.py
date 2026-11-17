"""Migration 3 von `workspace`: die Rolle `node` kommt zu den Rollen der Verknüpfungen, vorhandene bleiben."""

from __future__ import annotations

import pytest
from migration_helpers import ordered, plugin, versions
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from viewer.core.infrastructure.database import MigrationRunner, SqliteDatabase
from viewer.plugins.workspace.infrastructure.database.schema import MIGRATIONS

NOW = "2026-11-17T12:00:00+00:00"


def _elements(connection: object) -> None:
    project = connection.execute(text("SELECT uid FROM workspace_projects")).scalar_one()  # type: ignore[attr-defined]
    connection.execute(  # type: ignore[attr-defined]
        text("INSERT INTO workspace_element_kinds(kind, owner, label_prefix) VALUES ('thing', 'x', 'THING')")
    )
    for uid, label in (("a", "THING-001"), ("b", "THING-002")):
        connection.execute(  # type: ignore[attr-defined]
            text(
                "INSERT INTO workspace_elements(uid, project_uid, kind, label, created_at, updated_at) "
                "VALUES (:u, :p, 'thing', :l, :n, :n)"
            ),
            {"u": uid, "p": project, "l": label, "n": NOW},
        )


def _link(connection: object, uid: str, role: str) -> None:
    connection.execute(  # type: ignore[attr-defined]
        text("INSERT INTO workspace_links(uid, from_uid, to_uid, role, created_at) VALUES (:u, 'a', 'b', :r, :n)"),
        {"u": uid, "r": role, "n": NOW},
    )


def test_links_made_before_the_migration_survive_and_the_role_node_is_accepted(
    runner: MigrationRunner, database: SqliteDatabase
) -> None:
    runner.run(ordered(plugin("workspace", migrations=MIGRATIONS[:2])))
    with database.engine.begin() as connection:
        _elements(connection)
        _link(connection, "l1", "reference")

    assert ("workspace", 3) in runner.run(ordered(plugin("workspace", migrations=MIGRATIONS)))

    assert versions(database)["workspace"] == len(MIGRATIONS)
    with database.engine.begin() as connection:
        assert connection.execute(text("SELECT uid, role FROM workspace_links")).all() == [("l1", "reference")]
        _link(connection, "l2", "node")


def test_other_roles_and_duplicates_are_still_refused(runner: MigrationRunner, database: SqliteDatabase) -> None:
    runner.run(ordered(plugin("workspace", migrations=MIGRATIONS)))
    with database.engine.begin() as connection:
        _elements(connection)
        _link(connection, "l1", "node")
    with pytest.raises(IntegrityError), database.engine.begin() as connection:
        _link(connection, "l2", "bogus")
    with pytest.raises(IntegrityError), database.engine.begin() as connection:
        _link(connection, "l3", "node")  # dasselbe Paar mit derselben Rolle


def test_the_index_on_the_target_still_exists(runner: MigrationRunner, database: SqliteDatabase) -> None:
    runner.run(ordered(plugin("workspace", migrations=MIGRATIONS)))
    with database.engine.begin() as connection:
        names = {r[0] for r in connection.execute(text("SELECT name FROM sqlite_master WHERE type = 'index'"))}
    assert "workspace_links_to" in names

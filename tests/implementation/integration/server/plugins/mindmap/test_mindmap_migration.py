"""Migration 1 von `mindmap`: ein leerer Stand wird auf die aktuelle Version gebracht, die Regeln stehen im Schema."""

from __future__ import annotations

import pytest
from migration_helpers import ordered, plugin, versions
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from viewer.core.application.plugin import PluginDefinition
from viewer.core.infrastructure.database import MigrationRunner, SqliteDatabase
from viewer.plugins.mindmap.infrastructure.database.schema import MIGRATIONS
from viewer.plugins.workspace.infrastructure.database.schema import MIGRATIONS as WORKSPACE

NOW = "2026-10-16T12:00:00+00:00"


def _defs() -> list[PluginDefinition]:
    return ordered(
        plugin("workspace", migrations=WORKSPACE), plugin("mindmap", requires=("workspace",), migrations=MIGRATIONS)
    )


def _prepare(runner: MigrationRunner, database: SqliteDatabase) -> str:
    """Bringt die Datenbank auf die aktuelle Version und legt einen Baum mit zwei Knoten an. Gibt die Projekt-uid."""
    assert ("mindmap", len(MIGRATIONS)) in runner.run(_defs())
    with database.engine.begin() as connection:
        project: str = connection.execute(text("SELECT uid FROM workspace_projects")).scalar_one()
        connection.execute(
            text(
                "INSERT INTO workspace_element_kinds(kind, owner, label_prefix) "
                "VALUES ('mindmap_node', 'mindmap', 'NODE')"
            )
        )
        for uid, label in (("n1", "NODE-001"), ("n2", "NODE-002")):
            connection.execute(
                text(
                    "INSERT INTO workspace_elements(uid, project_uid, kind, label, created_at, updated_at) "
                    "VALUES (:u, :p, 'mindmap_node', :l, :n, :n)"
                ),
                {"u": uid, "p": project, "l": label, "n": NOW},
            )
            connection.execute(text("INSERT INTO mindmap_nodes(uid, title) VALUES (:u, 'T')"), {"u": uid})
        connection.execute(
            text("INSERT INTO mindmap_trees(uid, project_uid, kind) VALUES ('t1', :p, 'project')"), {"p": project}
        )
    return project


def test_an_empty_database_gets_the_current_version_and_the_tables(
    runner: MigrationRunner, database: SqliteDatabase
) -> None:
    runner.run(_defs())

    assert versions(database)["mindmap"] == len(MIGRATIONS)
    with database.engine.begin() as connection:
        tables = {r[0] for r in connection.execute(text("SELECT name FROM sqlite_master WHERE type = 'table'"))}
        kinds = {r[0] for r in connection.execute(text("SELECT code FROM mindmap_tree_kinds"))}
    assert {
        "mindmap_tree_kinds",
        "mindmap_trees",
        "mindmap_nodes",
        "mindmap_placements",
        "mindmap_documents",
    } <= tables
    assert kinds == {"project"}
    assert runner.run(_defs()) == []  # ein zweiter Lauf tut nichts


def test_a_node_stands_at_most_once_per_tree_and_its_parent_in_the_same_tree(
    runner: MigrationRunner, database: SqliteDatabase
) -> None:
    _prepare(runner, database)
    insert = "INSERT INTO mindmap_placements(tree_uid, node_uid, parent_uid, position) VALUES ('t1', :n, :p, 0)"
    with database.engine.begin() as connection:
        connection.execute(text(insert), {"n": "n1", "p": None})
    with pytest.raises(IntegrityError), database.engine.begin() as connection:
        connection.execute(text(insert), {"n": "n1", "p": None})  # derselbe Knoten, derselbe Baum
    with pytest.raises(IntegrityError), database.engine.begin() as connection:
        connection.execute(text(insert), {"n": "n2", "p": "unbekannt"})  # Parent steht nicht im Baum
    with pytest.raises(IntegrityError), database.engine.begin() as connection:
        connection.execute(text(insert), {"n": "n2", "p": "n2"})  # nicht unter sich selbst
    with database.engine.begin() as connection:
        connection.execute(text(insert), {"n": "n2", "p": "n1"})


def test_a_project_has_one_project_tree(runner: MigrationRunner, database: SqliteDatabase) -> None:
    project = _prepare(runner, database)
    with pytest.raises(IntegrityError), database.engine.begin() as connection:
        connection.execute(
            text("INSERT INTO mindmap_trees(uid, project_uid, kind) VALUES ('t2', :p, 'project')"), {"p": project}
        )
    with pytest.raises(IntegrityError), database.engine.begin() as connection:
        connection.execute(text("INSERT INTO mindmap_trees(uid, project_uid, kind) VALUES ('t3', 'x', 'project')"))


def test_a_document_belongs_to_one_node_and_is_named_once(runner: MigrationRunner, database: SqliteDatabase) -> None:
    _prepare(runner, database)
    insert = (
        "INSERT INTO mindmap_documents(node_uid, name, content, updated_at) VALUES (:n, 'NODE-001_notes.md', 'x', :t)"
    )
    with database.engine.begin() as connection:
        connection.execute(text(insert), {"n": "n1", "t": NOW})
    with pytest.raises(IntegrityError), database.engine.begin() as connection:
        connection.execute(text(insert), {"n": "n1", "t": NOW})  # derselbe Name am selben Knoten
    with pytest.raises(IntegrityError), database.engine.begin() as connection:
        connection.execute(text(insert), {"n": "unbekannt", "t": NOW})  # Knoten gibt es nicht


def test_the_marks_are_a_fixed_list_and_a_node_has_none_at_first(runner: MigrationRunner, database: SqliteDatabase) -> None:
    _prepare(runner, database)

    with database.engine.begin() as connection:
        marks = {r[0] for r in connection.execute(text("SELECT code FROM mindmap_marks"))}
        current = connection.execute(text("SELECT mark FROM mindmap_nodes WHERE uid = 'n1'")).scalar_one()
    assert marks == {"discarded", "later"}
    assert current is None


def test_a_node_carries_one_mark_of_the_list_and_nothing_else(runner: MigrationRunner, database: SqliteDatabase) -> None:
    _prepare(runner, database)
    update = "UPDATE mindmap_nodes SET mark = :m WHERE uid = 'n1'"
    with database.engine.begin() as connection:
        connection.execute(text(update), {"m": "later"})
        connection.execute(text(update), {"m": "discarded"})  # ersetzt die erste
        connection.execute(text(update), {"m": None})  # keine
    with pytest.raises(IntegrityError), database.engine.begin() as connection:
        connection.execute(text(update), {"m": "verworfen"})


def test_version_2_data_survives_the_upgrade_to_the_marks(runner: MigrationRunner, database: SqliteDatabase) -> None:
    defs = _defs()
    old = [plugin("workspace", migrations=WORKSPACE), plugin("mindmap", requires=("workspace",), migrations=MIGRATIONS[:2])]
    runner.run(ordered(*old))
    with database.engine.begin() as connection:
        project: str = connection.execute(text("SELECT uid FROM workspace_projects")).scalar_one()
        connection.execute(
            text("INSERT INTO workspace_element_kinds(kind, owner, label_prefix) VALUES ('mindmap_node', 'mindmap', 'NODE')")
        )
        connection.execute(
            text(
                "INSERT INTO workspace_elements(uid, project_uid, kind, label, created_at, updated_at) "
                "VALUES ('n1', :p, 'mindmap_node', 'NODE-001', :n, :n)"
            ),
            {"p": project, "n": NOW},
        )
        connection.execute(text("INSERT INTO mindmap_nodes(uid, title, text) VALUES ('n1', 'Alt', 'Text')"))

    assert ("mindmap", 3) in runner.run(defs)

    with database.engine.begin() as connection:
        row = connection.execute(text("SELECT title, text, mark FROM mindmap_nodes WHERE uid = 'n1'")).one()
    assert tuple(row) == ("Alt", "Text", None)

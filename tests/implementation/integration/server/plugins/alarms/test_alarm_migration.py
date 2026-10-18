"""Migration 2 von `alarms`: ein Wecker aus Version 1 behält sein Ziel als erstes Element; erledigte laufen 24 h."""

from __future__ import annotations

from migration_helpers import ordered, plugin, versions
from sqlalchemy import text
from viewer.core.infrastructure.database import MigrationRunner, SqliteDatabase
from viewer.plugins.alarms.infrastructure.database.schema import MIGRATIONS
from viewer.plugins.workspace.infrastructure.database.schema import MIGRATIONS as WORKSPACE

NOW = "2026-10-16T12:00:00+00:00"


def _defs(alarm_versions: int):  # type: ignore[no-untyped-def]
    return ordered(
        plugin("workspace", migrations=WORKSPACE),
        plugin("alarms", requires=("workspace",), migrations=MIGRATIONS[:alarm_versions]),
    )


def test_a_version_1_alarm_keeps_its_target_and_a_done_one_gets_its_time(
    runner: MigrationRunner, database: SqliteDatabase
) -> None:
    runner.run(_defs(1))
    with database.engine.begin() as connection:
        project: str = connection.execute(text("SELECT uid FROM workspace_projects")).scalar_one()
        connection.execute(
            text("INSERT INTO workspace_element_kinds(kind, owner, label_prefix) VALUES ('alarm', 'alarms', 'ALARM')")
        )
        for uid, label in (("a1", "ALARM-001"), ("a2", "ALARM-002"), ("t", "ALARM-003")):
            connection.execute(
                text(
                    "INSERT INTO workspace_elements(uid, project_uid, kind, label, created_at, updated_at) "
                    "VALUES (:u, :p, 'alarm', :l, :n, :n)"
                ),
                {"u": uid, "p": project, "l": label, "n": NOW},
            )
        for uid, target, status in (("a1", "t", "Pending"), ("a2", None, "Done"), ("t", None, "Pending")):
            connection.execute(
                text(
                    "INSERT INTO alarms_alarms(uid, at, text, target_uid, target_text, status, snoozed_until) "
                    "VALUES (:u, :n, 'Text', :t, NULL, :s, NULL)"
                ),
                {"u": uid, "n": NOW, "t": target, "s": status},
            )

    assert runner.run(_defs(2)) == [("alarms", 2)]

    assert versions(database)["alarms"] == 2
    with database.engine.begin() as connection:
        targets = connection.execute(text("SELECT alarm_uid, position, element_uid FROM alarms_targets")).all()
        done: dict[str, str | None] = dict(connection.execute(text("SELECT uid, done_at FROM alarms_alarms")).all())
        statuses = {row[0] for row in connection.execute(text("SELECT code FROM alarms_statuses"))}
    assert [tuple(row) for row in targets] == [("a1", 0, "t")]
    assert done["a1"] is None and done["a2"] is not None
    assert "Expired" in statuses

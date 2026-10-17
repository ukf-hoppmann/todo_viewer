"""Hilfen für Tests mit Migrationen: kleine Plugin-Definitionen mit SQL."""

from __future__ import annotations

from typing import Any, cast

from viewer.core.application.core_plugin import build_core_definition
from viewer.core.application.plugin import PluginDefinition
from viewer.core.domain.plugin import Migration, load_order
from viewer.core.infrastructure.database import SqliteDatabase
from viewer.core.infrastructure.database.core_schema import CORE_MIGRATIONS


class NoStore:
    def get(self, owner: str) -> None:
        return None

    def put(self, owner: str, document: dict[str, Any]) -> None:
        pass


def mig(version: int, *statements: str) -> Migration:
    def apply(connection: Any) -> None:
        for statement in statements:
            connection.exec_driver_sql(statement)

    return Migration(version, apply)


def plugin(plugin_id: str, requires: tuple[str, ...] = (), migrations: tuple[Migration, ...] = ()) -> PluginDefinition:
    return PluginDefinition(plugin_id, lambda c: None, requires=requires, migrations=migrations)


def ordered(*defs: PluginDefinition) -> list[PluginDefinition]:
    core = build_core_definition(NoStore(), CORE_MIGRATIONS, cast(Any, None))
    all_defs = [core, *defs]
    by_id = {d.id: d for d in all_defs}
    return [by_id[i] for i in load_order(all_defs)]


def versions(database: SqliteDatabase) -> dict[str, int]:
    with database.transaction() as tx:
        return dict(tx.connection.exec_driver_sql("SELECT owner, version FROM core_migrations").all())


def tables(database: SqliteDatabase) -> set[str]:
    with database.transaction() as tx:
        rows = tx.connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'").all()
    return {r[0] for r in rows}

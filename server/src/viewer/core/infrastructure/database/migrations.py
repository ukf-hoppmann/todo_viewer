from __future__ import annotations

from collections.abc import Sequence

import structlog
from sqlalchemy import Connection, text

from viewer.core.application.plugin import PluginDefinition
from viewer.core.application.ports import BackupMaker
from viewer.core.domain.errors import DatabaseTooNew, MigrationFailed, SchemaViolation
from viewer.core.domain.plugin import schema_problems, table_prefix
from viewer.core.infrastructure.database.engine import SqliteDatabase

log = structlog.get_logger(__name__)

MIGRATIONS_TABLE = "core_migrations"
BACKUP_REASON = "migration"


class MigrationRunner:
    """Führt die ausstehenden Migrationen aller Besitzer aus, in der Reihenfolge der übergebenen Definitionen
    (Core zuerst, dann Plugins nach `requires`). Stand in `core_migrations(owner, version)`."""

    def __init__(self, database: SqliteDatabase, backups: BackupMaker) -> None:
        self._database = database
        self._backups = backups

    def run(self, definitions: Sequence[PluginDefinition]) -> list[tuple[str, int]]:
        """Gibt die angewendeten `(besitzer, version)` zurück."""
        current = self._current_versions()
        for definition in definitions:
            newest = max((m.version for m in definition.migrations), default=0)
            if current.get(definition.id, 0) > newest:
                raise DatabaseTooNew(
                    f"Die Datenbank ist neuer als der Code: {definition.id} steht auf {current[definition.id]}, "
                    f"bekannt ist {newest}",
                    details={"owner": definition.id, "database": current[definition.id], "code": newest},
                )
        pending = [
            (definition, migration)
            for definition in definitions
            for migration in definition.migrations
            if migration.version > current.get(definition.id, 0)
        ]
        if not pending:
            return []
        if self._has_data():
            path = self._backups.create(BACKUP_REASON)
            log.info("migration_backup", path=str(path))
        applied: list[tuple[str, int]] = []
        for definition, migration in pending:
            allowed = {definition.id, "core", *definition.requires}
            try:
                with self._database.transaction() as tx:
                    connection = tx.connection
                    before = _tables(connection)
                    migration.apply(connection)
                    after = _tables(connection)
                    self._check_schema(connection, definition.id, before, after, allowed)
                    connection.execute(
                        text(
                            f"INSERT INTO {MIGRATIONS_TABLE}(owner, version) VALUES (:owner, :version) "
                            "ON CONFLICT(owner) DO UPDATE SET version = excluded.version"
                        ),
                        {"owner": definition.id, "version": migration.version},
                    )
            except (SchemaViolation, MigrationFailed):
                raise
            except Exception as exc:
                raise MigrationFailed(
                    f"Migration {definition.id} {migration.version} ist fehlgeschlagen: {exc}",
                    details={"owner": definition.id, "version": migration.version},
                ) from exc
            log.info("migration_applied", owner=definition.id, version=migration.version)
            applied.append((definition.id, migration.version))
        return applied

    def _current_versions(self) -> dict[str, int]:
        with self._database.transaction() as tx:
            tx.connection.exec_driver_sql(
                f"CREATE TABLE IF NOT EXISTS {MIGRATIONS_TABLE} (owner TEXT PRIMARY KEY, version INTEGER NOT NULL)"
            )
            rows = tx.connection.exec_driver_sql(f"SELECT owner, version FROM {MIGRATIONS_TABLE}").all()
        return {owner: version for owner, version in rows}

    def _has_data(self) -> bool:
        with self._database.transaction() as tx:
            return bool(_tables(tx.connection) - {MIGRATIONS_TABLE})

    def _check_schema(
        self, connection: Connection, owner: str, before: set[str], after: set[str], allowed: set[str]
    ) -> None:
        prefix = table_prefix(owner)
        owned = {t for t in after if t.startswith(prefix)}
        created = after - before
        references = {t: _references(connection, t) for t in owned | created}
        problems = schema_problems(owner, created | owned, references, allowed)
        if problems:
            raise SchemaViolation(
                f"Schema von '{owner}' verletzt die Regeln: " + "; ".join(problems), details={"problems": problems}
            )


def _tables(connection: Connection) -> set[str]:
    rows = connection.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    )
    return {name for (name,) in rows}


def _references(connection: Connection, table: str) -> set[str]:
    rows = connection.exec_driver_sql(f'PRAGMA foreign_key_list("{table}")').all()
    return {row[2] for row in rows}

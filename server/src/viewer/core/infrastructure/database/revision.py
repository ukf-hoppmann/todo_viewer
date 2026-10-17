from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import ColumnElement, Connection, Table, select, update

from viewer.core.domain.errors import NotFound, VersionConflict


def update_with_revision(
    connection: Connection,
    table: Table,
    where: ColumnElement[bool],
    expected_revision: int,
    values: Mapping[str, Any],
) -> int:
    """Optimistische Sperre: ändert die Zeile nur, wenn ihre `revision` noch `expected_revision` ist.

    Erhöht die `revision` und gibt den neuen Wert zurück. Sonst `version_conflict` (Zeile wurde geändert) oder
    `not_found` (Zeile fehlt); in beiden Fällen bleibt die Zeile unverändert.
    """
    result = connection.execute(
        update(table)
        .where(where, table.c.revision == expected_revision)
        .values(**values, revision=table.c.revision + 1)
    )
    if result.rowcount == 1:
        return expected_revision + 1
    current = connection.execute(select(table.c.revision).where(where)).first()
    if current is None:
        raise NotFound(f"Eintrag in {table.name} nicht gefunden")
    raise VersionConflict(
        f"Eintrag in {table.name} wurde seit dem Lesen geändert",
        details={"table": table.name, "expected": expected_revision, "current": current[0]},
    )

"""Liest die alte Datenbank, nur lesend, in Zeilen (Wörterbücher) in der Reihenfolge der alten Schlüssel."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import sqlalchemy as sa

from viewer.app.import_legacy import legacy_schema as schema

Row = dict[str, Any]


class LegacyError(Exception):
    """Die alte Datenbank ist nicht zu lesen oder darf nicht übernommen werden (Text für den Anwender)."""


@dataclass
class Legacy:
    projects: list[Row]
    items: list[Row]
    dependencies: list[Row]
    extra_fields: list[Row]
    document_names: list[Row]
    documents: list[Row]
    topics: list[Row]
    notes: list[Row]
    links: list[Row]
    triggers: list[Row]
    note_documents: list[Row]
    counters: list[Row]
    notices: list[Row]


def _rows(connection: sa.Connection, table: sa.Table, *order: sa.ColumnElement[Any]) -> list[Row]:
    statement = sa.select(table).order_by(*(order or tuple(table.primary_key.columns)))
    return [dict(row._mapping) for row in connection.execute(statement)]


def merge_name_placeholders(legacy: Legacy) -> list[str]:
    """Frühere Fassungen haben Topics und Notes unter der Kennung `<Projektname>` abgelegt, ohne eine Projektzeile mit
    Namen: Eine Zeile ohne Namen, deren Kennung der Name eines anderen Projekts ist, geht in dieses Projekt auf.
    Gibt die Kennungen der aufgelösten Platzhalter zurück."""
    by_name = {str(p["name"]).lower(): str(p["id"]) for p in legacy.projects if p.get("name")}
    target = {
        str(p["id"]): by_name[str(p["id"]).lower()]
        for p in legacy.projects
        if not p.get("name") and str(p["id"]).lower() in by_name
    }
    if not target:
        return []
    legacy.projects[:] = [p for p in legacy.projects if str(p["id"]) not in target]
    for table, columns in (
        (legacy.items, ("project_id",)),
        (legacy.topics, ("project_id",)),
        (legacy.notes, ("project_id",)),
        (legacy.notices, ("project_id", "counterpart_project")),
        (legacy.links, ("target_project",)),
    ):
        for row in table:
            for column in columns:
                row[column] = target.get(str(row[column]), row[column])
    highest: dict[tuple[str, str], Row] = {}
    for row in legacy.counters:
        row["project_id"] = target.get(str(row["project_id"]), row["project_id"])
        key = (str(row["project_id"]), str(row["kind"]))
        if key not in highest or (row["last"] or 0) > (highest[key]["last"] or 0):
            highest[key] = row
    legacy.counters[:] = list(highest.values())
    return sorted(target)


def read_legacy(path: Path) -> Legacy:
    """Öffnet die Datei schreibgeschützt (`mode=ro`); fehlt sie oder eine Tabelle, ist das ein `LegacyError`."""
    if not path.is_file():
        raise LegacyError(f"Die alte Datenbank gibt es nicht: {path}")
    engine = sa.create_engine(f"sqlite:///file:{path.resolve()}?mode=ro&uri=true")
    try:
        with engine.connect() as connection:
            present = set(sa.inspect(connection).get_table_names())
            missing = sorted(set(schema.metadata.tables) - present)
            if missing:
                raise LegacyError(f"In der alten Datenbank fehlen Tabellen: {', '.join(missing)}")
            t = schema
            legacy = Legacy(
                projects=_rows(
                    connection, t.projects, sa.func.coalesce(t.projects.c.position, 1_000_000), t.projects.c.id
                ),
                items=_rows(connection, t.items, t.items.c.project_id, t.items.c.position, t.items.c.uid),
                dependencies=_rows(connection, t.item_dependencies),
                extra_fields=_rows(connection, t.item_extra_fields),
                document_names=_rows(connection, t.item_document_names),
                documents=_rows(connection, t.documents),
                topics=_rows(connection, t.topics, t.topics.c.project_id, t.topics.c.created, t.topics.c.uid),
                notes=_rows(connection, t.notes, t.notes.c.project_id, t.notes.c.created, t.notes.c.uid),
                links=_rows(connection, t.note_links, t.note_links.c.id),
                triggers=_rows(connection, t.note_triggers, t.note_triggers.c.id),
                note_documents=_rows(connection, t.note_documents),
                counters=_rows(connection, t.note_counters),
                notices=_rows(connection, t.note_notices, t.note_notices.c.id),
            )
            merge_name_placeholders(legacy)
            return legacy
    except sa.exc.DatabaseError as exc:
        raise LegacyError(f"Die alte Datenbank ist nicht zu lesen: {exc.orig}") from exc
    finally:
        engine.dispose()

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
            return Legacy(
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
    except sa.exc.DatabaseError as exc:
        raise LegacyError(f"Die alte Datenbank ist nicht zu lesen: {exc.orig}") from exc
    finally:
        engine.dispose()

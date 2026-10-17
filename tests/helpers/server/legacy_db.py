"""Baut eine synthetische alte Datenbank (Schema des alten Viewers) für die Tests der Datenübernahme.

Nichts hier stammt aus echten Daten; die Fälle stehen in `tests/fixtures/legacy-db/README.md`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import sqlalchemy as sa
from viewer.app.import_legacy import legacy_schema as schema

P_MAIN, P_TWO, P_GENERAL = "p-main", "p-two", "p-general"


def _item(uid: str, label: str, type_: str, **fields: Any) -> dict[str, Any]:
    return {
        "uid": uid,
        "project_id": P_MAIN,
        "label": label,
        "item_type": type_,
        "title": f"Titel {label}",
        "status": "Open",
        "parent_uid": None,
        "required_for_parent": None,
        "created": "2026-01-02",
        "area": None,
        "priority": "Normal",
        "goal": "Ziel",
        "completion_criteria": "Kriterien",
        "summary": None,
        "resolution": None,
        "location": "active",
        "deleted": None,
        "position": 0,
        **fields,
    }


def _note(uid: str, label: str, **fields: Any) -> dict[str, Any]:
    return {
        "uid": uid,
        "project_id": P_MAIN,
        "label": label,
        "summary": f"Kurzfassung {label}",
        "body": None,
        "status": "waiting",
        "topic_uid": None,
        "review_at": "2026-12-01T09:00:00+00:00",
        "trigger_mode": "any",
        "created": "2026-02-01T08:00:00+00:00",
        "updated": "2026-02-02T08:00:00+00:00",
        "archived": False,
        "deleted": None,
        **fields,
    }


def _topic(uid: str, label: str, **fields: Any) -> dict[str, Any]:
    return {
        "uid": uid,
        "project_id": P_MAIN,
        "label": label,
        "name": f"Name {label}",
        "parent_uid": None,
        "due_at": None,
        "created": "2026-02-01T08:00:00+00:00",
        "deleted": None,
        **fields,
    }


def content(**overrides: Any) -> dict[str, list[dict[str, Any]]]:
    """Alle Zeilen der Fälle je Tabelle; `overrides` ersetzt ganze Tabellen (z. B. andere Items)."""
    projects = [
        {"id": P_MAIN, "name": "Viewer", "backend": "database", "path": "/alt/viewer", "sync_path": "/spiegel/viewer",
         "mirror_database": False, "mirror_disabled": False, "auto_sync": True, "position": 1},
        {"id": P_TWO, "name": "Zwei", "backend": "database", "path": "/alt/zwei", "sync_path": "/spiegel/zwei",
         "mirror_database": False, "mirror_disabled": True, "auto_sync": False, "position": 2},
        {"id": P_GENERAL, "name": "Allgemein", "backend": "database", "path": None, "sync_path": None,
         "mirror_database": False, "mirror_disabled": False, "auto_sync": False, "position": 0},
    ]  # fmt: skip
    items = [
        _item("e1", "EPIC-001", "Epic", priority="High", area="Server", position=1),
        _item("s1", "STORY-001", "Story", parent_uid="e1", required_for_parent=True, priority="dringend", position=2,
              area="Server", status="In progress", summary="Fertig bald"),
        _item("s2", "STORY-002", "Story", parent_uid="e1", priority=None, area="Client", position=3),
        _item("t1", "TASK-001", "Task", parent_uid="s1", priority="Low", status="Completed", location="archive",
              position=4, resolution="Erledigt"),
        _item("t2", "TASK-002", "Task", parent_uid="s1", deleted="2026-03-01T10:00:00+00:00", position=5),
        _item("s3", "STORY-003", "Story", priority="Medium", position=6, area="Client"),
        _item("s4", "STORY-004", "Story", priority="Prospective", position=7),
        _item("t3", "TASK-003", "Task", priority="Important", position=8, parent_uid="missing"),
        _item("s5", "STORY-005", "Story", priority="wichtig", position=9),
        _item("x1", "TASK-001", "Task", project_id=P_TWO, priority="Urgent", position=1),
    ]  # fmt: skip
    topics = [
        _topic("tp1", "TOPIC-001"),
        _topic("tp2", "TOPIC-002", parent_uid="tp1", due_at="2026-11-30T00:00:00+00:00"),
        _topic("tp3", "TOPIC-003", deleted="2026-03-02T10:00:00+00:00"),
    ]
    notes = [
        _note("n1", "NOTE-001", topic_uid="tp1", body="Langtext"),
        _note("n2", "NOTE-002", status="snoozed"),
        _note("n3", "NOTE-003", status="done", archived=True),
        _note("n4", "NOTE-004", trigger_mode="all"),
        _note("n5", "NOTE-005", topic_uid="tp2"),
        _note("n6", "NOTE-006", deleted="2026-03-03T10:00:00+00:00"),
        _note("n7", "NOTE-001", project_id=P_TWO),
    ]
    return {
        "projects": projects,
        "items": items,
        "item_dependencies": [
            {"item_uid": "t1", "position": 0, "depends_on_uid": "s2"},
            {"item_uid": "t1", "position": 1, "depends_on_uid": "gone"},
        ],
        "item_extra_fields": [
            {"item_uid": "s2", "position": 0, "key": "Implementation", "value": "Erste Zeile\nZweite Zeile"},
            {"item_uid": "s2", "position": 1, "key": "Context", "value": "Kontext"},
            {"item_uid": "s3", "position": 0, "key": "Verification", "value": "Geprüft"},
        ],
        "item_document_names": [
            {"item_uid": "s3", "kind": "notes", "position": 0, "name": "STORY-003_notes.md"},
            {"item_uid": "s3", "kind": "spec", "position": 0, "name": "STORY-003_spec.md"},
            {"item_uid": "s3", "kind": "spec", "position": 1, "name": "STORY-003_spec_ui.md"},
        ],
        "documents": [
            {"item_uid": "s3", "name": "STORY-003_notes.md", "content": "# STORY-003 — Titel STORY-003\n"},
            {"item_uid": "s3", "name": "STORY-003_spec.md", "content": "# Spec\n"},
            {"item_uid": "s1", "name": "STORY-001_spec.md", "content": "# Ohne Namensliste\n"},
        ],
        "topics": topics,
        "notes": notes,
        "note_links": [
            {
                "id": 1,
                "note_uid": "n4",
                "target_kind": "item",
                "target_project": P_MAIN,
                "target_label": "STORY-001",
                "role": "trigger",
            },
            {
                "id": 2,
                "note_uid": "n1",
                "target_kind": "item",
                "target_project": P_MAIN,
                "target_label": "STORY-001",
                "role": "reference",
            },
            {
                "id": 3,
                "note_uid": "n7",
                "target_kind": "item",
                "target_project": P_MAIN,
                "target_label": "STORY-002",
                "role": "reference",
            },
            {
                "id": 4,
                "note_uid": "n3",
                "target_kind": "item",
                "target_project": P_MAIN,
                "target_label": "STORY-005",
                "role": "origin",
            },
            {
                "id": 5,
                "note_uid": "n1",
                "target_kind": "item",
                "target_project": P_MAIN,
                "target_label": "STORY-999",
                "role": "reference",
            },
            {
                "id": 6,
                "note_uid": "n2",
                "target_kind": "note",
                "target_project": P_MAIN,
                "target_label": "NOTE-001",
                "role": "reference",
            },
            {
                "id": 7,
                "note_uid": "n2",
                "target_kind": "topic",
                "target_project": P_MAIN,
                "target_label": "TOPIC-001",
                "role": "reference",
            },
            {
                "id": 8,
                "note_uid": "n1",
                "target_kind": "item",
                "target_project": P_MAIN,
                "target_label": "STORY-001",
                "role": "reference",
            },
        ],  # fmt: skip
        "note_triggers": [
            {
                "id": 1,
                "note_uid": "n2",
                "kind": "time",
                "at": "2030-01-01T09:00:00+00:00",
                "link_id": None,
                "target_status": None,
                "fired_at": None,
                "already_met": False,
            },
            {
                "id": 2,
                "note_uid": "n4",
                "kind": "event",
                "at": None,
                "link_id": 1,
                "target_status": "Completed",
                "fired_at": "2026-04-01T09:00:00+00:00",
                "already_met": True,
            },
            {
                "id": 3,
                "note_uid": "n5",
                "kind": "topic_due",
                "at": None,
                "link_id": None,
                "target_status": None,
                "fired_at": None,
                "already_met": False,
            },
            {
                "id": 4,
                "note_uid": "n7",
                "kind": "time",
                "at": "2026-05-01T09:00:00+00:00",
                "link_id": None,
                "target_status": None,
                "fired_at": "2026-05-01T09:00:00+00:00",
                "already_met": False,
            },
            {
                "id": 5,
                "note_uid": "n4",
                "kind": "event",
                "at": None,
                "link_id": None,
                "target_status": "In progress",
                "fired_at": None,
                "already_met": False,
            },
        ],  # fmt: skip
        "note_documents": [
            {"note_uid": "n1", "name": "NOTE-001_notes.md", "content": "# NOTE-001\n"},
            {"note_uid": "gone", "name": "NOTE-099_notes.md", "content": "weg"},
        ],
        "note_counters": [
            {"project_id": P_MAIN, "kind": "note", "last": 9},
            {"project_id": P_MAIN, "kind": "topic", "last": 5},
            {"project_id": P_TWO, "kind": "note", "last": 3},
            {"project_id": P_TWO, "kind": "weird", "last": 1},
        ],
        "note_notices": [
            {
                "id": 1,
                "side": "note",
                "project_id": P_MAIN,
                "label": "NOTE-001",
                "cause": "item_completed",
                "counterpart_kind": "item",
                "counterpart_project": P_MAIN,
                "counterpart_label": "STORY-001",
                "created_at": "2026-05-02T09:00:00+00:00",
                "decided_at": None,
                "decision": None,
            },
            {
                "id": 2,
                "side": "item",
                "project_id": P_MAIN,
                "label": "STORY-002",
                "cause": "note_promoted",
                "counterpart_kind": "note",
                "counterpart_project": P_MAIN,
                "counterpart_label": "NOTE-003",
                "created_at": "2026-05-03T09:00:00+00:00",
                "decided_at": "2026-05-04T09:00:00+00:00",
                "decision": "acknowledge",
            },
            {
                "id": 3,
                "side": "note",
                "project_id": P_MAIN,
                "label": "NOTE-001",
                "cause": "project_unreachable",
                "counterpart_kind": "item",
                "counterpart_project": "lost",
                "counterpart_label": "STORY-001",
                "created_at": "2026-05-05T09:00:00+00:00",
                "decided_at": None,
                "decision": None,
            },
        ],  # fmt: skip
        **overrides,
    }


def build(path: Path, **overrides: Any) -> Path:
    """Legt die alte Datenbank mit den Fällen an (oder mit ersetzten Tabellen) und gibt den Pfad zurück."""
    engine = sa.create_engine(f"sqlite:///{path}")
    try:
        schema.metadata.create_all(engine)
        with engine.begin() as connection:
            for name, rows in content(**overrides).items():
                if rows:
                    connection.execute(schema.metadata.tables[name].insert(), rows)
    finally:
        engine.dispose()
    return path

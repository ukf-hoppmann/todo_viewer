"""Die Tabellen der alten Datenbank (`configs/todo.db`), nur zum Lesen. Eine eigene Kopie der Spalten: der Altcode
wird nie importiert (Regel 0)."""

from __future__ import annotations

import sqlalchemy as sa

metadata = sa.MetaData()

projects = sa.Table(
    "projects",
    metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    sa.Column("name", sa.Text),
    sa.Column("backend", sa.String(20)),
    sa.Column("path", sa.Text),
    sa.Column("sync_path", sa.Text),
    sa.Column("mirror_database", sa.Boolean),
    sa.Column("mirror_disabled", sa.Boolean),
    sa.Column("auto_sync", sa.Boolean),
    sa.Column("position", sa.Integer),
)

items = sa.Table(
    "items",
    metadata,
    sa.Column("uid", sa.String(36), primary_key=True),
    sa.Column("project_id", sa.String(64)),
    sa.Column("label", sa.String(100)),
    sa.Column("item_type", sa.Text),
    sa.Column("title", sa.Text),
    sa.Column("status", sa.Text),
    sa.Column("parent_uid", sa.String(36)),
    sa.Column("required_for_parent", sa.Boolean),
    sa.Column("created", sa.Text),
    sa.Column("area", sa.Text),
    sa.Column("priority", sa.Text),
    sa.Column("goal", sa.Text),
    sa.Column("completion_criteria", sa.Text),
    sa.Column("summary", sa.Text),
    sa.Column("resolution", sa.Text),
    sa.Column("location", sa.String(10)),
    sa.Column("deleted", sa.Text),
    sa.Column("position", sa.Integer),
)

item_dependencies = sa.Table(
    "item_dependencies",
    metadata,
    sa.Column("item_uid", sa.String(36), primary_key=True),
    sa.Column("position", sa.Integer, primary_key=True),
    sa.Column("depends_on_uid", sa.String(36)),
)

item_extra_fields = sa.Table(
    "item_extra_fields",
    metadata,
    sa.Column("item_uid", sa.String(36), primary_key=True),
    sa.Column("position", sa.Integer, primary_key=True),
    sa.Column("key", sa.Text),
    sa.Column("value", sa.Text),
)

item_document_names = sa.Table(
    "item_document_names",
    metadata,
    sa.Column("item_uid", sa.String(36), primary_key=True),
    sa.Column("kind", sa.String(10), primary_key=True),
    sa.Column("position", sa.Integer, primary_key=True),
    sa.Column("name", sa.Text),
)

documents = sa.Table(
    "documents",
    metadata,
    sa.Column("item_uid", sa.String(36), primary_key=True),
    sa.Column("name", sa.String(255), primary_key=True),
    sa.Column("content", sa.Text),
)

topics = sa.Table(
    "topics",
    metadata,
    sa.Column("uid", sa.String(36), primary_key=True),
    sa.Column("project_id", sa.String(64)),
    sa.Column("label", sa.String(100)),
    sa.Column("name", sa.Text),
    sa.Column("parent_uid", sa.String(36)),
    sa.Column("due_at", sa.Text),
    sa.Column("created", sa.Text),
    sa.Column("deleted", sa.Text),
)

notes = sa.Table(
    "notes",
    metadata,
    sa.Column("uid", sa.String(36), primary_key=True),
    sa.Column("project_id", sa.String(64)),
    sa.Column("label", sa.String(100)),
    sa.Column("summary", sa.Text),
    sa.Column("body", sa.Text),
    sa.Column("status", sa.String(20)),
    sa.Column("topic_uid", sa.String(36)),
    sa.Column("review_at", sa.Text),
    sa.Column("trigger_mode", sa.String(10)),
    sa.Column("created", sa.Text),
    sa.Column("updated", sa.Text),
    sa.Column("archived", sa.Boolean),
    sa.Column("deleted", sa.Text),
)

note_links = sa.Table(
    "note_links",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("note_uid", sa.String(36)),
    sa.Column("target_kind", sa.String(10)),
    sa.Column("target_project", sa.String(64)),
    sa.Column("target_label", sa.String(100)),
    sa.Column("role", sa.String(10)),
)

note_triggers = sa.Table(
    "note_triggers",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("note_uid", sa.String(36)),
    sa.Column("kind", sa.String(10)),
    sa.Column("at", sa.Text),
    sa.Column("link_id", sa.Integer),
    sa.Column("target_status", sa.Text),
    sa.Column("fired_at", sa.Text),
    sa.Column("already_met", sa.Boolean),
)

note_documents = sa.Table(
    "note_documents",
    metadata,
    sa.Column("note_uid", sa.String(36), primary_key=True),
    sa.Column("name", sa.String(255), primary_key=True),
    sa.Column("content", sa.Text),
)

note_counters = sa.Table(
    "note_counters",
    metadata,
    sa.Column("project_id", sa.String(64), primary_key=True),
    sa.Column("kind", sa.String(10), primary_key=True),
    sa.Column("last", sa.Integer),
)

note_notices = sa.Table(
    "note_notices",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("side", sa.String(10)),
    sa.Column("project_id", sa.String(64)),
    sa.Column("label", sa.String(100)),
    sa.Column("cause", sa.String(30)),
    sa.Column("counterpart_kind", sa.String(10)),
    sa.Column("counterpart_project", sa.String(64)),
    sa.Column("counterpart_label", sa.String(100)),
    sa.Column("created_at", sa.Text),
    sa.Column("decided_at", sa.Text),
    sa.Column("decision", sa.String(20)),
)

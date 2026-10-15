"""Table definitions for queries. They describe what `migrations.py` creates and never create anything."""
from __future__ import annotations

import sqlalchemy as sa

metadata = sa.MetaData()

projects = sa.Table(
    "projects", metadata,
    sa.Column("id", sa.String(64), primary_key=True),
    # NULL for rows that only hold items of a source that is not registered (tests, older databases).
    sa.Column("name", sa.Text),
    sa.Column("backend", sa.String(20)),
    sa.Column("path", sa.Text),
    sa.Column("sync_path", sa.Text),
    sa.Column("mirror_database", sa.Boolean, nullable=False, server_default=sa.false()),
    sa.Column("mirror_disabled", sa.Boolean, nullable=False, server_default=sa.false()),
    sa.Column("last_sync_at", sa.Text),
    sa.Column("synced_primary", sa.String(64)),
    sa.Column("synced_mirror", sa.String(64)),
    sa.Column("position", sa.Integer),
    sa.Column("extra", sa.Text),  # JSON object of unknown keys
)

ui_state = sa.Table(
    "ui_state", metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("data", sa.Text, nullable=False),  # JSON object
)

items = sa.Table(
    "items", metadata,
    sa.Column("uid", sa.String(36), primary_key=True),
    sa.Column("project_id", sa.String(64), nullable=False),
    sa.Column("label", sa.String(100), nullable=False),
    sa.Column("item_type", sa.Text, nullable=False),
    sa.Column("title", sa.Text, nullable=False),
    sa.Column("status", sa.Text, nullable=False),
    sa.Column("parent_uid", sa.String(36)),
    sa.Column("required_for_parent", sa.Boolean),
    sa.Column("created", sa.Text),
    sa.Column("area", sa.Text),
    sa.Column("priority", sa.Text),
    sa.Column("goal", sa.Text),
    sa.Column("completion_criteria", sa.Text),
    sa.Column("summary", sa.Text),
    sa.Column("resolution", sa.Text),
    sa.Column("location", sa.String(10), nullable=False),
    sa.Column("deleted", sa.Text),
    sa.Column("position", sa.Integer, nullable=False),
)

item_dependencies = sa.Table(
    "item_dependencies", metadata,
    sa.Column("item_uid", sa.String(36), primary_key=True),
    sa.Column("position", sa.Integer, primary_key=True),
    sa.Column("depends_on_uid", sa.String(36), nullable=False),
)

item_extra_fields = sa.Table(
    "item_extra_fields", metadata,
    sa.Column("item_uid", sa.String(36), primary_key=True),
    sa.Column("position", sa.Integer, primary_key=True),
    sa.Column("key", sa.Text, nullable=False),
    sa.Column("value", sa.Text, nullable=False),
)

item_document_names = sa.Table(
    "item_document_names", metadata,
    sa.Column("item_uid", sa.String(36), primary_key=True),
    sa.Column("kind", sa.String(10), primary_key=True),
    sa.Column("position", sa.Integer, primary_key=True),
    sa.Column("name", sa.Text, nullable=False),
)

documents = sa.Table(
    "documents", metadata,
    sa.Column("item_uid", sa.String(36), primary_key=True),
    sa.Column("name", sa.String(255), primary_key=True),
    sa.Column("content", sa.Text, nullable=False),
)

topics = sa.Table(
    "topics", metadata,
    sa.Column("uid", sa.String(36), primary_key=True),
    sa.Column("project_id", sa.String(64), nullable=False),
    sa.Column("label", sa.String(100), nullable=False),
    sa.Column("name", sa.Text, nullable=False),
    sa.Column("parent_uid", sa.String(36)),
    sa.Column("due_at", sa.Text),
    sa.Column("created", sa.Text, nullable=False),
    sa.Column("deleted", sa.Text),
)

notes = sa.Table(
    "notes", metadata,
    sa.Column("uid", sa.String(36), primary_key=True),
    sa.Column("project_id", sa.String(64), nullable=False),
    sa.Column("label", sa.String(100), nullable=False),
    sa.Column("summary", sa.Text, nullable=False),
    sa.Column("body", sa.Text),
    sa.Column("status", sa.String(20), nullable=False),
    sa.Column("topic_uid", sa.String(36)),
    sa.Column("review_at", sa.Text),
    sa.Column("trigger_mode", sa.String(10), nullable=False),
    sa.Column("created", sa.Text, nullable=False),
    sa.Column("updated", sa.Text, nullable=False),
    sa.Column("archived", sa.Boolean, nullable=False, server_default=sa.false()),
    sa.Column("deleted", sa.Text),
)

note_links = sa.Table(
    "note_links", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("note_uid", sa.String(36), nullable=False),
    sa.Column("target_kind", sa.String(10), nullable=False),
    sa.Column("target_project", sa.String(64), nullable=False),
    sa.Column("target_label", sa.String(100), nullable=False),
    sa.Column("role", sa.String(10), nullable=False),
)

note_triggers = sa.Table(
    "note_triggers", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("note_uid", sa.String(36), nullable=False),
    sa.Column("kind", sa.String(10), nullable=False),
    sa.Column("at", sa.Text),
    sa.Column("link_id", sa.Integer),
    sa.Column("target_status", sa.Text),
    sa.Column("fired_at", sa.Text),
    sa.Column("already_met", sa.Boolean, nullable=False, server_default=sa.false()),
)

note_documents = sa.Table(
    "note_documents", metadata,
    sa.Column("note_uid", sa.String(36), primary_key=True),
    sa.Column("name", sa.String(255), primary_key=True),
    sa.Column("content", sa.Text, nullable=False),
)

note_counters = sa.Table(
    "note_counters", metadata,
    sa.Column("project_id", sa.String(64), primary_key=True),
    sa.Column("kind", sa.String(10), primary_key=True),
    sa.Column("last", sa.Integer, nullable=False),
)

note_notices = sa.Table(
    "note_notices", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("side", sa.String(10), nullable=False),
    sa.Column("project_id", sa.String(64), nullable=False),
    sa.Column("label", sa.String(100), nullable=False),
    sa.Column("cause", sa.String(30), nullable=False),
    sa.Column("counterpart_kind", sa.String(10), nullable=False),
    sa.Column("counterpart_project", sa.String(64), nullable=False),
    sa.Column("counterpart_label", sa.String(100), nullable=False),
    sa.Column("created_at", sa.Text, nullable=False),
    sa.Column("decided_at", sa.Text),
    sa.Column("decision", sa.String(20)),
)

sync_entries = sa.Table(
    "sync_entries", metadata,
    sa.Column("project_id", sa.String(64), primary_key=True),
    sa.Column("folder", sa.Text, primary_key=True),
    sa.Column("kind", sa.String(10), primary_key=True),
    sa.Column("label", sa.String(100), primary_key=True),
    sa.Column("name", sa.String(255), primary_key=True),
    sa.Column("database_version", sa.String(64), nullable=False),
    sa.Column("markdown_version", sa.String(64), nullable=False),
)

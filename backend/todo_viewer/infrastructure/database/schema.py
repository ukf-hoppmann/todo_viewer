"""Table definitions for queries. They describe what `migrations.py` creates and never create anything."""
from __future__ import annotations

import sqlalchemy as sa

metadata = sa.MetaData()

projects = sa.Table("projects", metadata, sa.Column("id", sa.String(64), primary_key=True))

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

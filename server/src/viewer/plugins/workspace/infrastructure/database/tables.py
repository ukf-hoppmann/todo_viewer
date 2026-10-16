"""SQLAlchemy-Beschreibung der Tabellen, die `update_with_revision` und die Abfragen brauchen."""

from __future__ import annotations

from sqlalchemy import Column, Integer, MetaData, String, Table

metadata = MetaData()

projects = Table(
    "workspace_projects",
    metadata,
    Column("uid", String, primary_key=True),
    Column("name", String),
    Column("mirror_folder", String),
    Column("mirror_enabled", Integer),
    Column("auto_sync", Integer),
    Column("sync_direction", String),
    Column("position", Integer),
    Column("revision", Integer),
    Column("created_at", String),
    Column("deleted_at", String),
)

elements = Table(
    "workspace_elements",
    metadata,
    Column("uid", String, primary_key=True),
    Column("project_uid", String),
    Column("kind", String),
    Column("label", String),
    Column("revision", Integer),
    Column("created_at", String),
    Column("updated_at", String),
    Column("deleted_at", String),
)

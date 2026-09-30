"""Versioned, forward-only schema migrations. Each version is a list of SQL statements run in one transaction."""
from __future__ import annotations

import sqlalchemy as sa

# Foreign keys between items are checked at commit, so an item and the items referring to it can be
# written or deleted in one transaction in any order.
_DEFERRED = "DEFERRABLE INITIALLY DEFERRED"

MIGRATIONS: dict[int, list[str]] = {
    1: [
        "CREATE TABLE projects (id VARCHAR(64) PRIMARY KEY)",
        f"""CREATE TABLE items (
            uid VARCHAR(36) PRIMARY KEY,
            project_id VARCHAR(64) NOT NULL REFERENCES projects (id),
            label VARCHAR(100) NOT NULL,
            item_type TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            parent_uid VARCHAR(36) REFERENCES items (uid) {_DEFERRED},
            required_for_parent BOOLEAN,
            created TEXT,
            area TEXT,
            priority TEXT,
            goal TEXT,
            completion_criteria TEXT,
            summary TEXT,
            resolution TEXT,
            location VARCHAR(10) NOT NULL,
            deleted TEXT,
            position INTEGER NOT NULL,
            UNIQUE (project_id, label)
        )""",
        f"""CREATE TABLE item_dependencies (
            item_uid VARCHAR(36) NOT NULL REFERENCES items (uid) ON DELETE CASCADE {_DEFERRED},
            position INTEGER NOT NULL,
            depends_on_uid VARCHAR(36) NOT NULL REFERENCES items (uid) {_DEFERRED},
            PRIMARY KEY (item_uid, position)
        )""",
        f"""CREATE TABLE item_extra_fields (
            item_uid VARCHAR(36) NOT NULL REFERENCES items (uid) ON DELETE CASCADE {_DEFERRED},
            position INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY (item_uid, position)
        )""",
        f"""CREATE TABLE item_document_names (
            item_uid VARCHAR(36) NOT NULL REFERENCES items (uid) ON DELETE CASCADE {_DEFERRED},
            kind VARCHAR(10) NOT NULL,
            position INTEGER NOT NULL,
            name TEXT NOT NULL,
            PRIMARY KEY (item_uid, kind, position)
        )""",
        f"""CREATE TABLE documents (
            item_uid VARCHAR(36) NOT NULL REFERENCES items (uid) ON DELETE CASCADE {_DEFERRED},
            name VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            PRIMARY KEY (item_uid, name)
        )""",
    ],
    # Projects move from config.json into the database; rows without a name only hold items.
    2: [
        "ALTER TABLE projects ADD COLUMN name TEXT",
        "ALTER TABLE projects ADD COLUMN backend VARCHAR(20)",
        "ALTER TABLE projects ADD COLUMN path TEXT",
        "ALTER TABLE projects ADD COLUMN sync_path TEXT",
        "ALTER TABLE projects ADD COLUMN position INTEGER",
        "ALTER TABLE projects ADD COLUMN extra TEXT",
        "CREATE TABLE ui_state (id INTEGER PRIMARY KEY, data TEXT NOT NULL)",
    ],
    # Whether the database keeps a mirror of a markdown project; existing projects keep none.
    3: [
        "ALTER TABLE projects ADD COLUMN mirror_database BOOLEAN NOT NULL DEFAULT 0",
    ],
    # The state of both sides right after the last sync, to tell later which side changed.
    4: [
        "ALTER TABLE projects ADD COLUMN last_sync_at TEXT",
        "ALTER TABLE projects ADD COLUMN synced_primary VARCHAR(64)",
        "ALTER TABLE projects ADD COLUMN synced_mirror VARCHAR(64)",
    ],
    # A database project can keep its mirror folder while the mirror is off; existing projects keep it switched on.
    5: [
        "ALTER TABLE projects ADD COLUMN mirror_disabled BOOLEAN NOT NULL DEFAULT 0",
    ],
}

CURRENT_VERSION = max(MIGRATIONS)


def migrate(conn: sa.Connection) -> None:
    """Brings the schema to CURRENT_VERSION; runs inside the caller's transaction."""
    if not sa.inspect(conn).has_table("schema_version"):
        conn.execute(sa.text("CREATE TABLE schema_version (version INTEGER NOT NULL)"))
        conn.execute(sa.text("INSERT INTO schema_version (version) VALUES (0)"))
    version: int = conn.execute(sa.text("SELECT version FROM schema_version")).scalar_one()
    for number in sorted(n for n in MIGRATIONS if n > version):
        for statement in MIGRATIONS[number]:
            conn.execute(sa.text(statement))
        conn.execute(sa.text("UPDATE schema_version SET version = :v"), {"v": number})

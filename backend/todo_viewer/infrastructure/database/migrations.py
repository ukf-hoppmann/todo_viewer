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
    # Topics, notes, links, and triggers. Links hold project plus label of their target, not a key.
    6: [
        f"""CREATE TABLE topics (
            uid VARCHAR(36) PRIMARY KEY,
            project_id VARCHAR(64) NOT NULL REFERENCES projects (id),
            label VARCHAR(100) NOT NULL,
            name TEXT NOT NULL,
            parent_uid VARCHAR(36) REFERENCES topics (uid) {_DEFERRED},
            due_at TEXT,
            created TEXT NOT NULL,
            deleted TEXT,
            UNIQUE (project_id, label)
        )""",
        f"""CREATE TABLE notes (
            uid VARCHAR(36) PRIMARY KEY,
            project_id VARCHAR(64) NOT NULL REFERENCES projects (id),
            label VARCHAR(100) NOT NULL,
            summary TEXT NOT NULL,
            body TEXT,
            status VARCHAR(20) NOT NULL,
            topic_uid VARCHAR(36) REFERENCES topics (uid) {_DEFERRED},
            review_at TEXT,
            trigger_mode VARCHAR(10) NOT NULL,
            created TEXT NOT NULL,
            updated TEXT NOT NULL,
            archived BOOLEAN NOT NULL DEFAULT 0,
            deleted TEXT,
            UNIQUE (project_id, label)
        )""",
        f"""CREATE TABLE note_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_uid VARCHAR(36) NOT NULL REFERENCES notes (uid) ON DELETE CASCADE {_DEFERRED},
            target_kind VARCHAR(10) NOT NULL,
            target_project VARCHAR(64) NOT NULL,
            target_label VARCHAR(100) NOT NULL,
            role VARCHAR(10) NOT NULL
        )""",
        "CREATE INDEX note_links_target ON note_links (target_kind, target_project, target_label)",
        f"""CREATE TABLE note_triggers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_uid VARCHAR(36) NOT NULL REFERENCES notes (uid) ON DELETE CASCADE {_DEFERRED},
            kind VARCHAR(10) NOT NULL,
            at TEXT,
            link_id INTEGER REFERENCES note_links (id) ON DELETE SET NULL {_DEFERRED},
            target_status TEXT,
            fired_at TEXT,
            already_met BOOLEAN NOT NULL DEFAULT 0
        )""",
        f"""CREATE TABLE note_documents (
            note_uid VARCHAR(36) NOT NULL REFERENCES notes (uid) ON DELETE CASCADE {_DEFERRED},
            name VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            PRIMARY KEY (note_uid, name)
        )""",
        # The last number given per project and kind; numbers are never reused.
        """CREATE TABLE note_counters (
            project_id VARCHAR(64) NOT NULL,
            kind VARCHAR(10) NOT NULL,
            last INTEGER NOT NULL,
            PRIMARY KEY (project_id, kind)
        )""",
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

"""Database adapter: the central database for projects with `backend = "database"`."""
from __future__ import annotations

from .backup import DatabaseRawBackup
from .config_import import LegacyConfigImport
from .documents import DatabaseDocumentStore
from .engine import Database
from .file_backup import SqliteFileBackup
from .notes import DatabaseNoteDocumentStore, DatabaseNoteRepository
from .repository import DatabaseBacklogRepository
from .sources import DatabaseSourceRepository
from .sync_state import DatabaseSyncStateStore
from .ui_state import DatabaseUiStateStore

__all__ = ["Database", "DatabaseBacklogRepository", "DatabaseDocumentStore", "DatabaseNoteDocumentStore",
           "DatabaseNoteRepository", "DatabaseRawBackup", "DatabaseSourceRepository", "DatabaseSyncStateStore",
           "DatabaseUiStateStore", "LegacyConfigImport", "SqliteFileBackup"]

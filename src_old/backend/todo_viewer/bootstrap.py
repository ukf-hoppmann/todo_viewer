"""Composition root: the only place that knows which adapter implements which port."""
from __future__ import annotations

import os
import platform
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import structlog

from todo_viewer.application.container import Container
from todo_viewer.application.services import (
    AutoSyncService,
    BacklogOverviewService,
    BackupService,
    ConversionService,
    DocumentService,
    FolderBrowseService,
    ItemService,
    NoteDocumentService,
    NoteIndexService,
    NoteService,
    NotesSettingsService,
    NotesSync,
    RetypeService,
    SourceLookup,
    SourceService,
    StorageService,
    SyncService,
    SyncStatusService,
    TopicService,
    TrashService,
    UiStateService,
)
from todo_viewer.domain.creation import ItemFactory
from todo_viewer.domain.editing import EditPlanner
from todo_viewer.domain.lifecycle import LifecycleRules
from todo_viewer.domain.retype import RetypePlanner
from todo_viewer.domain.trash import TrashPlanner
from todo_viewer.infrastructure.config import JsonFile, JsonNotesSettingsStore, storage_url
from todo_viewer.infrastructure.database import (
    Database,
    DatabaseBacklogRepository,
    DatabaseDocumentStore,
    DatabaseNoteDocumentStore,
    DatabaseNoteRepository,
    DatabaseRawBackup,
    DatabaseSourceRepository,
    DatabaseSyncStateStore,
    DatabaseUiStateStore,
    LegacyConfigImport,
    SqliteFileBackup,
)
from todo_viewer.infrastructure.filesystem import GitProjectNameSuggester, LocalFolderBrowser, browse_start_from
from todo_viewer.infrastructure.log_setup import configure_logging
from todo_viewer.infrastructure.markdown import (
    KeyedLocks,
    MarkdownMergeMarkers,
    MarkdownRawBackup,
    build_markdown_documents,
    build_markdown_repository,
)
from todo_viewer.infrastructure.markdown.layout import LayoutFactory, SourcePathResolver
from todo_viewer.infrastructure.notes_files import FilesNotesMirror
from todo_viewer.infrastructure.routing import RoutingBacklogRepository, RoutingDocumentStore, RoutingRawBackup

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    config_dir: Path
    frontend_dir: Path
    browse_start: str | None
    log_file: Path | None = None
    log_level: str = "INFO"
    # Seconds between two checks of the automatic sync; 0 = no timer. It runs only while a project has the switch on.
    auto_sync_interval: float = 0.0

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            base_dir=PROJECT_ROOT,
            config_dir=Path(os.environ.get("CONFIG_DIR", PROJECT_ROOT / "configs")),
            frontend_dir=Path(os.environ.get("FRONTEND_DIR", PROJECT_ROOT / "src_old" / "web" / "dist")),
            browse_start=os.environ.get("BROWSE_START"),
            log_file=Path(os.environ["LOG_FILE"]) if os.environ.get("LOG_FILE") else None,
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
            auto_sync_interval=float(os.environ.get("AUTO_SYNC_INTERVAL", "30")),
        )


def start_logging(settings: Settings) -> None:
    """Configures logging and records the settings the server runs with."""
    configure_logging(settings.log_level, settings.log_file)
    structlog.get_logger(__name__).info(
        "startup", api="2", python=platform.python_version(), config_dir=str(settings.config_dir),
        frontend_dir=str(settings.frontend_dir), browse_start=settings.browse_start,
        auto_sync_interval=settings.auto_sync_interval,
        log_file=str(settings.log_file) if settings.log_file else None, log_level=settings.log_level.upper())


def build_container(settings: Settings, today: Callable[[], date] = date.today) -> Container:
    resolver = SourcePathResolver(settings.base_dir)
    locks = KeyedLocks()  # shared: backlog files and documents of a folder are written under one lock
    config = JsonFile(settings.config_dir / "config.json")
    # Holds the projects of every backend; created and migrated on first use.
    url = storage_url(config, f"sqlite:///{settings.config_dir / 'todo.db'}")
    # A copy of the database file goes into the same folder as the backups made when the primary source is switched.
    file_backup = SqliteFileBackup.for_url(url, settings.config_dir / "backups")
    database = Database(url, before_migration=(lambda: file_backup.create("migration")) if file_backup else None)
    # Earlier versions kept sources and UI state in JSON files; they are taken over on first access.
    legacy = LegacyConfigImport(database, config, JsonFile(settings.config_dir / "ui_state.json"))
    backlogs = RoutingBacklogRepository({"markdown": build_markdown_repository(settings.base_dir, locks),
                                         "database": DatabaseBacklogRepository(database)})
    planner, rules = EditPlanner(), LifecycleRules()
    documents = RoutingDocumentStore({"markdown": build_markdown_documents(settings.base_dir, locks),
                                      "database": DatabaseDocumentStore(database)})
    source_repo = DatabaseSourceRepository(database, legacy.sources)
    lookup = SourceLookup(source_repo)
    note_repo = DatabaseNoteRepository(database)
    note_settings = NotesSettingsService(JsonNotesSettingsStore(config))
    notes = NoteService(note_repo, source_repo, backlogs, note_settings.current)
    markers = MarkdownMergeMarkers(LayoutFactory(resolver))
    note_document_store = DatabaseNoteDocumentStore(database)
    notes_mirror = FilesNotesMirror(settings.base_dir)  # the notes folder of the markdown side: always a mirror
    sync = SyncService(backlogs, documents, notes, db_backup=file_backup, states=DatabaseSyncStateStore(database),
                       markers=markers, notes_sync=NotesSync(note_repo, note_document_store, notes_mirror),
                       notes_mirror=notes_mirror)
    raw_backup = RoutingRawBackup({"markdown": MarkdownRawBackup(LayoutFactory(resolver)),
                                   "database": DatabaseRawBackup()})
    backup = BackupService(raw_backup, sync, settings.config_dir / "backups")
    items = ItemService(backlogs, planner, rules, ItemFactory(planner), today, notes)
    item_documents = DocumentService(backlogs, documents, planner, rules, today)
    note_documents = NoteDocumentService(note_repo, note_document_store, today)

    sync_status = SyncStatusService(sync, source_repo)
    return Container(
        overview=BacklogOverviewService(source_repo, backlogs),
        items=items,
        trash=TrashService(backlogs, documents, TrashPlanner(rules), today, notes),
        notes=notes,
        topics=TopicService(note_repo, source_repo, note_settings.current),
        notes_settings=note_settings,
        note_index=NoteIndexService(notes, note_repo, source_repo),
        note_documents=note_documents,
        retype=RetypeService(backlogs, documents, RetypePlanner(), rules, note_repo, notes),
        conversion=ConversionService(items, item_documents, notes, note_documents, backlogs, source_repo, today),
        sources=SourceService(source_repo, backlogs, GitProjectNameSuggester(resolver), sync, backup),
        source_lookup=lookup,
        documents=item_documents,
        sync=sync,
        sync_status=sync_status,
        autosync=AutoSyncService(sync, sync_status, source_repo, settings.auto_sync_interval),
        folders=FolderBrowseService(LocalFolderBrowser(browse_start_from(settings.browse_start), resolver)),
        storage=StorageService(database),
        ui_state=UiStateService(DatabaseUiStateStore(database, legacy.ui_state)),
    )

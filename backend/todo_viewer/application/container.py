"""The set of use cases the outer layers (e.g. the HTTP API) can call."""
from __future__ import annotations

from dataclasses import dataclass

from .services import (
    BacklogOverviewService,
    DocumentService,
    FolderBrowseService,
    ItemService,
    NoteDocumentService,
    NoteIndexService,
    NoteService,
    NotesSettingsService,
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


@dataclass(frozen=True)
class Container:
    overview: BacklogOverviewService
    items: ItemService
    trash: TrashService
    notes: NoteService
    topics: TopicService
    note_documents: NoteDocumentService
    notes_settings: NotesSettingsService
    note_index: NoteIndexService
    retype: RetypeService
    sources: SourceService
    source_lookup: SourceLookup
    documents: DocumentService
    sync: SyncService
    sync_status: SyncStatusService
    folders: FolderBrowseService
    storage: StorageService
    ui_state: UiStateService

"""FastAPI dependencies handing the routers their services from the container."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from todo_viewer.application.container import Container
from todo_viewer.application.services import (
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


def container(request: Request) -> Container:
    c: Container = request.app.state.container
    return c


ContainerDep = Annotated[Container, Depends(container)]


def _overview(c: ContainerDep) -> BacklogOverviewService:
    return c.overview


def _items(c: ContainerDep) -> ItemService:
    return c.items


def _trash(c: ContainerDep) -> TrashService:
    return c.trash


def _notes(c: ContainerDep) -> NoteService:
    return c.notes


def _note_documents(c: ContainerDep) -> NoteDocumentService:
    return c.note_documents


def _notes_settings(c: ContainerDep) -> NotesSettingsService:
    return c.notes_settings


def _note_index(c: ContainerDep) -> NoteIndexService:
    return c.note_index


def _topics(c: ContainerDep) -> TopicService:
    return c.topics


def _retype(c: ContainerDep) -> RetypeService:
    return c.retype


def _sources(c: ContainerDep) -> SourceService:
    return c.sources


def _source_lookup(c: ContainerDep) -> SourceLookup:
    return c.source_lookup


def _documents(c: ContainerDep) -> DocumentService:
    return c.documents


def _sync(c: ContainerDep) -> SyncService:
    return c.sync


def _sync_status(c: ContainerDep) -> SyncStatusService:
    return c.sync_status


def _folders(c: ContainerDep) -> FolderBrowseService:
    return c.folders


def _storage(c: ContainerDep) -> StorageService:
    return c.storage


def _ui_state(c: ContainerDep) -> UiStateService:
    return c.ui_state


Overview = Annotated[BacklogOverviewService, Depends(_overview)]
Items = Annotated[ItemService, Depends(_items)]
Trash = Annotated[TrashService, Depends(_trash)]
Notes = Annotated[NoteService, Depends(_notes)]
NoteDocuments = Annotated[NoteDocumentService, Depends(_note_documents)]
NotesSettings = Annotated[NotesSettingsService, Depends(_notes_settings)]
NoteIndex = Annotated[NoteIndexService, Depends(_note_index)]
Topics = Annotated[TopicService, Depends(_topics)]
Retype = Annotated[RetypeService, Depends(_retype)]
Sources = Annotated[SourceService, Depends(_sources)]
Lookup = Annotated[SourceLookup, Depends(_source_lookup)]
Documents = Annotated[DocumentService, Depends(_documents)]
Sync = Annotated[SyncService, Depends(_sync)]
SyncStatus = Annotated[SyncStatusService, Depends(_sync_status)]
Folders = Annotated[FolderBrowseService, Depends(_folders)]
Storage = Annotated[StorageService, Depends(_storage)]
UiState = Annotated[UiStateService, Depends(_ui_state)]

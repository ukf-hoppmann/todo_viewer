"""The set of use cases the outer layers (e.g. the HTTP API) can call."""
from __future__ import annotations

from dataclasses import dataclass

from .services import (
    BacklogOverviewService,
    DocumentService,
    FolderBrowseService,
    ItemEditService,
    SourceLookup,
    SourceService,
    UiStateService,
)


@dataclass(frozen=True)
class Container:
    overview: BacklogOverviewService
    item_edits: ItemEditService
    sources: SourceService
    source_lookup: SourceLookup
    documents: DocumentService
    folders: FolderBrowseService
    ui_state: UiStateService

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
    SourceLookup,
    SourceService,
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


def _sources(c: ContainerDep) -> SourceService:
    return c.sources


def _source_lookup(c: ContainerDep) -> SourceLookup:
    return c.source_lookup


def _documents(c: ContainerDep) -> DocumentService:
    return c.documents


def _folders(c: ContainerDep) -> FolderBrowseService:
    return c.folders


def _ui_state(c: ContainerDep) -> UiStateService:
    return c.ui_state


Overview = Annotated[BacklogOverviewService, Depends(_overview)]
Items = Annotated[ItemService, Depends(_items)]
Sources = Annotated[SourceService, Depends(_sources)]
Lookup = Annotated[SourceLookup, Depends(_source_lookup)]
Documents = Annotated[DocumentService, Depends(_documents)]
Folders = Annotated[FolderBrowseService, Depends(_folders)]
UiState = Annotated[UiStateService, Depends(_ui_state)]

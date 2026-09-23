"""Documents, folder browser and UI state."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body

from ..dependencies import Documents, Folders, UiState
from ..schemas import DocumentOut, FolderListingOut, Ok

router = APIRouter(prefix="/api")


@router.get("/itemfile", response_model=DocumentOut, tags=["documents"])
def item_file(source: int, documents: Documents, path: str = "") -> DocumentOut:
    """A notes/spec markdown file; only files inside the backlog folder are served."""
    return DocumentOut(path=path, content=documents.read(source, path))


@router.get("/browse", response_model=FolderListingOut, tags=["sources"])
def browse(folders: Folders, path: str | None = None) -> FolderListingOut:
    """Subfolders of a folder for the backlog folder picker."""
    return FolderListingOut.of(folders.browse(path))


@router.get("/state", tags=["ui-state"])
def get_state(state: UiState) -> dict[str, Any]:
    return state.get()


@router.post("/state", response_model=Ok, tags=["ui-state"])
def save_state(state: UiState, body: Annotated[dict[str, Any], Body()]) -> Ok:
    state.save(body)
    return Ok()

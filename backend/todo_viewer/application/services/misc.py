"""Small pass-through use cases: documents, folder browsing, UI state."""
from __future__ import annotations

from typing import Any

from ..ports import DocumentStore, FolderBrowser, FolderListing, UiStateStore
from .sources import SourceLookup


class DocumentService:
    def __init__(self, lookup: SourceLookup, documents: DocumentStore):
        self._lookup = lookup
        self._documents = documents

    def read(self, source_index: int, relative_path: str) -> str:
        return self._documents.read(self._lookup.get(source_index), relative_path)


class FolderBrowseService:
    def __init__(self, browser: FolderBrowser):
        self._browser = browser

    def browse(self, path: str | None) -> FolderListing:
        return self._browser.browse((path or "").strip() or None)


class UiStateService:
    def __init__(self, store: UiStateStore):
        self._store = store

    def get(self) -> dict[str, Any]:
        return self._store.load()

    def save(self, state: dict[str, Any]) -> None:
        self._store.save(state)

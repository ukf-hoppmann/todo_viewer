"""Small pass-through use cases: folder browsing, UI state."""
from __future__ import annotations

from typing import Any

from ..ports import FolderBrowser, FolderListing, UiStateStore


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

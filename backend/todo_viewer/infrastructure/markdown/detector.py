from __future__ import annotations

from todo_viewer.domain.item import ItemFormat, Location

from .syntax import BACKLOG_MARKER_RE, ENTRY_HEADER_RE


class FormatDetector:
    """Decides which parser a file needs; None means the file holds no items."""

    def detect(self, text: str, location: Location) -> ItemFormat | None:
        if ENTRY_HEADER_RE.search(text) and BACKLOG_MARKER_RE.search(text):
            return ItemFormat.BACKLOG_V2
        if location is Location.ARCHIVE:
            # An archive never falls back to checkbox parsing ("No entries." etc.).
            return None
        return ItemFormat.CHECKBOX

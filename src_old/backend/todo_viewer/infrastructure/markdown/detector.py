from __future__ import annotations

from .syntax import BACKLOG_MARKER_RE


class FormatDetector:
    """Only files that declare the structured backlog format hold items."""

    def is_backlog(self, text: str) -> bool:
        return BACKLOG_MARKER_RE.search(text) is not None

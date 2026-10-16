"""Finds backlog files that contain Git merge markers (an unfinished merge or pull)."""
from __future__ import annotations

import re
from pathlib import Path

from todo_viewer.domain.item import Location
from todo_viewer.domain.source import Source

from .layout import LayoutFactory

_START = re.compile(r"^<{7}(\s|$)", re.MULTILINE)
_END = re.compile(r"^>{7}(\s|$)", re.MULTILINE)


class MarkdownMergeMarkers:
    def __init__(self, layouts: LayoutFactory):
        self._layouts = layouts

    def files_with_markers(self, source: Source) -> list[str]:
        """The files of the backlog folder (relative paths) that have a start and an end marker of a merge
        conflict at the beginning of lines. Files that are missing or not text are not reported."""
        layout = self._layouts.for_source(source)
        files = [layout.file(location) for location in Location]
        if layout.items_folder().is_dir():
            files += sorted(p for p in layout.items_folder().rglob("*") if p.is_file())
        return [path.relative_to(layout.folder).as_posix() for path in files if _has_markers(path)]


def _has_markers(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return bool(_START.search(text) and _END.search(text))

"""Byte-exact copy of a markdown backlog (TODO.md, archive.md, items/), e.g. before the primary source is switched."""
from __future__ import annotations

import filecmp
import shutil
from pathlib import Path

from todo_viewer.domain.item import Location
from todo_viewer.domain.source import Source

from .layout import LayoutFactory


class MarkdownRawBackup:
    def __init__(self, layouts: LayoutFactory):
        self._layouts = layouts

    def copy(self, source: Source, target: str) -> bool:
        """Copies the backlog files of `source` into the folder `target` and checks every copy against its original.

        Files that do not belong to the backlog are left out. Raises OSError if anything cannot be written or a copy
        differs from its original.
        """
        layout = self._layouts.for_source(source)
        folder = Path(target)
        folder.mkdir(parents=True)
        for location in Location:
            original = layout.file(location)
            if original.is_file():
                self._copy_file(original, folder / original.name)
        if layout.items_folder().is_dir():
            for original in sorted(p for p in layout.items_folder().rglob("*") if p.is_file()):
                self._copy_file(original, folder / "items" / original.relative_to(layout.items_folder()))
        return True

    @staticmethod
    def _copy_file(original: Path, copy: Path) -> None:
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, copy)
        if not filecmp.cmp(original, copy, shallow=False):
            raise OSError(f"The copy of {original.name} differs from the original.")

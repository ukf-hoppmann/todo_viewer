"""Die Golden-Files des Mindmap-Spiegels (`tests/fixtures/mirror-mindmap/`)."""

from __future__ import annotations

from pathlib import Path

from mirror_files import read_folder
from viewer.core.domain.files import FileSet

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "mirror-mindmap"

__all__ = ["FIXTURES", "FileSet", "read_folder"]

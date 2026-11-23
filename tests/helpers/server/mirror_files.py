"""Ordner mit Dateien als `FileSet` lesen (für die Golden-Tests der Codecs)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from viewer.core.domain.files import FileEntry, FileSet

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "mirror-v2"  # Format 2: Alarme, Memos, v2-Lesen
BACKLOG_FIXTURES = FIXTURES.parent / "mirror-v3"  # Format 3: Backlog (`TODO.md`, `archive.md`, `items/`)


def read_folder(folder: Path) -> FileSet:
    """Alle Dateien des Ordners (relative POSIX-Pfade) als `FileSet`; Text mit LF."""
    files: dict[str, FileEntry] = {}
    for path in sorted(folder.rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            relative = path.relative_to(folder).as_posix()
            files[relative] = FileEntry(relative, data.decode("utf-8"), hashlib.sha256(data).hexdigest())
    return FileSet(files)

from __future__ import annotations

import dataclasses
import re
import shutil
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from todo_viewer.domain.errors import BackupFailedError, DomainError
from todo_viewer.domain.source import Source
from todo_viewer.domain.sync import SyncDirection

from ..ports import RawBackup
from .sync import SyncService


class BackupService:
    """Saves the current primary source of a project as a markdown backlog folder before the primary source is switched.

    The backlog folder is `<folder>/<project>_<id8>/<YYYYMMDD-HHMMSS>/`. A backend that keeps files has them copied
    byte for byte; otherwise the data is exported like a sync into a folder and checked against the original.
    """

    def __init__(self, raw: RawBackup, sync: SyncService, folder: Path, clock: Callable[[], datetime] = datetime.now):
        self._raw = raw
        self._sync = sync
        self._folder = folder
        self._clock = clock

    def create(self, source: Source) -> str:
        """Returns the folder of the backup; raises BackupFailedError (and leaves nothing behind) if it fails."""
        target = self._unused(self._folder / f"{_slug(source.project)}_{source.id[:8]}"
                              / self._clock().strftime("%Y%m%d-%H%M%S"))
        try:
            if not self._raw.copy(source, str(target)):
                self._export(source, target)
        except (OSError, DomainError) as error:
            shutil.rmtree(target, ignore_errors=True)
            raise BackupFailedError(str(error)) from error
        return str(target)

    def _export(self, source: Source, target: Path) -> None:
        exported = dataclasses.replace(source, sync_path=str(target))
        preview = self._sync.preview(exported, SyncDirection.TO_MD)
        self._sync.run(exported, SyncDirection.TO_MD, preview.token, delete_missing=False, language="en")
        if not self._sync.in_sync(exported, SyncDirection.TO_MD):
            raise OSError("The exported backlog differs from the original.")

    @staticmethod
    def _unused(target: Path) -> Path:
        """`target`, or `target-2`, `target-3`, … if a backup of the same second exists."""
        candidate, number = target, 1
        while candidate.exists():
            number += 1
            candidate = target.with_name(f"{target.name}-{number}")
        return candidate


def _slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-") or "project"

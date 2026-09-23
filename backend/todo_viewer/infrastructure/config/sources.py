"""Sources stored in config.json: {"sources": [{"project": ..., "path": ...}, ...]}."""
from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from todo_viewer.domain.errors import ConfigMissingError
from todo_viewer.domain.source import Source

from .json_file import JsonFile

LEGACY_FILE_SUFFIXES = {".md", ".markdown", ".txt"}


class LegacySourceMigrator:
    """Older entries pointed to the TODO file itself; sources are folders now."""

    def migrate(self, raw: dict[str, Any]) -> bool:
        path = Path(raw.get("path", ""))
        if path.suffix.lower() in LEGACY_FILE_SUFFIXES:
            raw["path"] = str(path.parent)
            return True
        return False


class JsonSourceRepository:
    def __init__(self, file: JsonFile, migrator: LegacySourceMigrator):
        self._file = file
        self._migrator = migrator
        self._lock = threading.RLock()

    def all(self) -> list[Source]:
        with self._lock:
            if not self._file.exists():
                raise ConfigMissingError()
            return [self._to_source(raw) for raw in self._read()["sources"]]

    @contextmanager
    def edit(self) -> Iterator[list[Source]]:
        with self._lock:
            config = self._read() if self._file.exists() else {"sources": []}
            sources = [self._to_source(raw) for raw in config["sources"]]
            yield sources
            config["sources"] = [self._to_raw(s) for s in sources]
            self._file.write(config)

    def _read(self) -> dict[str, Any]:
        """Reads the config (keeping unknown top-level keys) and persists migrations."""
        config: dict[str, Any] = self._file.read()
        raws = config.setdefault("sources", [])
        if any([self._migrator.migrate(raw) for raw in raws]):
            self._file.write(config)
        return config

    @staticmethod
    def _to_source(raw: dict[str, Any]) -> Source:
        extra = {k: v for k, v in raw.items() if k not in ("project", "path")}
        return Source(project=raw["project"], path=raw["path"], extra=extra)

    @staticmethod
    def _to_raw(source: Source) -> dict[str, Any]:
        return {"project": source.project, "path": source.path, **source.extra}

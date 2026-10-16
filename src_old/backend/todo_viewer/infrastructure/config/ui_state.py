from __future__ import annotations

import json
from typing import Any

import structlog

from .json_file import JsonFile

log = structlog.get_logger(__name__)


class JsonUiStateStore:
    """UI state (filters, view, language) in ui_state.json; unreadable state counts as empty."""

    def __init__(self, file: JsonFile):
        self._file = file

    def load(self) -> dict[str, Any]:
        if not self._file.exists():
            return {}
        try:
            data = self._file.read()
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("ui_state_unreadable", path=str(self._file.path), error=f"{type(exc).__name__}: {exc}")
            return {}
        return data if isinstance(data, dict) else {}

    def save(self, state: dict[str, Any]) -> None:
        self._file.write(state)

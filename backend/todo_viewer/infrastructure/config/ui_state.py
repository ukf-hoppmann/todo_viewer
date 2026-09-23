from __future__ import annotations

import json
from typing import Any

from .json_file import JsonFile


class JsonUiStateStore:
    """UI state (filters, view, language) in ui_state.json; unreadable state counts as empty."""

    def __init__(self, file: JsonFile):
        self._file = file

    def load(self) -> dict[str, Any]:
        if not self._file.exists():
            return {}
        try:
            data = self._file.read()
        except (json.JSONDecodeError, OSError):
            return {}
        return data if isinstance(data, dict) else {}

    def save(self, state: dict[str, Any]) -> None:
        self._file.write(state)

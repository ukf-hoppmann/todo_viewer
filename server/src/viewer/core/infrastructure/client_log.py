"""Schreibt Einträge des Browsers über structlog ins viewer.log (Logger `viewer.client`)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import structlog

_METHODS = {"debug": "debug", "info": "info", "warn": "warning", "error": "error"}


class StructlogClientLog:
    def __init__(self) -> None:
        self._log = structlog.get_logger("viewer.client")

    def write(self, level: str, message: str, fields: Mapping[str, Any]) -> None:
        getattr(self._log, _METHODS[level])(message, **fields)

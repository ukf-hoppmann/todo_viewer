"""Ereignisse zwischen Core und Plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Event:
    """`topic` hat die Form `<owner>.<name>`; nur `public` geht über SSE."""

    topic: str
    payload: dict[str, Any] = field(default_factory=dict)
    public: bool = False

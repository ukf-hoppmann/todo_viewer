"""Configured backlog sources."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class Source:
    project: str
    path: str
    # Unknown config keys are preserved when a source is rewritten.
    extra: dict[str, Any] = field(default_factory=dict, compare=False)

    def updated(self, project: str, path: str) -> Source:
        return replace(self, project=project, path=path)


@dataclass(frozen=True)
class SourceProblem:
    """Why a configured backlog folder cannot be read."""

    code: str
    message: str

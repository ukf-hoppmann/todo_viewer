"""Configured backlog sources."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class Source:
    project: str
    path: str
    # Where the project is stored: "markdown" (files in `path`) or "database".
    backend: str = "markdown"
    # Stable identifier, independent of name, path, and position in the list; "" until the source is stored.
    id: str = ""
    # Database projects only: folder their markdown files are synced with, if any.
    sync_path: str | None = None
    # Unknown config keys are preserved when a source is rewritten.
    extra: dict[str, Any] = field(default_factory=dict, compare=False)

    def updated(self, project: str, path: str) -> Source:
        return replace(self, project=project, path=path)


@dataclass(frozen=True)
class SourceProblem:
    """Why a configured backlog folder cannot be read."""

    code: str
    message: str

"""Configured backlog sources."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class Source:
    project: str
    path: str
    # Where the project is stored: "markdown" (files in `path`) or "database".
    backend: str = "markdown"
    # Unknown config keys are preserved when a source is rewritten.
    extra: dict[str, Any] = field(default_factory=dict, compare=False)

    @property
    def id(self) -> str:
        """Stable identifier derived from the folder, independent of the position in the config."""
        return hashlib.sha1(self.path.encode("utf-8")).hexdigest()[:12]

    def updated(self, project: str, path: str) -> Source:
        return replace(self, project=project, path=path)


@dataclass(frozen=True)
class SourceProblem:
    """Why a configured backlog folder cannot be read."""

    code: str
    message: str

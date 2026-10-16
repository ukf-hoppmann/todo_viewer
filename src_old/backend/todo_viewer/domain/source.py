"""Configured backlog sources."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class SyncBaseline:
    """What the two sides of a project looked like right after its last sync (fingerprints) and when that was."""

    at: str
    primary: str
    mirror: str


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
    # Markdown projects only: whether the database keeps a mirror of the project (written by a sync only).
    mirror_database: bool = False
    # Database projects only: the mirror folder `sync_path` is kept but not used, so the mirror can be switched
    # on again without choosing the folder anew.
    mirror_disabled: bool = False
    # The owner's switch: the viewer syncs this project by itself (STORY-059). Default off; it only acts while the
    # project has a mirror (`auto_sync_active`).
    auto_sync: bool = False
    # Unknown config keys are preserved when a source is rewritten.
    extra: dict[str, Any] = field(default_factory=dict, compare=False)
    # The state after the last sync, if the project was synced since it got its mirror; not part of its identity.
    baseline: SyncBaseline | None = field(default=None, compare=False)

    @property
    def markdown_path(self) -> str | None:
        """The folder of the markdown side, whichever side is primary; None if a database project has none."""
        return (self.path if self.backend == "markdown" else self.sync_path) or None

    @property
    def mirror(self) -> str:
        """The backend that mirrors the primary one: "markdown", "database", or "none"."""
        if self.backend == "markdown":
            return "database" if self.mirror_database else "none"
        return "markdown" if self.sync_path and not self.mirror_disabled else "none"

    @property
    def auto_sync_active(self) -> bool:
        """Whether the automatic sync runs for this project: the switch is on and there is a mirror to sync with."""
        return self.auto_sync and self.mirror != "none"

    def updated(self, project: str, path: str) -> Source:
        return replace(self, project=project, path=path)


@dataclass(frozen=True)
class SourceProblem:
    """Why a configured backlog folder cannot be read."""

    code: str
    message: str

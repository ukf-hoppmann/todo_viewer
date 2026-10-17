"""Ein- und Ausgaben der Sync-Operationen des Core (HTTP + MCP)."""

from __future__ import annotations

from dataclasses import dataclass, field

from viewer.core.application.sync import Decision
from viewer.core.domain.sync import Direction


@dataclass(frozen=True)
class SyncStatusIn:
    project: str


@dataclass(frozen=True)
class SyncPreviewIn:
    project: str
    direction: Direction = "both"


@dataclass(frozen=True)
class SyncExecuteIn:
    project: str
    token: str
    direction: Direction = "both"
    decisions: list[Decision] = field(default_factory=list)
    delete_missing: bool = False

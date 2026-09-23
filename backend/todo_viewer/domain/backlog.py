"""A loaded backlog: the items of one source plus what can be done with them."""
from __future__ import annotations

from dataclasses import dataclass, field

from .item import Item, ItemFormat
from .source import SourceProblem


@dataclass
class Backlog:
    items: list[Item] = field(default_factory=list)
    # True if the backlog has both an active and an archive list.
    archive_available: bool = False
    problem: SourceProblem | None = None

    def supports_archive(self, item: Item) -> bool:
        return self.archive_available and item.format is ItemFormat.BACKLOG_V2

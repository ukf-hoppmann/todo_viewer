"""A loaded backlog: the items of one source plus what can be done with them."""
from __future__ import annotations

from dataclasses import dataclass, field

from .errors import DuplicateItemError, InvalidSourceError, ItemNotFoundError
from .item import Item
from .source import SourceProblem


@dataclass
class Backlog:
    items: list[Item] = field(default_factory=list)
    # True if the backlog has both an active and an archive list.
    archive_available: bool = False
    problem: SourceProblem | None = None

    def require_usable(self) -> None:
        """Raises the source's problem (missing folder, unsupported format, ...) if there is one."""
        if self.problem:
            raise InvalidSourceError(self.problem.message, code=self.problem.code)

    def find(self, item_id: str) -> Item:
        """The item with this id; ids are unique across the active list and the archive."""
        self.require_usable()
        found = [i for i in self.items if i.id == item_id]
        if not found:
            raise ItemNotFoundError(item_id)
        if len(found) > 1:
            raise DuplicateItemError(item_id)
        return found[0]

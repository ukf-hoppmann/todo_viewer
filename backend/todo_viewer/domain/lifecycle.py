"""Parent lifecycle and structure rules of the backlog format, checked over a whole backlog.

A change is rejected only if it introduces a violation or adds items to an existing one;
violations that were already in the files do not block other edits.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from .errors import LifecycleViolationError
from .item import Item, Status

EPIC = "Epic"
# An epic leaves Open for one of these; Rejected is allowed without children.
EPIC_NEEDS_REQUIRED_CHILD = frozenset({Status.IN_PROGRESS, Status.AWAITING_CONFIRMATION, Status.COMPLETED})
DONE_FOR_AWAITING = frozenset({Status.AWAITING_CONFIRMATION, Status.COMPLETED})
# Rules that depend on the item alone, not on other items.
OWN_RULES = frozenset({"epic_with_parent", "required_for_parent_missing", "summary_required_with_notes"})


@dataclass(frozen=True, order=True)
class Violation:
    code: str
    item_id: str
    related: tuple[str, ...] = ()


class LifecycleRules:
    def violations(self, items: Sequence[Item]) -> set[Violation]:
        children: dict[str, list[Item]] = {}
        for i in items:
            if i.parent:
                children.setdefault(i.parent, []).append(i)

        known = {i.id for i in items}
        found: set[Violation] = set()
        for i in items:
            found.update(self._structure(i, known))
            found.update(self._as_parent(i, children.get(i.id, [])))
        found.update(self._cycles(items, lambda i: [i.parent] if i.parent else [], "parent_cycle"))
        found.update(self._cycles(items, lambda i: i.dependencies, "dependency_cycle"))
        return found

    def check_change(self, before: Sequence[Item], after: Sequence[Item], returning: Sequence[Item] = ()) -> None:
        """Raises LifecycleViolationError for the first violation the change introduces or extends.

        `returning` are items that come back into use (restored from the trash): their own old flaws
        (OWN_RULES) are not counted as new; rules between items still are.
        """
        existing = {(v.code, v.item_id): set(v.related) for v in self.violations(before)}
        back = {i.id for i in returning}
        for v in self.violations([*before, *returning]):
            if v.item_id in back and v.code in OWN_RULES:
                existing[(v.code, v.item_id)] = set(v.related)
        for v in sorted(self.violations(after)):
            known = existing.get((v.code, v.item_id))
            if known is None or not set(v.related) <= known:
                raise LifecycleViolationError(v.code, v.item_id, v.related)

    def check_delete(self, items: Sequence[Item], item_id: str) -> None:
        """An item may only be deleted if nothing refers to it and no rule breaks without it."""
        referrers = [i for i in items if i.parent == item_id or item_id in i.dependencies]
        if referrers:
            raise LifecycleViolationError("item_referenced", item_id, _ids(referrers))
        self.check_change(items, [i for i in items if i.id != item_id])

    @staticmethod
    def _structure(item: Item, known: set[str]) -> Iterable[Violation]:
        if item.item_type == EPIC and item.parent:
            yield Violation("epic_with_parent", item.id)
        if item.parent and item.required_for_parent is None:
            yield Violation("required_for_parent_missing", item.id)
        if item.notes and not item.summary:
            yield Violation("summary_required_with_notes", item.id)
        refs = ([item.parent] if item.parent else []) + item.dependencies
        unknown = sorted({r for r in refs if r not in known})
        if unknown:
            yield Violation("unknown_reference", item.id, tuple(unknown))

    @staticmethod
    def _as_parent(parent: Item, children: list[Item]) -> Iterable[Violation]:
        required = [c for c in children if c.required_for_parent is True]
        if parent.item_type == EPIC and parent.status in EPIC_NEEDS_REQUIRED_CHILD and not required:
            yield Violation("epic_without_required_child", parent.id)

        if parent.status == Status.AWAITING_CONFIRMATION:
            blocking = [c for c in required if c.status not in DONE_FOR_AWAITING]
        elif parent.status == Status.COMPLETED:
            blocking = [c for c in required if c.status != Status.COMPLETED]
        else:
            blocking = []
        if blocking:
            yield Violation("required_children_not_done", parent.id, _ids(blocking))

        if Status.is_terminal(parent.status):
            active = [c for c in children if not Status.is_terminal(c.status)]
            if active:
                yield Violation("children_still_active", parent.id, _ids(active))

    @staticmethod
    def _cycles(items: Sequence[Item], edges_of: Callable[[Item], Iterable[str]], code: str) -> Iterable[Violation]:
        known = {i.id for i in items}
        graph = {i.id: [t for t in edges_of(i) if t in known] for i in items}
        seen: set[frozenset[str]] = set()
        for start in sorted(graph):
            cycle = _find_cycle(start, graph, [], set(), set())
            if cycle and frozenset(cycle) not in seen:
                seen.add(frozenset(cycle))
                yield Violation(code, min(cycle), tuple(sorted(cycle)))


def _find_cycle(node: str, graph: dict[str, list[str]], path: list[str], on_path: set[str],
                done: set[str]) -> list[str] | None:
    if node in on_path:
        return path[path.index(node):]
    if node in done:
        return None
    path.append(node)
    on_path.add(node)
    for target in graph[node]:
        cycle = _find_cycle(target, graph, path, on_path, done)
        if cycle:
            return cycle
    path.pop()
    on_path.discard(node)
    done.add(node)
    return None


def _ids(items: Iterable[Item]) -> tuple[str, ...]:
    return tuple(sorted(i.id for i in items))

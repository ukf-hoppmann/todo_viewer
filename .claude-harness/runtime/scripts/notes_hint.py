"""Hint for notes written on a story or epic while one of its children is in progress (part of the todo module).

The rule is in skills/todo/SKILL.md (where discussions are recorded). The hint is a question, never a rejection.
"""

from __future__ import annotations

from collections.abc import Sequence

CONTAINER_TYPES = {"Epic", "Story"}


def child_in_progress_hint(identifier: str, item_type: str, in_progress: Sequence[str]) -> str | None:
    """The question for notes on `identifier`, or None for tasks and when no child is in progress."""
    if item_type not in CONTAINER_TYPES or not in_progress:
        return None
    verb = "is" if len(in_progress) == 1 else "are"
    return (
        f"hint: {identifier} is a {item_type.lower()} and {', '.join(in_progress)} {verb} in progress. "
        "Does this discussion belong in the notes of that child? Exceptions are fine."
    )

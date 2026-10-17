"""Items für Tests der Domäne des Plugins `backlog`."""

from __future__ import annotations

from datetime import date

from viewer.plugins.backlog.domain.model import Item


def item(
    uid: str,
    parent: str | None = None,
    status: str = "Open",
    required: bool | None = None,
    title: str = "",
    priority: str = "Normal",
    label: str | None = None,
) -> Item:
    return Item(
        uid=uid,
        project_uid="p",
        label=label or uid.upper(),
        type="Task",
        title=title or uid,
        status=status,
        priority=priority,
        area=None,
        parent_uid=parent,
        required_for_parent=required,
        goal=None,
        completion_criteria=None,
        summary=None,
        resolution=None,
        created=date(2026, 10, 16),
        position=0,
        revision=1,
    )

"""Öffentliche Schnittstelle des Plugins `workspace` für Plugins, die es in `requires` nennen."""

from viewer.plugins.workspace.application.ports import ElementRegistry, Links, Projects
from viewer.plugins.workspace.domain.model import (
    Element,
    Link,
    LinkView,
    Project,
    TriggerLinkReserved,
    UnknownElementKind,
    UnknownReference,
)

__all__ = [
    "Element",
    "ElementRegistry",
    "Link",
    "LinkView",
    "Links",
    "Project",
    "Projects",
    "TriggerLinkReserved",
    "UnknownElementKind",
    "UnknownReference",
]

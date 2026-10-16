"""Öffentliche Schnittstelle des Plugins `workspace` für Plugins, die es in `requires` nennen."""

from viewer.plugins.workspace.application.ports import ElementRegistry, Projects
from viewer.plugins.workspace.domain.model import Element, Project, UnknownElementKind, UnknownReference

__all__ = ["Element", "ElementRegistry", "Project", "Projects", "UnknownElementKind", "UnknownReference"]

"""Test-Plugin, das Elementtypen im Register von `workspace` anmeldet und es benutzt wie ein Fach-Plugin."""

from __future__ import annotations

from typing import Any

from viewer.core.application.plugin import PluginContext, PluginDefinition
from viewer.core.domain.plugin import ElementKind

KINDS = (
    ElementKind("epic", "EPIC"),
    ElementKind("story", "STORY"),
    ElementKind("task", "TASK"),
)


class KindsServices:
    def __init__(self, context: PluginContext) -> None:
        self.database = context.database
        self.registry: Any = context.required["workspace"].registry
        self.links: Any = context.required["workspace"].links

    def run(self, action: Any) -> Any:
        """Führt `action(registry, tx)` in einer Transaktion aus (wie ein Fach-Plugin)."""
        with self.database.transaction() as tx:
            return action(self.registry, tx)

    def run_links(self, action: Any) -> Any:
        """Führt `action(links, tx)` in einer Transaktion aus (Port `Links`)."""
        with self.database.transaction() as tx:
            return action(self.links, tx)


def _build(context: PluginContext) -> KindsServices:
    return KindsServices(context)


KINDS_PLUGIN = PluginDefinition(id="kinds-test", build=_build, requires=("workspace",), element_kinds=KINDS)

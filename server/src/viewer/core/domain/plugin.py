"""Datentypen eines Plugins, die ohne Ports auskommen, und die Prüfung der Plugin-Liste."""

from __future__ import annotations

import re
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from viewer.core.domain.events import Event
from viewer.core.domain.operations import HttpBinding, Operation

_PLUGIN_ID = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
_OPERATION_NAME = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
_PATH_PARAM = re.compile(r"\{[^}]*\}")


@dataclass(frozen=True)
class Migration:
    """Eine vorwärts gerichtete Migration der eigenen Tabellen; `apply` bekommt die SQLAlchemy-Verbindung."""

    version: int
    apply: Callable[[Any], None]


@dataclass(frozen=True)
class ElementKind:
    """Ein Elementtyp, den ein Plugin im Element-Register von `workspace` anmeldet; `label_prefix` z. B. `STORY`."""

    kind: str
    label_prefix: str


@dataclass(frozen=True)
class Subscription:
    """Abonnement eines Plugins; `handler(services, event)`. `topic` ohne `*` ist exakt, mit `*` am Ende ein Präfix."""

    topic: str
    handler: Callable[[Any, Event], None]


class PluginShape(Protocol):
    """Was die Prüfung von einem Plugin wissen muss (erfüllt von `PluginDefinition`)."""

    @property
    def id(self) -> str: ...
    @property
    def requires(self) -> Sequence[str]: ...
    @property
    def operations(self) -> Sequence[Operation]: ...
    @property
    def migrations(self) -> Sequence[Migration]: ...
    @property
    def element_kinds(self) -> Sequence[ElementKind]: ...


def table_prefix(plugin_id: str) -> str:
    return plugin_id.replace("-", "_") + "_"


def route_key(owner: str, binding: HttpBinding) -> tuple[str, str]:
    path = _PATH_PARAM.sub("{}", binding.path)
    return binding.method, f"/api/{owner}{path}"


def validate_plugins(plugins: Sequence[PluginShape], reserved_owners: Sequence[str] = ("core",)) -> list[str]:
    """Gibt alle Probleme der Plugin-Liste zurück (leer = gültig). Reine Funktion."""
    problems: list[str] = []
    ids: dict[str, int] = {}
    for plugin in plugins:
        if not _PLUGIN_ID.match(plugin.id):
            problems.append(f"Plugin-ID '{plugin.id}' ist nicht kebab-case")
        if plugin.id in reserved_owners:
            problems.append(f"Plugin-ID '{plugin.id}' ist für den Core reserviert")
        ids[plugin.id] = ids.get(plugin.id, 0) + 1
    problems += [f"Plugin-ID '{pid}' kommt {n}-mal vor" for pid, n in ids.items() if n > 1]

    prefixes: dict[str, str] = {}
    for plugin in plugins:
        prefix = table_prefix(plugin.id)
        if prefix in prefixes and prefixes[prefix] != plugin.id:
            problems.append(f"Plugins '{prefixes[prefix]}' und '{plugin.id}' teilen das Tabellen-Präfix '{prefix}'")
        prefixes.setdefault(prefix, plugin.id)
    for prefix, owner in prefixes.items():
        for other_prefix, other in prefixes.items():
            if owner != other and other_prefix.startswith(prefix):
                problems.append(f"Tabellen-Präfix '{prefix}' von '{owner}' überlappt '{other_prefix}' von '{other}'")

    for plugin in plugins:
        versions = [m.version for m in plugin.migrations]
        if versions != list(range(1, len(versions) + 1)):
            problems.append(f"Migrationen von '{plugin.id}' müssen lückenlos bei 1 beginnen und aufsteigen: {versions}")

    for plugin in plugins:
        for req in plugin.requires:
            if req not in ids:
                problems.append(f"Plugin '{plugin.id}' verlangt unbekanntes Plugin '{req}'")
            elif req == plugin.id:
                problems.append(f"Plugin '{plugin.id}' verlangt sich selbst")
    problems += _cycle_problems(plugins, ids)

    for plugin in plugins:
        if plugin.element_kinds and plugin.id != "workspace" and "workspace" not in plugin.requires:
            problems.append(f"Plugin '{plugin.id}' meldet Elementtypen an und muss 'workspace' in requires nennen")

    routes: dict[tuple[str, str], str] = {}
    tools: dict[str, str] = {}
    for plugin in plugins:
        names: set[str] = set()
        for op in plugin.operations:
            where = f"{plugin.id}.{op.name}"
            if not _OPERATION_NAME.match(op.name):
                problems.append(f"Operation '{where}' ist nicht snake_case")
            if op.name in names:
                problems.append(f"Operation '{where}' ist doppelt")
            names.add(op.name)
            if op.http is not None:
                if not op.http.path.startswith("/") and op.http.path != "":
                    problems.append(f"Route von '{where}' muss mit '/' beginnen: '{op.http.path}'")
                key = route_key(plugin.id, op.http)
                if key in routes:
                    problems.append(f"Doppelte Route {key[0]} {key[1]}: '{routes[key]}' und '{where}'")
                routes.setdefault(key, where)
            if op.mcp:
                tool = f"{plugin.id.replace('-', '_')}_{op.name}"
                if tool in tools:
                    problems.append(f"Doppeltes MCP-Tool '{tool}': '{tools[tool]}' und '{where}'")
                tools.setdefault(tool, where)
    return problems


def _cycle_problems(plugins: Sequence[PluginShape], ids: dict[str, int]) -> list[str]:
    graph = {p.id: [r for r in p.requires if r in ids and r != p.id] for p in plugins}
    state: dict[str, int] = {}
    problems: list[str] = []

    def visit(node: str, path: list[str]) -> None:
        state[node] = 1
        for nxt in graph.get(node, []):
            if state.get(nxt) == 1:
                cycle = [*path[path.index(nxt) :], nxt] if nxt in path else [node, nxt]
                problems.append("Zyklus in requires: " + " -> ".join(cycle))
            elif state.get(nxt) is None:
                visit(nxt, [*path, nxt])
        state[node] = 2

    for node in graph:
        if state.get(node) is None:
            visit(node, [node])
    return problems


def load_order(plugins: Sequence[PluginShape]) -> list[str]:
    """Plugin-IDs so sortiert, dass jedes Plugin nach den Plugins aus `requires` kommt (Liste muss gültig sein)."""
    by_id = {p.id: p for p in plugins}
    order: list[str] = []
    seen: set[str] = set()

    def visit(pid: str) -> None:
        if pid in seen:
            return
        seen.add(pid)
        for req in by_id[pid].requires:
            visit(req)
        order.append(pid)

    for plugin in plugins:
        visit(plugin.id)
    return order


def schema_problems(
    owner: str,
    owned_tables: Collection[str],
    references: Mapping[str, Collection[str]],
    allowed_owners: Collection[str],
) -> list[str]:
    """Prüft nach einer Migration: eigene Tabellen tragen das Präfix, Fremdschlüssel zeigen nur auf erlaubte Besitzer.

    `references` bildet eine Tabelle auf die von ihren Fremdschlüsseln referenzierten Tabellen ab;
    `allowed_owners` sind der Besitzer selbst, der Core und die Plugins aus `requires`.
    """
    problems: list[str] = []
    own_prefix = table_prefix(owner)
    for table in sorted(owned_tables):
        if not table.startswith(own_prefix):
            problems.append(f"Tabelle '{table}' von '{owner}' trägt nicht das Präfix '{own_prefix}'")
    prefixes = [table_prefix(o) for o in allowed_owners]
    for table in sorted(references):
        for target in sorted(references[table]):
            if not any(target.startswith(p) for p in prefixes):
                problems.append(
                    f"Fremdschlüssel von '{table}' auf '{target}': '{owner}' darf nur auf eigene Tabellen, "
                    "die des Core und die von Plugins aus requires zeigen"
                )
    return problems

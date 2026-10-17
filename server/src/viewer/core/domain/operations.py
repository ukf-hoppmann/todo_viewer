"""Beschreibung von Anwendungsfällen, aus denen HTTP-Route und MCP-Tool entstehen."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


@dataclass(frozen=True)
class HttpBinding:
    """Methode und Pfad unter `/api/<owner>`; `{name}` sind Pfadparameter (Felder des Inputs)."""

    method: HttpMethod
    path: str


@dataclass(frozen=True)
class Operation:
    """Ein Anwendungsfall, einmal beschrieben.

    `handler(services, input)` bekommt die Dienste des Plugins (Ergebnis von
    `PluginDefinition.build`) und eine Instanz von `input` und gibt eine
    Instanz von `output` (oder eine Liste davon) zurück; sync oder async.
    """

    name: str
    summary: str
    kind: Literal["read", "write"]
    input: type
    output: Any
    handler: Callable[[Any, Any], Any]
    http: HttpBinding | None = None
    mcp: bool = True

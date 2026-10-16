"""UI-Zustand: ein JSON-Dokument je Besitzer, ersetzt Browser-Speicher (Architektur §4 des Scopes client)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from viewer.core.application.plugin import PluginContext, PluginDefinition
from viewer.core.application.ports import UiStateStore
from viewer.core.domain.errors import InvalidInput
from viewer.core.domain.operations import HttpBinding, Operation
from viewer.core.domain.plugin import Migration

MAX_DOCUMENT_BYTES = 256 * 1024
_OWNER = re.compile(r"^[a-z][a-z0-9-]{0,63}$")


@dataclass(frozen=True)
class GetUiState:
    owner: str


@dataclass(frozen=True)
class PutUiState:
    owner: str
    document: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UiState:
    owner: str
    document: dict[str, Any]


class UiStateService:
    def __init__(self, store: UiStateStore) -> None:
        self._store = store

    def get(self, data: GetUiState) -> UiState:
        _check_owner(data.owner)
        return UiState(data.owner, self._store.get(data.owner) or {})

    def put(self, data: PutUiState) -> UiState:
        _check_owner(data.owner)
        size = len(json.dumps(data.document, ensure_ascii=False).encode())
        if size > MAX_DOCUMENT_BYTES:
            raise InvalidInput(
                f"UI-Zustand zu groß ({size} Bytes, erlaubt {MAX_DOCUMENT_BYTES})",
                details={"size": size, "max": MAX_DOCUMENT_BYTES},
            )
        self._store.put(data.owner, data.document)
        return UiState(data.owner, data.document)


def _check_owner(owner: str) -> None:
    if not _OWNER.match(owner):
        raise InvalidInput(f"Ungültiger Besitzer '{owner}'", details={"owner": owner})


def build_core_definition(store: UiStateStore, migrations: tuple[Migration, ...]) -> PluginDefinition:
    """Der Core als Besitzer `core`: eigene Migrationen und die Operationen für den UI-Zustand.

    Weder lesen noch schreiben ist ein MCP-Tool (Einstellungen dürfen nicht als Tool angeboten werden).
    """

    def build(context: PluginContext) -> UiStateService:
        return UiStateService(store)

    return PluginDefinition(
        id="core",
        build=build,
        migrations=migrations,
        operations=(
            Operation(
                "get_ui_state",
                "UI-Zustand eines Besitzers lesen",
                "read",
                GetUiState,
                UiState,
                lambda services, data: services.get(data),
                HttpBinding("GET", "/ui-state/{owner}"),
                mcp=False,
            ),
            Operation(
                "put_ui_state",
                "UI-Zustand eines Besitzers ersetzen",
                "write",
                PutUiState,
                UiState,
                lambda services, data: services.put(data),
                HttpBinding("PUT", "/ui-state/{owner}"),
                mcp=False,
            ),
        ),
    )

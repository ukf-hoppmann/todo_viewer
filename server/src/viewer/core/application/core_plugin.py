"""Der Core als Besitzer `core`: eigene Migrationen und seine Operationen (UI-Zustand, Sync)."""

from __future__ import annotations

from dataclasses import dataclass

from viewer.core.application.client_log import ClientLogIn, ClientLogOut, ClientLogService
from viewer.core.application.plugin import PluginContext, PluginDefinition
from viewer.core.application.ports import ClientLogWriter, Clock, UiStateStore
from viewer.core.application.sync import Preview, SyncResult, SyncService, SyncStatus
from viewer.core.application.sync_operations import SyncExecuteIn, SyncPreviewIn, SyncStatusIn
from viewer.core.application.ui_state import GetUiState, PutUiState, UiState, UiStateService
from viewer.core.domain.operations import HttpBinding, Operation
from viewer.core.domain.plugin import Migration


@dataclass(frozen=True)
class HealthIn:
    pass


@dataclass(frozen=True)
class HealthOut:
    status: str


@dataclass(frozen=True)
class CoreServices:
    ui_state: UiStateService
    sync: SyncService
    client_log: ClientLogService


def build_core_definition(
    store: UiStateStore,
    migrations: tuple[Migration, ...],
    sync: SyncService,
    client_log: ClientLogWriter,
    clock: Clock,
) -> PluginDefinition:
    """Die Operationen des Core. UI-Zustand ist kein MCP-Tool (Einstellungen dürfen nicht als Tool angeboten
    werden); Sync-Status, Vorschau und Ausführen sind es, denn der Harness braucht sie."""

    def build(context: PluginContext) -> CoreServices:
        return CoreServices(UiStateService(store), sync, ClientLogService(client_log, clock))

    return PluginDefinition(
        id="core",
        build=build,
        migrations=migrations,
        operations=(
            Operation(
                "health",
                "Ist der Viewer erreichbar? Antwortet `ok`; über HTTP gibt es dafür GET /api/core/health",
                "read",
                HealthIn,
                HealthOut,
                lambda services, data: HealthOut("ok"),
            ),
            Operation(
                "get_ui_state",
                "UI-Zustand eines Besitzers lesen",
                "read",
                GetUiState,
                UiState,
                lambda services, data: services.ui_state.get(data),
                HttpBinding("GET", "/ui-state/{owner}"),
                mcp=False,
            ),
            Operation(
                "put_ui_state",
                "UI-Zustand eines Besitzers ersetzen",
                "write",
                PutUiState,
                UiState,
                lambda services, data: services.ui_state.put(data),
                HttpBinding("PUT", "/ui-state/{owner}"),
                mcp=False,
            ),
            Operation(
                "client_log",
                "Eintrag des Browser-Loggings ins viewer.log schreiben (Menge und Größe begrenzt)",
                "write",
                ClientLogIn,
                ClientLogOut,
                lambda services, data: services.client_log.write(data),
                HttpBinding("POST", "/client-log"),
                mcp=False,
            ),
            Operation(
                "sync_status",
                "Zustand des Abgleichs zwischen Datenbank und Markdown-Spiegel eines Projekts, ohne Daten zu ändern",
                "read",
                SyncStatusIn,
                SyncStatus,
                lambda services, data: services.sync.status(data.project),
                HttpBinding("GET", "/sync/{project}/status"),
            ),
            Operation(
                "sync_preview",
                "Vorschau des Abgleichs eines Projekts mit Token, Übertragungen und Konflikten",
                "read",
                SyncPreviewIn,
                Preview,
                lambda services, data: services.sync.preview(data.project, data.direction),
                HttpBinding("GET", "/sync/{project}/preview"),
            ),
            Operation(
                "sync_execute",
                "Abgleich eines Projekts ausführen (Token der Vorschau, Entscheidungen je Konflikt)",
                "write",
                SyncExecuteIn,
                SyncResult,
                lambda services, data: services.sync.execute(
                    data.project, data.token, data.direction, data.decisions, data.delete_missing
                ),
                HttpBinding("POST", "/sync/{project}/execute"),
            ),
        ),
    )

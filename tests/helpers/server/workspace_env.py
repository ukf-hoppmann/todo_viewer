from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from fakes import FixedClock
from kinds_plugin.plugin import KINDS_PLUGIN, KindsServices
from mirror_plugin.plugin import MIRROR_PLUGIN
from starlette.testclient import TestClient
from viewer.app.composition import create_app
from viewer.core.application.plugin import PluginDefinition
from viewer.core.domain.settings import Settings
from viewer.plugins.backlog.application.operations import BacklogServices
from viewer.plugins.backlog.plugin import plugin as backlog_plugin
from viewer.plugins.notes.application.operations import NotesServices
from viewer.plugins.notes.plugin import plugin as notes_plugin
from viewer.plugins.workspace.application.operations import WorkspaceServices
from viewer.plugins.workspace.plugin import plugin as workspace_plugin


class Env:
    def __init__(self, tmp_path: Path, settings: Settings, plugins: Sequence[PluginDefinition] | None = None) -> None:
        self.tmp_path = tmp_path
        self.clock = FixedClock()
        chosen = plugins or [workspace_plugin, KINDS_PLUGIN, MIRROR_PLUGIN]
        self.app = create_app(settings, plugins=chosen, clock=self.clock)
        self.client = TestClient(self.app)

    @property
    def workspace(self) -> WorkspaceServices:
        services = self.app.state.plugin_host.services("workspace")
        assert isinstance(services, WorkspaceServices)
        return services

    @property
    def kinds(self) -> KindsServices:
        services = self.app.state.plugin_host.services("kinds-test")
        assert isinstance(services, KindsServices)
        return services

    @property
    def backlog(self) -> BacklogServices:
        services = self.app.state.plugin_host.services("backlog")
        assert isinstance(services, BacklogServices)
        return services

    @property
    def notes(self) -> NotesServices:
        services = self.app.state.plugin_host.services("notes")
        assert isinstance(services, NotesServices)
        return services

    def services_links(self) -> Any:
        return self.workspace.links

    def projects(self) -> list[dict[str, object]]:
        return self.client.get("/api/workspace/projects").json()  # type: ignore[no-any-return]

    def create(self, name: str, **fields: object) -> dict[str, object]:
        response = self.client.post("/api/workspace/projects", json={"name": name, **fields})
        assert response.status_code == 200, response.text
        return response.json()  # type: ignore[no-any-return]

    def general(self) -> dict[str, object]:
        return next(p for p in self.projects() if p["builtin"])


def backlog_env(tmp_path: Path, settings: Settings) -> Env:
    """Eine Umgebung mit dem echten Plugin `backlog` (und `workspace`)."""
    return Env(tmp_path, settings, plugins=[workspace_plugin, backlog_plugin])


def notes_env(tmp_path: Path, settings: Settings) -> Env:
    """Eine Umgebung mit den echten Plugins `notes`, `backlog` (das `notes` braucht) und `workspace`."""
    return Env(tmp_path, settings, plugins=[workspace_plugin, backlog_plugin, notes_plugin])

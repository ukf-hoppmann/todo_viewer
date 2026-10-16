from __future__ import annotations

from pathlib import Path
from typing import Any

from fakes import FixedClock
from kinds_plugin.plugin import KINDS_PLUGIN, KindsServices
from mirror_plugin.plugin import MIRROR_PLUGIN
from starlette.testclient import TestClient
from viewer.app.composition import create_app
from viewer.core.domain.settings import Settings
from viewer.plugins.workspace.application.operations import WorkspaceServices
from viewer.plugins.workspace.plugin import plugin as workspace_plugin


class Env:
    def __init__(self, tmp_path: Path, settings: Settings) -> None:
        self.tmp_path = tmp_path
        self.clock = FixedClock()
        self.app = create_app(settings, plugins=[workspace_plugin, KINDS_PLUGIN, MIRROR_PLUGIN], clock=self.clock)
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

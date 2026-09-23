from __future__ import annotations

import json
import os
import shutil
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from todo_viewer.api import create_app
from todo_viewer.bootstrap import PROJECT_ROOT, Settings, build_container

FIXTURES = Path(__file__).parent / "fixtures"
GOLDEN = Path(__file__).parent / "golden"
UPDATE_GOLDEN = os.environ.get("UPDATE_GOLDEN") == "1"


@dataclass
class Response:
    status_code: int
    body: Any


class ApiClient:
    """Framework-neutral wrapper so the characterization tests survive a framework swap."""

    def __init__(self, raw: Any, root: Path):
        self._raw = raw
        self.root = root

    def _wrap(self, resp: Any) -> Response:
        return Response(resp.status_code, resp.json())

    def get(self, url: str, **params: Any) -> Response:
        return self._wrap(self._raw.get(url, params=params))

    def post(self, url: str, body: Any) -> Response:
        return self._wrap(self._raw.post(url, json=body))

    def put(self, url: str, body: Any) -> Response:
        return self._wrap(self._raw.put(url, json=body))

    def delete(self, url: str, **params: Any) -> Response:
        return self._wrap(self._raw.delete(url, params=params))


@dataclass
class Workspace:
    root: Path
    config_dir: Path
    repos: Path

    def add_backlog(self, fixture: str, name: str | None = None) -> Path:
        """Copies a fixture folder into a fake git repo and returns the backlog folder."""
        repo = self.repos / (name or fixture)
        (repo / ".git").mkdir(parents=True, exist_ok=True)
        target = repo / "docs"
        shutil.copytree(FIXTURES / fixture, target)
        return target

    def write_config(self, sources: list[dict[str, str]]) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "config.json").write_text(json.dumps({"sources": sources}), encoding="utf-8")

    def read_config(self) -> dict[str, Any]:
        return json.loads((self.config_dir / "config.json").read_text(encoding="utf-8"))


@pytest.fixture
def workspace(tmp_path: Path) -> Workspace:
    ws = Workspace(root=tmp_path, config_dir=tmp_path / "configs", repos=tmp_path / "repos")
    ws.repos.mkdir()
    return ws


@pytest.fixture
def settings(workspace: Workspace) -> Settings:
    frontend = workspace.root / "frontend"
    frontend.mkdir()
    (frontend / "index.html").write_text("<!doctype html><title>test</title>", encoding="utf-8")
    return Settings(base_dir=PROJECT_ROOT, config_dir=workspace.config_dir,
                    frontend_dir=frontend, browse_start=str(workspace.repos))


@pytest.fixture
def api(workspace: Workspace, settings: Settings) -> Iterator[ApiClient]:
    app = create_app(build_container(settings), settings.frontend_dir)
    with TestClient(app) as client:
        yield ApiClient(client, workspace.root)


def _normalize(value: Any, roots: list[str]) -> Any:
    if isinstance(value, str):
        for root in roots:
            value = value.replace(root, "<ROOT>")
        return value
    if isinstance(value, list):
        return [_normalize(v, roots) for v in value]
    if isinstance(value, dict):
        return {k: _normalize(v, roots) for k, v in value.items()}
    return value


@pytest.fixture
def golden(workspace: Workspace) -> Callable[[str, Any], None]:
    """Compares data (JSON) or text (.md) against a stored golden file."""
    roots = sorted({str(workspace.root.resolve()), str(workspace.root)}, key=len, reverse=True)

    def check(name: str, data: Any) -> None:
        path = GOLDEN / name
        if isinstance(data, str):
            actual = data
        else:
            actual = json.dumps(_normalize(data, roots), indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        if UPDATE_GOLDEN or not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(actual.encode("utf-8"))
            if not UPDATE_GOLDEN:
                pytest.fail(f"golden file {name} created, re-run to verify")
        assert actual == path.read_bytes().decode("utf-8")

    return check

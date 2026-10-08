from __future__ import annotations

import json

import pytest

from tests.conftest import ApiClient, Workspace

PROJECT = "demo"
BASE = f"/api/v2/projects/{PROJECT}"


@pytest.fixture
def notes_api(api: ApiClient, workspace: Workspace) -> ApiClient:
    """The API with one database project, `demo`, in which notes and topics live."""
    workspace.config_dir.mkdir(parents=True, exist_ok=True)
    sources = [{"project": PROJECT, "path": "demo", "backend": "database"}]
    (workspace.config_dir / "config.json").write_text(json.dumps({"sources": sources}), encoding="utf-8")
    return api

from __future__ import annotations

import json

import pytest

from tests.conftest import ApiClient, Workspace

PROJECT = "demo"
OTHER = "other"
BASE = f"/api/v2/projects/{PROJECT}"
OTHER_BASE = f"/api/v2/projects/{OTHER}"


@pytest.fixture
def notes_api(api: ApiClient, workspace: Workspace) -> ApiClient:
    """The API with two database projects, `demo` and `other`, in which notes and topics live."""
    workspace.config_dir.mkdir(parents=True, exist_ok=True)
    sources = [{"project": PROJECT, "path": "demo", "backend": "database"},
               {"project": OTHER, "path": "other", "backend": "database"}]
    (workspace.config_dir / "config.json").write_text(json.dumps({"sources": sources}), encoding="utf-8")
    return api

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from example_plugin.plugin import EXAMPLE_PLUGIN
from fastapi.testclient import TestClient
from viewer.app.composition import create_app
from viewer.core.domain.settings import Settings
from viewer.core.infrastructure.config import load_settings


@pytest.fixture
def dist(tmp_path: Path) -> Path:
    folder = tmp_path / "dist"
    (folder / "assets").mkdir(parents=True)
    (folder / "index.html").write_text("<html>Viewer</html>", encoding="utf-8")
    (folder / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    (folder / "favicon.svg").write_text("<svg/>", encoding="utf-8")
    (tmp_path / "geheim.txt").write_text("nicht ausliefern", encoding="utf-8")
    return folder


def client(tmp_path: Path, static_dir: Path) -> TestClient:
    settings = Settings(
        db_path=str(tmp_path / "viewer.db"),
        backup_dir=str(tmp_path / "backups"),
        log_dir=str(tmp_path / "logs"),
        static_dir=str(static_dir),
    )
    return TestClient(create_app(settings, plugins=[EXAMPLE_PLUGIN]))


@pytest.fixture
def web(tmp_path: Path, dist: Path) -> Iterator[TestClient]:
    with client(tmp_path, dist) as test_client:
        yield test_client


def test_the_root_and_every_address_of_the_ui_serve_index_html(web: TestClient) -> None:
    for path in ("/", "/backlog/main", "/notes/main/deep/link"):
        response = web.get(path)
        assert (response.status_code, response.text) == (200, "<html>Viewer</html>")
        assert response.headers["cache-control"] == "no-cache"


def test_files_of_the_build_are_served_and_assets_are_cached_for_good(web: TestClient) -> None:
    asset = web.get("/assets/app.js")
    icon = web.get("/favicon.svg")

    assert (asset.status_code, asset.text) == (200, "console.log(1)")
    assert "immutable" in asset.headers["cache-control"]
    assert (icon.status_code, icon.text) == (200, "<svg/>")


def test_files_outside_the_folder_are_not_served(web: TestClient) -> None:
    response = web.get("/%2e%2e/geheim.txt")

    assert "nicht ausliefern" not in response.text


def test_api_and_mcp_win_over_the_ui_and_unknown_api_paths_are_errors(web: TestClient) -> None:
    assert web.get("/api/core/health").json() == {"status": "ok"}
    unknown = web.get("/api/nope")
    assert (unknown.status_code, unknown.json()["code"]) == (404, "not_found")
    assert web.get("/mcp/x").status_code == 404
    assert "<html>" not in web.get("/api/nope").text


def test_the_server_serves_only_the_api_when_there_is_no_build(tmp_path: Path) -> None:
    with client(tmp_path, tmp_path / "missing") as api_only:
        assert api_only.get("/api/core/health").status_code == 200
        assert api_only.get("/").status_code == 404


def test_the_folder_of_the_build_is_configurable() -> None:
    assert load_settings(env={"VIEWER_STATIC_DIR": "/app/client/dist"}).static_dir == "/app/client/dist"
    assert load_settings(env={}).static_dir == "client/dist"


def test_a_missing_asset_is_a_404_and_not_the_index_html(web: TestClient) -> None:
    response = web.get("/assets/Old-abc123.js")

    assert (response.status_code, response.json()["code"]) == (404, "not_found")
    assert "<html>" not in response.text

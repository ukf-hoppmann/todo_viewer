"""One log line per request (level by outcome), error code and details for 4xx, stack trace for 5xx."""
from __future__ import annotations

import logging
import re
from pathlib import Path

import pytest
import structlog
from fastapi.testclient import TestClient

from todo_viewer.api import create_app
from todo_viewer.bootstrap import build_container
from todo_viewer.infrastructure.log_setup import configure_logging
from todo_viewer.infrastructure.markdown.repository import MarkdownBacklogRepository


@pytest.fixture
def log(tmp_path):
    path = tmp_path / "test.log"
    configure_logging("DEBUG", path)

    def read(event: str = "request") -> list[str]:
        for handler in logging.getLogger().handlers:
            handler.flush()
        text = path.read_text(encoding="utf-8")
        # an entry is its line plus the indented stack trace below it
        return [e for e in re.split(r"\n(?! )", text) if e.split(" ")[2:3] == [event]]

    yield read
    logging.getLogger().handlers.clear()
    structlog.reset_defaults()


@pytest.fixture
def app(settings):
    return create_app(build_container(settings), settings.frontend_dir)


@pytest.fixture
def client(app):
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def source_id(workspace, client):
    folder = workspace.add_backlog("backlog")
    workspace.write_config([{"project": "backlog", "path": str(folder)}])
    return client.get("/api/v2/sources").json()[0]["id"]


def _item_body(source_id: str, **override: str) -> dict:
    return {"source_id": source_id, "type": "Task", "title": "x", "area": "a", "goal": "g",
            "completion_criteria": "c", **override}


def test_rejected_request_logs_code_and_details(client, source_id, log):
    resp = client.post("/api/v2/items", json=_item_body(source_id, parent="STORY-000", required_for_parent="No"))

    assert resp.status_code == 409
    [line] = log()
    assert " WARNING request " in line
    assert re.search(r" req=[0-9a-f]{8} ", line)
    assert "method=POST path=/api/v2/items status=409" in line
    assert "code=parent_closed" in line
    assert "details.items=STORY-000" in line
    assert "message=" in line


def test_validation_error_logs_the_field(client, source_id, log):
    resp = client.post("/api/v2/items", json=_item_body(source_id, goal=None))  # type: ignore[arg-type]

    assert resp.status_code == 400
    [line] = log()
    assert "status=400 " in line and "code=bad_request" in line and "details.field=goal" in line


def test_write_logs_info_with_created_item(client, source_id, log):
    resp = client.post("/api/v2/items", json=_item_body(source_id))

    assert resp.status_code == 201
    [line] = log()
    assert " INFO request " in line
    assert "status=201 " in line
    assert f"source={source_id}" in line and "item=TASK-004" in line


def test_reads_are_debug_only(client, source_id, log):
    client.get("/api/v2/backlog")

    [line] = log()
    assert " DEBUG request " in line and "method=GET path=/api/v2/backlog status=200" in line


def test_ui_state_saves_are_debug_only(client, log):
    client.put("/api/v2/ui-state", json={"view": "list"})

    [line] = log()
    assert " DEBUG request " in line and "method=PUT" in line


def test_query_string_is_logged(client, source_id, log):
    client.get("/api/v2/index", params={"source_id": source_id})

    [line] = log()
    assert f'query="source_id={source_id}"' in line


def test_unhandled_error_logs_stack_trace(app, client, source_id, log, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("kaputt")
    monkeypatch.setattr(app.state.container.items, "create", boom)

    resp = client.post("/api/v2/items", json=_item_body(source_id))

    assert resp.status_code == 500
    [entry] = log()
    first, *trace = entry.splitlines()
    assert " ERROR request " in first and "status=500" in first
    assert trace and "RuntimeError: kaputt" in trace[-1]


def test_os_error_logs_code_and_stack_trace(app, client, source_id, log, monkeypatch):
    def denied(*_, **__):
        raise PermissionError(13, "Permission denied", "/backlog/TODO.md")
    monkeypatch.setattr(app.state.container.items, "create", denied)

    resp = client.post("/api/v2/items", json=_item_body(source_id))

    assert (resp.status_code, resp.json()["code"]) == (500, "write_failed")
    [entry] = log()
    first, *trace = entry.splitlines()
    assert " ERROR request " in first and "status=500" in first and "code=write_failed" in first
    assert trace and "PermissionError" in trace[-1]


def test_file_write_is_logged_with_the_request_id(client, source_id, log):
    client.post("/api/v2/items", json=_item_body(source_id))

    [request] = log()
    [written] = log("file_written")
    assert " INFO file_written " in written and "TODO.md" in written
    req = re.search(r" req=(\w+) ", request).group(1)
    assert f" req={req} " in written


def test_unparsable_backlog_is_warned(client, source_id, log, monkeypatch):
    def broken(*_, **__):
        raise ValueError("unexpected heading")
    monkeypatch.setattr(MarkdownBacklogRepository, "_parse", broken)

    client.get("/api/v2/backlog")

    [line, *_] = log("backlog_unparsable")
    assert " WARNING backlog_unparsable " in line and "TODO.md" in line
    assert 'error="ValueError: unexpected heading"' in line


def test_unreadable_ui_state_is_warned(client, workspace, log):
    workspace.config_dir.mkdir(parents=True, exist_ok=True)
    (workspace.config_dir / "ui_state.json").write_text("{kaputt", encoding="utf-8")

    assert client.get("/api/v2/ui-state").json() == {}

    [line] = log("ui_state_unreadable")
    assert " WARNING " in line and "ui_state.json" in line and "error=" in line


def test_unreadable_folder_is_warned(client, workspace, log, monkeypatch):
    def denied(self):
        raise PermissionError(13, "Permission denied", str(self))
    monkeypatch.setattr(Path, "iterdir", denied)

    listing = client.get("/api/v2/folders", params={"path": str(workspace.repos)}).json()

    assert listing["error"]
    [line] = log("folder_unreadable")
    assert " WARNING " in line and "Permission denied" in line

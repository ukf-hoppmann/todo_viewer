"""Der ganze Viewer als echter Prozess-Server mit MCP-Client für die Systemtests (Aufbau wie `test_harness_flow.py`)."""

from __future__ import annotations

import json
import socket
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import uvicorn
from mcp import Client
from mcp.types import TextContent
from running_server import RunningServer

from viewer.app.composition import create_app
from viewer.core.domain.settings import Settings


@contextmanager
def running_viewer(tmp_path: Path) -> Iterator[RunningServer]:
    """Der ganze Viewer mit allen Plugins als uvicorn-Server auf einem freien Port, Daten unter `tmp_path`."""
    settings = Settings(
        sse_keepalive_seconds=0.2,
        db_path=str(tmp_path / "viewer.db"),
        backup_dir=str(tmp_path / "backups"),
        log_dir=str(tmp_path / "logs"),
    )
    app = create_app(settings)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", lifespan="on"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not server.started and time.time() < deadline:
        time.sleep(0.02)
    assert server.started, "Server startet nicht"
    try:
        yield RunningServer(f"http://127.0.0.1:{port}", app)
    finally:
        server.should_exit = True
        thread.join(timeout=10)


class Harness:
    """Ruft die MCP-Tools des Viewers auf und gibt den JSON-Inhalt der Antwort zurück."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def call(self, tool: str, **arguments: Any) -> Any:
        result = await self._client.call_tool(tool, arguments)
        body = _body(result.content[0])
        assert not result.is_error, f"{tool}: {body}"
        return body

    async def fails(self, tool: str, **arguments: Any) -> dict[str, Any]:
        result = await self._client.call_tool(tool, arguments)
        assert result.is_error, f"{tool} hätte scheitern müssen"
        body: dict[str, Any] = _body(result.content[0])
        return body


def _body(content: Any) -> Any:
    assert isinstance(content, TextContent)
    return json.loads(content.text)

"""Der Neubau als echter Prozess (`python -m viewer.app.main`), wie ihn das Image startet: API, MCP und Frontend."""

from __future__ import annotations

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest
import viewer
from mcp import Client

SRC = Path(viewer.__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def get(url: str) -> tuple[int, str]:
    with urllib.request.urlopen(url, timeout=3) as response:
        return response.status, response.read().decode()


@pytest.fixture
def process(tmp_path: Path) -> Iterator[str]:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>Neubau</html>", encoding="utf-8")
    port = free_port()
    env = {
        **os.environ,
        "PYTHONPATH": str(SRC),
        "VIEWER_CONFIG": str(tmp_path / "none.json"),
        "VIEWER_PORT": str(port),
        "VIEWER_DB": str(tmp_path / "configs" / "viewer.db"),
        "VIEWER_BACKUP_DIR": str(tmp_path / "configs" / "backups"),
        "VIEWER_LOG_DIR": str(tmp_path / "logs"),
        "VIEWER_STATIC_DIR": str(dist),
    }
    server = subprocess.Popen([sys.executable, "-m", "viewer.app.main"], env=env, cwd=tmp_path)  # noqa: S603
    base = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                get(base + "/api/core/health")
                break
            except OSError:
                if server.poll() is not None:
                    pytest.fail("Der Server ist beendet")
                time.sleep(0.1)
        else:
            pytest.fail("Der Server antwortet nicht")
        yield base
    finally:
        server.terminate()
        server.wait(timeout=15)


def test_the_process_answers_health_serves_the_ui_and_speaks_mcp(process: str, tmp_path: Path) -> None:
    assert json.loads(get(process + "/api/core/health")[1]) == {"status": "ok"}
    assert get(process + "/")[1] == "<html>Neubau</html>"
    assert get(process + "/memos/main")[1] == "<html>Neubau</html>"

    async def tools() -> set[str]:
        async with Client(process + "/mcp") as client:
            return {tool.name for tool in (await client.list_tools()).tools}

    names = asyncio.run(tools())
    assert {"core_health", "backlog_index_lines", "memos_move_memo", "alarms_create_alarm"} <= names
    assert (tmp_path / "configs" / "viewer.db").is_file() and (tmp_path / "logs" / "viewer.log").is_file()

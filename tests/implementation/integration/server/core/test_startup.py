from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx2 as httpx
import pytest
from viewer.app.composition import PLUGINS, create_app
from viewer.core.application.plugin import PluginDefinition
from viewer.core.domain.errors import PluginSetupError
from viewer.core.domain.settings import Settings

SERVER_DIR = Path(__file__).resolve().parents[5] / "server"


def test_faulty_plugin_list_prevents_start_with_clear_message() -> None:
    plugins = [
        PluginDefinition("a", lambda c: None, requires=("b",)),
        PluginDefinition("b", lambda c: None, requires=("a", "fehlt")),
    ]
    with pytest.raises(PluginSetupError) as err:
        create_app(plugins=plugins)
    message = str(err.value)
    assert "Zyklus in requires: a -> b -> a" in message
    assert "Plugin 'b' verlangt unbekanntes Plugin 'fehlt'" in message


def test_production_plugin_list_is_valid(settings: Settings) -> None:
    create_app(settings, plugins=PLUGINS)


def test_server_process_starts_and_answers_health(tmp_path: Path) -> None:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    env = {
        **os.environ,
        "PYTHONPATH": str(SERVER_DIR / "src"),
        "VIEWER_PORT": str(port),
        "VIEWER_LOG_DIR": str(tmp_path / "logs"),
        "VIEWER_DB": str(tmp_path / "viewer.db"),
        "VIEWER_BACKUP_DIR": str(tmp_path / "backups"),
        "VIEWER_CONFIG": str(tmp_path / "none.json"),
    }
    proc = subprocess.Popen(
        [sys.executable, "-m", "viewer.app.main"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        deadline = time.time() + 15
        response = None
        while time.time() < deadline:
            try:
                response = httpx.get(f"http://127.0.0.1:{port}/api/core/health", timeout=1)
                break
            except httpx.TransportError:
                time.sleep(0.1)
        assert response is not None and response.json() == {"status": "ok"}
    finally:
        proc.terminate()
        proc.wait(timeout=10)
    entries = [json.loads(line) for line in (tmp_path / "logs" / "viewer.log").read_text(encoding="utf-8").splitlines()]
    assert any(e.get("event") == "request" and e.get("path") == "/api/core/health" for e in entries)

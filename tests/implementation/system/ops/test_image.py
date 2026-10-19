"""Das Image des Neubaus bauen, starten und `GET /api/core/health` fragen (braucht einen laufenden Docker).

Eigener Befehl (siehe `tests/README.md`): `VIEWER_IMAGE_TEST=1 pytest …/test_image.py`. Ohne diese Variable oder ohne
erreichbaren Docker-Daemon wird übersprungen (der Bau lädt Basis-Images und Pakete aus dem Netz und dauert Minuten).
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
TAG = "todo-viewer-next-test"


def docker_available() -> bool:
    if os.environ.get("VIEWER_IMAGE_TEST") != "1" or shutil.which("docker") is None:
        return False
    return subprocess.run(["docker", "info"], capture_output=True, check=False).returncode == 0


pytestmark = pytest.mark.skipif(
    not docker_available(), reason="VIEWER_IMAGE_TEST=1 und ein erreichbarer Docker-Daemon fehlen"
)


@pytest.fixture
def container(tmp_path: Path) -> Iterator[str]:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run(["docker", "build", "-f", "server/Dockerfile", "-t", TAG, "."], cwd=ROOT, check=True)
    name = f"{TAG}-{port}"
    configs, logs = tmp_path / "configs", tmp_path / "logs"
    configs.mkdir()
    logs.mkdir()
    subprocess.run(
        ["docker", "run", "-d", "--name", name, "-p", f"127.0.0.1:{port}:5411"]
        + ["-v", f"{configs}:/app/configs", "-v", f"{logs}:/app/logs", TAG],
        check=True,
    )
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, check=False)
        subprocess.run(["docker", "rmi", "-f", TAG], capture_output=True, check=False)


def test_the_image_answers_health_and_serves_the_built_frontend(container: str, tmp_path: Path) -> None:
    deadline = time.time() + 60
    while True:
        try:
            with urllib.request.urlopen(container + "/api/core/health", timeout=3) as response:
                assert response.status == 200 and b'"ok"' in response.read()
            break
        except OSError:
            assert time.time() < deadline, "Der Container antwortet nicht"
            time.sleep(0.5)
    with urllib.request.urlopen(container + "/", timeout=3) as page:
        assert b'<div id="root">' in page.read()
    assert (tmp_path / "configs" / "viewer.db").is_file()

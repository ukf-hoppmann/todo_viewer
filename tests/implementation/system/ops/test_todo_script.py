"""`todo.sh` mit einem Ersatz für `docker`; die Compose-Datei."""

from __future__ import annotations

import json
import shutil
import stat
import subprocess
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
FAKE = """#!/bin/bash
echo "$@" >> "$CALLS"
"""


def _answers(url: str) -> bool:
    try:
        urllib.request.urlopen(url, timeout=2)  # noqa: S310
    except OSError:
        return False
    return True


@pytest.fixture
def docker(tmp_path: Path) -> Path:
    script = tmp_path / "fake-docker"
    script.write_text(FAKE, encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


def todo(
    docker: Path, tmp_path: Path, *args: str, script: str = "todo.sh"
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    calls = tmp_path / "calls.txt"
    calls.write_text("", encoding="utf-8")
    result = subprocess.run(
        [str(ROOT / script), *args],
        capture_output=True,
        text=True,
        env={"DOCKER": str(docker), "CALLS": str(calls), "PATH": "/usr/bin:/bin"},
        check=False,
    )
    return result, calls.read_text(encoding="utf-8").splitlines()


def test_todo_sh_hands_its_time_zone_to_compose(tmp_path: Path) -> None:
    """Gesetztes `TZ` bleibt; sonst kommt die Zone des Rechners aus `/etc/localtime`."""
    seen = tmp_path / "tz.txt"
    fake = tmp_path / "fake-docker"
    fake.write_text('#!/bin/bash\necho "${TZ:-unset}" >> "$SEEN"\n', encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)

    def run(env: dict[str, str]) -> str:
        seen.write_text("", encoding="utf-8")
        base = {"DOCKER": str(fake), "SEEN": str(seen), "PATH": "/usr/bin:/bin"}
        subprocess.run([str(ROOT / "todo.sh"), "stop"], env={**base, **env}, capture_output=True, check=True)
        return seen.read_text(encoding="utf-8").strip()

    assert run({"TZ": "Asia/Tokyo"}) == "Asia/Tokyo"
    localtime = Path("/etc/localtime")
    if localtime.is_symlink() and "zoneinfo/" in str(localtime.resolve()):
        assert run({}) == str(localtime.resolve()).split("zoneinfo/", 1)[1]


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker ist nicht installiert")
def test_the_compose_file_has_the_viewer_and_its_proxy() -> None:
    output = subprocess.run(
        ["docker", "compose", "config", "--format", "json"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    services = json.loads(output)["services"]

    assert set(services) == {"todo-viewer-next", "todo-proxy"}
    new = services["todo-viewer-next"]
    assert new["restart"] == "unless-stopped"
    assert new["build"]["dockerfile"] == "server/Dockerfile"
    assert [(p["host_ip"], p["published"], p["target"]) for p in new["ports"]] == [("127.0.0.1", "5411", 5411)]
    targets = {v["target"] for v in new["volumes"]}
    assert {"/app/configs", "/app/logs"} <= targets
    assert any(e.startswith("BROWSE_START") or e == "BROWSE_START" for e in new["environment"])
    assert "TZ" in new["environment"]
    proxy = services["todo-proxy"]
    assert proxy["image"].startswith("nginx:")
    assert "todo-viewer-next" in proxy["depends_on"]
    assert [(p["host_ip"], p["published"], p["target"]) for p in proxy["ports"]] == [("127.0.0.1", "5413", 80)]
    assert [v["target"] for v in proxy["volumes"]] == ["/etc/nginx/conf.d/default.conf"]


def test_the_proxy_forwards_todo_localhost_to_the_new_service_without_buffering() -> None:
    conf = (ROOT / "nginx" / "todo.localhost.conf").read_text(encoding="utf-8")

    assert "server_name todo.localhost;" in conf
    assert "http://todo-viewer-next:5411" in conf
    assert "proxy_buffering off;" in conf


@pytest.mark.parametrize(
    ("arguments", "calls"),
    [
        (["start"], ["compose up -d --build todo-viewer-next todo-proxy"]),
        (["stop"], ["compose stop todo-viewer-next todo-proxy"]),
        (["restart"], ["compose restart todo-viewer-next todo-proxy"]),
        (["down"], ["compose rm -sf todo-viewer-next todo-proxy"]),
        (["update"], ["compose build --no-cache todo-viewer-next", "compose up -d todo-viewer-next todo-proxy"]),
    ],
)
def test_the_new_starter_addresses_the_new_service_and_its_proxy(
    docker: Path, tmp_path: Path, arguments: list[str], calls: list[str]
) -> None:
    result, seen = todo(docker, tmp_path, *arguments, script="todo.sh")

    assert result.returncode == 0, result.stderr
    assert seen == calls


def test_the_new_starter_prints_the_usage_for_an_unknown_command(docker: Path, tmp_path: Path) -> None:
    result, seen = todo(docker, tmp_path, "nope", script="todo.sh")

    assert result.returncode == 1 and seen == []
    assert "start" in result.stdout

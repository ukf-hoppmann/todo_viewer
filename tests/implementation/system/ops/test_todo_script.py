"""`todo.sh` (Neubau) und `todo_old.sh` (alter Viewer) mit einem Ersatz für `docker`; die Compose-Datei."""

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
    docker: Path, tmp_path: Path, *args: str, script: str = "todo_old.sh"
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


@pytest.mark.parametrize(
    ("arguments", "calls"),
    [
        (["next", "start"], ["compose up -d --build todo-viewer-next"]),
        (["next", "stop"], ["compose stop todo-viewer-next"]),
        (["next", "restart"], ["compose restart todo-viewer-next"]),
        (["next", "update"], ["compose build --no-cache todo-viewer-next", "compose up -d todo-viewer-next"]),
    ],
)
def test_next_commands_address_only_the_new_service(
    docker: Path, tmp_path: Path, arguments: list[str], calls: list[str]
) -> None:
    result, seen = todo(docker, tmp_path, *arguments)

    assert result.returncode == 0, result.stderr
    assert seen == calls


def test_next_status_shows_the_container_and_says_when_it_does_not_answer(docker: Path, tmp_path: Path) -> None:
    if _answers("http://localhost:5411/api/core/health"):
        pytest.skip("auf dieser Maschine läuft der Neubau gerade auf Port 5411")
    result, seen = todo(docker, tmp_path, "next", "status")

    assert seen == ["compose ps -a todo-viewer-next"]
    assert result.returncode == 0 and "antwortet nicht unter http://localhost:5411" in result.stderr


def test_next_logs_fall_back_to_the_container_output_without_a_log_file(docker: Path, tmp_path: Path) -> None:
    log = ROOT / "logs" / "viewer.log"
    if log.exists():
        pytest.skip("logs/viewer.log gibt es auf dieser Maschine schon")

    _, seen = todo(docker, tmp_path, "next", "logs")

    assert seen == ["compose logs todo-viewer-next"]


def test_the_old_commands_no_longer_touch_the_new_service(docker: Path, tmp_path: Path) -> None:
    for command, expected in (
        ("stop", "compose stop todo-viewer"),
        ("restart", "compose restart todo-viewer"),
        ("status", "compose ps -a todo-viewer"),
    ):
        _, seen = todo(docker, tmp_path, command)
        assert seen == [expected], command


def test_an_unknown_command_prints_the_usage_for_both_viewers(docker: Path, tmp_path: Path) -> None:
    result, seen = todo(docker, tmp_path, "next", "nope")

    assert result.returncode == 1 and seen == []
    assert "next start" in result.stdout and "Neubau" in result.stdout


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
def test_the_compose_file_has_the_new_service_next_to_the_old_one() -> None:
    output = subprocess.run(
        ["docker", "compose", "config", "--format", "json"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    services = json.loads(output)["services"]

    assert set(services) == {"todo-viewer", "todo-viewer-next"}
    new = services["todo-viewer-next"]
    assert new["restart"] == "unless-stopped"
    assert new["build"]["dockerfile"] == "server/Dockerfile"
    assert [(p["host_ip"], p["published"], p["target"]) for p in new["ports"]] == [("127.0.0.1", "5411", 5411)]
    targets = {v["target"] for v in new["volumes"]}
    assert {"/app/configs", "/app/logs"} <= targets
    assert any(e.startswith("BROWSE_START") or e == "BROWSE_START" for e in new["environment"])
    assert "TZ" in new["environment"]
    assert services["todo-viewer"]["ports"][0]["published"] == "5412"


@pytest.mark.parametrize(
    ("arguments", "calls"),
    [
        (["start"], ["compose up -d --build todo-viewer-next"]),
        (["stop"], ["compose stop todo-viewer-next"]),
        (["restart"], ["compose restart todo-viewer-next"]),
        (["down"], ["compose rm -sf todo-viewer-next"]),
        (["update"], ["compose build --no-cache todo-viewer-next", "compose up -d todo-viewer-next"]),
    ],
)
def test_the_new_starter_addresses_only_the_new_service(
    docker: Path, tmp_path: Path, arguments: list[str], calls: list[str]
) -> None:
    result, seen = todo(docker, tmp_path, *arguments, script="todo.sh")

    assert result.returncode == 0, result.stderr
    assert seen == calls


def test_the_new_starter_prints_the_usage_for_an_unknown_command(docker: Path, tmp_path: Path) -> None:
    result, seen = todo(docker, tmp_path, "nope", script="todo.sh")

    assert result.returncode == 1 and seen == []
    assert "todo_old.sh" in result.stdout

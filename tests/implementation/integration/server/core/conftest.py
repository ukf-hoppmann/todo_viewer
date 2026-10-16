from __future__ import annotations

import socket
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
import uvicorn
from example_plugin.plugin import EXAMPLE_PLUGIN
from fakes import FixedClock
from fastapi import FastAPI
from running_server import RunningServer
from viewer.app.composition import create_app
from viewer.core.domain.settings import Settings
from viewer.core.infrastructure.database import MigrationRunner, SqliteBackupMaker, SqliteDatabase


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        sse_keepalive_seconds=0.2,
        db_path=str(tmp_path / "viewer.db"),
        backup_dir=str(tmp_path / "backups"),
        log_dir=str(tmp_path / "logs"),
    )


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings, plugins=[EXAMPLE_PLUGIN])


@pytest.fixture
def server(app: FastAPI) -> Iterator[RunningServer]:
    """Echter uvicorn-Server auf einem freien Port, für Streaming-Tests."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", lifespan="on")
    uv = uvicorn.Server(config)
    thread = threading.Thread(target=uv.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not uv.started and time.time() < deadline:
        time.sleep(0.02)
    assert uv.started, "Server startet nicht"
    try:
        yield RunningServer(f"http://127.0.0.1:{port}", app)
    finally:
        uv.should_exit = True
        thread.join(timeout=10)


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()


@pytest.fixture
def database(tmp_path: Path) -> Iterator[SqliteDatabase]:
    db = SqliteDatabase(tmp_path / "data" / "viewer.db")
    yield db
    db.dispose()


@pytest.fixture
def backups(database: SqliteDatabase, tmp_path: Path, clock: FixedClock) -> SqliteBackupMaker:
    return SqliteBackupMaker(database, tmp_path / "backups", clock)


@pytest.fixture
def runner(database: SqliteDatabase, backups: SqliteBackupMaker) -> MigrationRunner:
    return MigrationRunner(database, backups)

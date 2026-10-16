from __future__ import annotations

import socket
import threading
import time
from collections.abc import Iterator

import pytest
import uvicorn
from example_plugin.plugin import EXAMPLE_PLUGIN
from fastapi import FastAPI
from running_server import RunningServer
from viewer.app.composition import create_app
from viewer.core.domain.settings import Settings


@pytest.fixture
def app() -> FastAPI:
    return create_app(Settings(sse_keepalive_seconds=0.2), plugins=[EXAMPLE_PLUGIN])


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

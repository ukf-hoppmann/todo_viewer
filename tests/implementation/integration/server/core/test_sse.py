from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable, Iterator

import httpx2 as httpx
from running_server import RunningServer
from viewer.core.domain.events import Event


def read_until(lines: Iterator[str], predicate: Callable[[list[str]], bool], limit: int = 50) -> list[str]:
    seen: list[str] = []
    for line in lines:
        seen.append(line)
        if predicate(seen):
            return seen
        if len(seen) > limit:
            break
    raise AssertionError(f"nicht erhalten: {seen}")


def wait_for_clients(server: RunningServer, n: int) -> None:
    hub = server.app.state.hub
    deadline = time.time() + 5
    while hub.client_count < n and time.time() < deadline:
        time.sleep(0.01)
    assert hub.client_count >= n


def test_public_event_reaches_sse_client_and_private_does_not(server: RunningServer) -> None:
    bus = server.app.state.events
    with httpx.Client(timeout=10) as client, client.stream("GET", server.base_url + "/api/core/events") as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        wait_for_clients(server, 1)
        bus.publish(Event("example.secret", {"x": 1}, public=False))
        bus.publish(Event("example.changed", {"uid": "i1", "text": "Grüße"}, public=True))
        seen = read_until(response.iter_lines(), lambda s: "event: example.changed" in s and s[-1] == "")
    assert "event: example.secret" not in seen
    data_line = seen[seen.index("event: example.changed") + 1]
    assert json.loads(data_line.removeprefix("data: ")) == {"uid": "i1", "text": "Grüße"}


def test_event_published_from_an_operation_arrives_over_sse(server: RunningServer) -> None:
    with httpx.Client(timeout=10) as client, client.stream("GET", server.base_url + "/api/core/events") as response:
        wait_for_clients(server, 1)
        threading.Thread(
            target=lambda: httpx.post(server.base_url + "/api/example/ping", json={"message": "hi"}), daemon=True
        ).start()
        seen = read_until(response.iter_lines(), lambda s: "event: example.ping" in s and s[-1] == "")
    assert 'data: {"message":"hi"}' in seen
    assert "event: example.secret" not in seen


def test_keep_alive_is_sent_when_idle(server: RunningServer) -> None:
    with httpx.Client(timeout=10) as client, client.stream("GET", server.base_url + "/api/core/events") as response:
        seen = read_until(response.iter_lines(), lambda s: ": keep-alive" in s)
    assert ": connected" in seen


def test_client_disconnect_unregisters_and_shutdown_closes_streams(server: RunningServer) -> None:
    hub = server.app.state.hub
    with httpx.Client(timeout=10) as client:
        with client.stream("GET", server.base_url + "/api/core/events") as response:
            wait_for_clients(server, 1)
            next(iter(response.iter_lines()))
        deadline = time.time() + 5
        while hub.client_count and time.time() < deadline:
            time.sleep(0.02)
    assert hub.client_count == 0

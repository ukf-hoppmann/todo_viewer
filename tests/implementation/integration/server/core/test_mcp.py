from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx2 as httpx
from mcp import Client
from running_server import RunningServer


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_tools_are_listed_with_description_and_schema(server: RunningServer) -> None:
    async def scenario() -> Any:
        async with Client(server.base_url + "/mcp") as client:
            return await client.list_tools()

    tools = {t.name: t for t in run(scenario()).tools}
    assert set(tools) == {
        "example_greet",
        "example_list_items",
        "example_retitle",
        "example_ping",
        "core_health",
        "core_sync_status",
        "core_sync_preview",
        "core_sync_execute",
    }
    greet = tools["example_greet"]
    assert greet.description == "Grüßt jemanden"
    assert set(greet.input_schema["properties"]) == {"name", "shout"} and greet.input_schema["required"] == ["name"]
    assert greet.annotations is not None and greet.annotations.read_only_hint is True
    assert tools["example_retitle"].annotations.read_only_hint is False


def test_tool_call_returns_json_text(server: RunningServer) -> None:
    async def scenario() -> Any:
        async with Client(server.base_url + "/mcp") as client:
            greet = await client.call_tool("example_greet", {"name": "Ada", "shout": True})
            items = await client.call_tool("example_list_items", {})
            return greet, items

    greet, items = run(scenario())
    assert not greet.is_error and json.loads(greet.content[0].text) == {"text": "HALLO ADA"}
    assert json.loads(items.content[0].text) == [{"uid": "i1", "title": "Erstes", "version": 1}]


def test_domain_error_arrives_with_the_same_code_as_over_http(server: RunningServer) -> None:
    args = {"uid": "zzz", "title": "x", "version": 1}

    async def scenario() -> Any:
        async with Client(server.base_url + "/mcp") as client:
            return await client.call_tool("example_retitle", args)

    result = run(scenario())
    http = httpx.put(server.base_url + "/api/example/items/zzz", json={"title": "x", "version": 1})
    assert result.is_error
    assert json.loads(result.content[0].text) == http.json()
    assert http.json()["code"] == "not_found"


def test_invalid_arguments_and_unknown_tools_are_errors_with_codes(server: RunningServer) -> None:
    async def scenario() -> Any:
        async with Client(server.base_url + "/mcp") as client:
            bad = await client.call_tool("example_greet", {})
            unknown = await client.call_tool("example_nope", {})
            return bad, unknown

    bad, unknown = run(scenario())
    assert bad.is_error and json.loads(bad.content[0].text)["code"] == "validation_error"
    assert unknown.is_error and json.loads(unknown.content[0].text)["code"] == "not_found"


def test_tool_that_publishes_events_reaches_the_event_bus(server: RunningServer) -> None:
    seen: list[str] = []
    server.app.state.events.subscribe("example.*", lambda e: seen.append(e.topic))

    async def scenario() -> None:
        async with Client(server.base_url + "/mcp") as client:
            await client.call_tool("example_ping", {"message": "hi"})

    run(scenario())
    assert seen == ["example.ping", "example.secret"]

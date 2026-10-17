"""MCP-Host: macht aus den Operationen der Plugins (`mcp=True`) MCP-Tools `<owner>_<name>`.

Eingabe-Schema und Prüfung nutzen dieselben Dataclasses (`pydantic.TypeAdapter`) wie die HTTP-Routen, der Aufruf
läuft über denselben `PluginHost.call`. Fehler kommen mit demselben `code` an wie über HTTP.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass
from typing import Any

import structlog
from mcp.server import Server, ServerRequestContext
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import (
    CallToolRequestParams,
    CallToolResult,
    ListToolsResult,
    PaginatedRequestParams,
    TextContent,
    Tool,
    ToolAnnotations,
)
from pydantic import TypeAdapter, ValidationError
from starlette.routing import Route

from viewer.core.application.plugin import PluginHost
from viewer.core.domain.errors import DomainError
from viewer.core.domain.operations import Operation

log = structlog.get_logger(__name__)

MCP_PATH = "/mcp"


@dataclass(frozen=True)
class McpTool:
    name: str
    owner: str
    operation: Operation
    input_adapter: TypeAdapter[Any]
    output_adapter: TypeAdapter[Any]

    def describe(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.operation.summary,
            input_schema=self.input_adapter.json_schema(),
            annotations=ToolAnnotations(read_only_hint=self.operation.kind == "read"),
        )


def tool_name(owner: str, operation: Operation) -> str:
    return f"{owner.replace('-', '_')}_{operation.name}"


def build_tools(host: PluginHost) -> dict[str, McpTool]:
    tools: dict[str, McpTool] = {}
    for plugin in host.plugins:
        owner = plugin.definition.id
        for op in plugin.definition.operations:
            if op.mcp:
                name = tool_name(owner, op)
                tools[name] = McpTool(name, owner, op, TypeAdapter(op.input), TypeAdapter(op.output))
    return tools


def _error(code: str, message: str, details: dict[str, Any] | None = None) -> CallToolResult:
    body = json.dumps({"code": code, "message": message, "details": details or {}}, ensure_ascii=False)
    return CallToolResult(content=[TextContent(text=body)], is_error=True)


def build_mcp_server(host: PluginHost) -> Server[Any]:
    tools = build_tools(host)

    async def on_list_tools(ctx: ServerRequestContext[Any], params: PaginatedRequestParams | None) -> ListToolsResult:
        return ListToolsResult(tools=[t.describe() for t in tools.values()])

    async def on_call_tool(ctx: ServerRequestContext[Any], params: CallToolRequestParams) -> CallToolResult:
        tool = tools.get(params.name)
        if tool is None:
            return _error("not_found", f"Tool {params.name} gibt es nicht", {"name": params.name})
        try:
            payload = tool.input_adapter.validate_python(params.arguments or {})
        except ValidationError as exc:
            errors = json.loads(exc.json(include_url=False, include_context=False))
            return _error("validation_error", "Ungültige Argumente", {"errors": errors})
        try:
            result = await host.call(tool.owner, tool.operation.name, payload)
            text = tool.output_adapter.dump_json(result).decode()
        except DomainError as exc:
            return _error(exc.code, exc.message, exc.details)
        except Exception:
            log.exception("mcp_tool_failed", tool=params.name)
            return _error("internal_error", "Interner Fehler")
        return CallToolResult(content=[TextContent(text=text)])

    return Server("todo-viewer", on_list_tools=on_list_tools, on_call_tool=on_call_tool)


@dataclass(frozen=True)
class McpHost:
    route: Route
    lifespan: AbstractAsyncContextManager[None]


def create_mcp_host(host: PluginHost, allowed_hosts: tuple[str, ...] = ()) -> McpHost:
    """Route `/mcp` (Streamable HTTP) und der Lebenszyklus des Session-Managers, den die App im Lifespan startet."""
    server = build_mcp_server(host)
    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*", "todo.localhost:*", *allowed_hosts],
        allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*", "http://todo.localhost:*"],
    )
    mcp_app = server.streamable_http_app(streamable_http_path=MCP_PATH, transport_security=security)
    route = next(r for r in mcp_app.routes if isinstance(r, Route) and r.path == MCP_PATH)

    @asynccontextmanager
    async def lifespan() -> AsyncIterator[None]:
        manager: StreamableHTTPSessionManager = server.session_manager
        async with manager.run():
            yield

    return McpHost(route, lifespan())

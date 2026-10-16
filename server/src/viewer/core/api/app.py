"""FastAPI-App des Core: Plugin-Operationen, Health, SSE, Fehlerformat, OpenAPI."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from viewer.core.api.errors import register_error_handlers
from viewer.core.api.middleware import RequestIdMiddleware
from viewer.core.api.routes import register_operations
from viewer.core.api.sse import SseHub
from viewer.core.application.plugin import PluginHost

Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


class Health(BaseModel):
    status: str


def create_http_app(host: PluginHost, hub: SseHub, *, lifespan: Lifespan | None = None) -> FastAPI:
    app = FastAPI(title="ToDo Viewer", version="0.0.0", lifespan=lifespan)
    app.add_middleware(RequestIdMiddleware)
    register_error_handlers(app)

    @app.get("/api/core/health", response_model=Health, tags=["core"], operation_id="core_health")
    async def health() -> Health:
        return Health(status="ok")

    @app.get(
        "/api/core/events",
        tags=["core"],
        operation_id="core_events",
        summary="Server-Sent Events: öffentliche Ereignisse (`event: <topic>`, `data: <json>`)",
        response_class=StreamingResponse,
        responses={200: {"content": {"text/event-stream": {"schema": {"type": "string"}}}}},
    )
    async def events() -> StreamingResponse:
        return StreamingResponse(
            hub.stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    register_operations(app, host)
    app.openapi = lambda: _openapi(app)  # type: ignore[method-assign]
    return app


def _openapi(app: FastAPI) -> dict[str, Any]:
    """OpenAPI ohne FastAPIs `HTTPValidationError`: Fehler haben überall das Format `ErrorBody` (Antwort `4XX`)."""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    components = schema.get("components", {}).get("schemas", {})
    for name in ("HTTPValidationError", "ValidationError"):
        components.pop(name, None)
    app.openapi_schema = schema
    return schema

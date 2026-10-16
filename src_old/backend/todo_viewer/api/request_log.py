"""One log line per request: method, path, status, duration, plus what handlers noted on the way.

Level by outcome: 5xx ERROR (with stack trace), 4xx WARNING, other writes INFO, reads and
UI-state saves DEBUG.
The request id is bound as a context variable, so every line logged while serving the request
carries it (`req=`), including lines from the infrastructure.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any

import structlog
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

log = structlog.get_logger(__name__)

READ_METHODS = {"GET", "HEAD", "OPTIONS"}
# Writes that change no backlog and happen on every filter change in the UI.
QUIET_PATHS = {"/api/v2/ui-state"}


def note(request: Request, **fields: Any) -> None:
    """Adds fields to the request's log line (e.g. the id of a created item, an error code)."""
    # A shared dict, not a context variable: sync endpoints run in a copied context,
    # so context changes made there would not reach the middleware.
    target = request.scope.get("state", {}).get("log")
    if target is not None:
        target.update(fields)


class RequestLogMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        fields: dict[str, Any] = {}
        scope.setdefault("state", {})["log"] = fields
        status = 500
        started = time.perf_counter()

        async def send_with_status(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        with structlog.contextvars.bound_contextvars(req=uuid.uuid4().hex[:8]):
            try:
                await self.app(scope, receive, send_with_status)
            except Exception as exc:
                self._log(scope, 500, started, {**fields, "exc_info": exc})
                raise
            self._log(scope, status, started, fields)

    @staticmethod
    def _log(scope: Scope, status: int, started: float, fields: dict[str, Any]) -> None:
        method = scope["method"]
        if status >= 500:
            level = logging.ERROR
        elif status >= 400:
            level = logging.WARNING
        elif method not in READ_METHODS and scope["path"] not in QUIET_PATHS:
            level = logging.INFO
        else:
            level = logging.DEBUG
        query = scope.get("query_string", b"").decode("latin-1")
        log.log(level, "request", method=method, path=scope["path"], **({"query": query} if query else {}),
                status=status, ms=round((time.perf_counter() - started) * 1000), **fields)

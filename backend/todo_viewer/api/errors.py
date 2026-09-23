"""The single place where domain errors become HTTP responses."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from todo_viewer.domain.errors import ConflictError, DomainError, ForbiddenError, NotFoundError

V2_PREFIX = "/api/v2/"


def error_response(code: str, message: str, status: int = 400, **extra: Any) -> JSONResponse:
    """Legacy error body: {"error": message, "code": code, ...details}."""
    return JSONResponse({"error": message, "code": code, **extra}, status_code=status)


def v2_error_response(code: str, message: str, status: int, details: dict[str, str]) -> JSONResponse:
    return JSONResponse({"code": code, "message": message, "details": details}, status_code=status)


def status_for(exc: DomainError, v2: bool) -> int:
    if isinstance(exc, NotFoundError):
        return 404
    if isinstance(exc, ForbiddenError):
        return 403
    if isinstance(exc, ConflictError) and v2:
        return 409
    return 400


def _is_v2(request: Request) -> bool:
    return request.url.path.startswith(V2_PREFIX)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError) -> JSONResponse:
        v2 = _is_v2(request)
        if v2:
            return v2_error_response(exc.code, exc.message, status_for(exc, v2), exc.details)
        return error_response(exc.code, exc.message, status_for(exc, v2), **exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        where = ".".join(str(p) for p in first.get("loc", ()) if p != "body")
        message = f"invalid request: {where} {first.get('msg', '')}".strip()
        if _is_v2(request):
            return v2_error_response("bad_request", message, 400, {"field": where})
        return error_response("bad_request", message)

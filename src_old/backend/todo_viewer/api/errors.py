"""The single place where domain errors become HTTP responses: {code, message, details}."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from todo_viewer.domain.errors import ConflictError, DomainError, ForbiddenError, NotFoundError

from .request_log import note


def error_response(code: str, message: str, status: int, details: dict[str, str]) -> JSONResponse:
    return JSONResponse({"code": code, "message": message, "details": details}, status_code=status)


def status_for(exc: DomainError) -> int:
    if isinstance(exc, NotFoundError):
        return 404
    if isinstance(exc, ForbiddenError):
        return 403
    if isinstance(exc, ConflictError):
        return 409
    return 400


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError) -> JSONResponse:
        note(request, code=exc.code, message=exc.message, details=exc.details)
        return error_response(exc.code, exc.message, status_for(exc), exc.details)

    @app.exception_handler(OSError)
    async def os_error(request: Request, exc: OSError) -> JSONResponse:
        # e.g. no write permission on a backlog folder
        note(request, code="write_failed", message=str(exc), exc_info=exc)
        return error_response("write_failed", str(exc), 500, {})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        where = ".".join(str(p) for p in first.get("loc", ()) if p != "body")
        message = f"invalid request: {where} {first.get('msg', '')}".strip()
        note(request, code="bad_request", message=message, details={"field": where})
        return error_response("bad_request", message, 400, {"field": where})

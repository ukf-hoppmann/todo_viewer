"""Umwandlung von `DomainError` in HTTP-Antworten `{code, message, details}` (nur hier)."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from viewer.core.domain.errors import DomainError

log = structlog.get_logger(__name__)

STATUS_BY_CODE: dict[str, int] = {
    "not_found": 404,
    "version_conflict": 409,
    "mirror_conflict": 409,
    "mirror_blocked": 409,
    "invalid_input": 422,
    "validation_error": 422,
    "config_invalid": 500,
}
_STATUS_CODES: dict[int, str] = {404: "not_found", 405: "method_not_allowed"}


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = {}


def error_response(status: int, code: str, message: str, details: dict[str, Any] | None = None) -> JSONResponse:
    body = ErrorBody(code=code, message=message, details=details or {})
    return JSONResponse(status_code=status, content=jsonable_encoder(body))


def register_error_handlers(app: FastAPI) -> None:
    async def on_domain_error(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, DomainError)
        return error_response(STATUS_BY_CODE.get(exc.code, 400), exc.code, exc.message, exc.details)

    async def on_validation_error(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, RequestValidationError)
        errors = jsonable_encoder(exc.errors(), custom_encoder={Exception: str})
        return error_response(422, "validation_error", "Ungültige Anfrage", {"errors": errors})

    async def on_http_exception(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, StarletteHTTPException)
        code = _STATUS_CODES.get(exc.status_code, "http_error")
        return error_response(exc.status_code, code, str(exc.detail))

    async def on_unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_error", path=request.url.path)
        return error_response(500, "internal_error", "Interner Fehler")

    app.add_exception_handler(DomainError, on_domain_error)
    app.add_exception_handler(RequestValidationError, on_validation_error)
    app.add_exception_handler(StarletteHTTPException, on_http_exception)
    app.add_exception_handler(Exception, on_unhandled)

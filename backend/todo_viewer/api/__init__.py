"""HTTP layer (FastAPI). Translates requests into service calls and results into JSON."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send

from todo_viewer.application.container import Container

from . import v2
from .errors import install_error_handlers
from .request_log import RequestLogMiddleware


def create_app(container: Container, frontend_dir: Path) -> FastAPI:
    app = FastAPI(title="ToDo Viewer", version="2.0")
    app.state.container = container
    install_error_handlers(app)
    app.add_middleware(RequestLogMiddleware)
    app.include_router(v2.router)
    app.include_router(v2.notes_router)
    # Mounted last: everything that is not an API route is a frontend file.
    app.mount("/", FrontendFiles(frontend_dir), name="frontend")
    return app


class FrontendFiles(StaticFiles):
    """The built frontend; checked per request, so a later `npm run build` needs no restart."""

    def __init__(self, directory: Path):
        super().__init__(directory=directory, html=True, check_dir=False)
        self._index = directory / "index.html"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not self._index.is_file():
            message = f"Frontend not built ({self._index.parent}): run `npm --prefix web run build`."
            await PlainTextResponse(message, 503)(scope, receive, send)
            return
        await super().__call__(scope, receive, send)

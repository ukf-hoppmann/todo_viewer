"""HTTP layer (FastAPI). Translates requests into service calls and results into JSON."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from todo_viewer.application.container import Container

from . import v2
from .errors import install_error_handlers
from .legacy import items, misc, sources


def create_app(container: Container, frontend_dir: Path) -> FastAPI:
    app = FastAPI(title="ToDo Viewer", version="2.0")
    app.state.container = container
    install_error_handlers(app)
    app.include_router(v2.router)
    # Legacy API for the old frontend; removed together with it.
    for module in (items, sources, misc):
        app.include_router(module.router)
    # Registered last: everything that is not an API route is a frontend file.
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    return app

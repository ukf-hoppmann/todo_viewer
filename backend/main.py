"""Entry point: `python backend/main.py` (HOST, PORT, DEV_RELOAD from the environment)."""
from __future__ import annotations

import os

import uvicorn

from todo_viewer.api import create_app
from todo_viewer.bootstrap import Settings, build_container

settings = Settings.from_env()
app = create_app(build_container(settings), settings.frontend_dir)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5411")),
        reload=os.environ.get("DEV_RELOAD", "1") == "1",
        app_dir=os.path.dirname(os.path.abspath(__file__)),
    )

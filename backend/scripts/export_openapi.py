"""Writes the OpenAPI schema of API v2 to web/src/api/openapi.json (input for the TS types)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI  # noqa: E402

from todo_viewer.api import v2  # noqa: E402
from todo_viewer.bootstrap import PROJECT_ROOT  # noqa: E402

TARGET = PROJECT_ROOT / "web" / "src" / "api" / "openapi.json"


def v2_schema() -> dict[str, Any]:
    app = FastAPI(title="ToDo Viewer API", version="2")
    app.include_router(v2.router)
    return app.openapi()


def render() -> str:
    return json.dumps(v2_schema(), indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    TARGET.write_text(render(), encoding="utf-8")
    print(f"wrote {TARGET}")

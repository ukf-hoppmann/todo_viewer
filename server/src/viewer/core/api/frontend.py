"""Liefert das gebaute Frontend (`client/dist`) unter `/` aus, mit `index.html` für Adressen der Oberfläche.

Die API liegt unter `/api`, MCP unter `/mcp`; beide Routen stehen vor dieser. Unter `/api` und `/mcp` gibt es nie
die `index.html`: eine unbekannte Adresse dort ist ein 404 im Fehlerformat der API.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, Response

RESERVED = ("api", "mcp")
IMMUTABLE = "public, max-age=31536000, immutable"


def add_frontend(app: FastAPI, directory: Path) -> bool:
    """Hängt die Auslieferung an, wenn `directory/index.html` besteht; gibt zurück, ob es geschah."""
    root = directory.resolve()
    index = root / "index.html"
    if not index.is_file():
        return False

    async def frontend(path: str) -> Response:
        if path.split("/", 1)[0] in RESERVED:
            return JSONResponse(
                {"code": "not_found", "message": f"/{path} gibt es nicht", "details": {"path": f"/{path}"}},
                status_code=404,
            )
        candidate = (root / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(root):
            headers = {"Cache-Control": IMMUTABLE} if path.startswith("assets/") else {}
            return FileResponse(candidate, headers=headers)
        if path.startswith("assets/"):
            # A page from an older build asks for a file that no longer exists: a 404 lets the client notice it.
            return JSONResponse(
                {"code": "not_found", "message": f"/{path} gibt es nicht", "details": {"path": f"/{path}"}},
                status_code=404,
            )
        return FileResponse(index, headers={"Cache-Control": "no-cache"})

    app.add_api_route("/{path:path}", frontend, methods=["GET"], include_in_schema=False)
    return True

"""Architektur §3: Die TypeScript-Typen der API werden aus dem OpenAPI-Schema erzeugt, nie von Hand.

Der Test erzeugt die Typen neu und vergleicht sie mit `client/src/shared/api/schema.d.ts`. Weicht die Datei ab,
fehlt ein Lauf von `scripts/gen-api.sh` (oder jemand hat sie von Hand geändert).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import cast

import pytest
from viewer.app.openapi import openapi_schema

ROOT = Path(__file__).resolve().parents[4]
GENERATOR = ROOT / "client" / "node_modules" / ".bin" / "openapi-typescript"
COMMITTED = ROOT / "client" / "src" / "shared" / "api" / "schema.d.ts"


@pytest.mark.skipif(not GENERATOR.exists(), reason="client/node_modules fehlt (cd client && npm ci)")
def test_committed_api_types_match_the_openapi_schema(tmp_path: Path) -> None:
    schema_file = tmp_path / "openapi.json"
    schema_file.write_text(
        json.dumps(openapi_schema(), indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    generated = tmp_path / "schema.d.ts"

    subprocess.run(
        [str(GENERATOR), str(schema_file), "-o", str(generated)], check=True, capture_output=True, cwd=tmp_path
    )

    assert generated.read_text(encoding="utf-8") == COMMITTED.read_text(encoding="utf-8"), (
        "client/src/shared/api/schema.d.ts ist veraltet: scripts/gen-api.sh ausführen"
    )


def test_every_core_route_is_in_the_schema() -> None:
    paths = set(cast(dict[str, object], openapi_schema()["paths"]))
    assert {"/api/core/health", "/api/core/events", "/api/core/ui-state/{owner}"} <= paths

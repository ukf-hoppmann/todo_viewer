"""The committed OpenAPI file is the source of the frontend's TS types; it must not drift."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import export_openapi  # noqa: E402


def test_openapi_file_is_up_to_date():
    assert export_openapi.TARGET.read_text(encoding="utf-8") == export_openapi.render(), (
        "API v2 changed: run `python backend/scripts/export_openapi.py` and `npm run gen:api` in web/"
    )

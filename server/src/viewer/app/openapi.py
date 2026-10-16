"""Gibt das OpenAPI-Schema des Servers als JSON aus: `python -m viewer.app.openapi`.

Daraus entstehen die TypeScript-Typen des Clients (`scripts/gen-api.sh`). Der Server wird dafür mit einer
leeren, temporären Datenbank gebaut und nicht gestartet.
"""

from __future__ import annotations

import json
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

import structlog

from viewer.app.composition import PLUGINS, create_app
from viewer.core.application.plugin import PluginDefinition
from viewer.core.domain.settings import Settings


def openapi_schema(plugins: Sequence[PluginDefinition] = PLUGINS) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        settings = Settings(
            db_path=str(root / "viewer.db"), backup_dir=str(root / "backups"), log_dir=str(root / "logs")
        )
        app = create_app(settings, plugins)
        schema = app.openapi()
        app.state.database.dispose()
    return schema


def main() -> int:
    structlog.configure(logger_factory=structlog.PrintLoggerFactory(file=sys.stderr))  # stdout gehört dem JSON
    json.dump(openapi_schema(), sys.stdout, indent=2, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Start des Servers: `python -m viewer.app.main` (Port 5412 laut Konfiguration)."""

from __future__ import annotations

import sys

import structlog
import uvicorn

from viewer.app.composition import create_app
from viewer.core.domain.errors import PluginSetupError
from viewer.core.infrastructure.config import load_settings
from viewer.core.infrastructure.logging import configure_logging


def main() -> int:
    settings = load_settings()
    configure_logging(settings.log_dir, to_stderr=True)
    log = structlog.get_logger("viewer.main")
    try:
        app = create_app(settings)
    except PluginSetupError as exc:
        log.error("plugin_setup_failed", problems=exc.problems)
        print(exc, file=sys.stderr)
        return 1
    log.info("starting", host=settings.host, port=settings.port)
    uvicorn.run(app, host=settings.host, port=settings.port, log_config=None)
    return 0


if __name__ == "__main__":
    sys.exit(main())

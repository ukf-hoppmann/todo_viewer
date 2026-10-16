"""Konfiguration aus `configs/viewer.json` und Umgebungsvariablen (Umgebung gewinnt)."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from viewer.core.domain.errors import DomainError
from viewer.core.domain.settings import Settings

DEFAULT_CONFIG_PATH = Path("configs/viewer.json")


class ConfigError(DomainError):
    code = "config_invalid"


def load_settings(path: Path | None = None, env: Mapping[str, str] | None = None) -> Settings:
    env = os.environ if env is None else env
    config_path = Path(env["VIEWER_CONFIG"]) if "VIEWER_CONFIG" in env else (path or DEFAULT_CONFIG_PATH)
    data = _read(config_path)
    defaults = Settings()
    try:
        plugins = data.get("plugins", {})
        if not isinstance(plugins, dict) or not all(isinstance(v, dict) for v in plugins.values()):
            raise ConfigError(f"'plugins' in {config_path} muss ein Objekt von Objekten sein")
        return Settings(
            host=str(env.get("VIEWER_HOST", data.get("host", defaults.host))),
            port=int(env.get("VIEWER_PORT", data.get("port", defaults.port))),
            log_dir=str(env.get("VIEWER_LOG_DIR", data.get("log_dir", defaults.log_dir))),
            db_path=str(env.get("VIEWER_DB", data.get("db_path", defaults.db_path))),
            backup_dir=str(env.get("VIEWER_BACKUP_DIR", data.get("backup_dir", defaults.backup_dir))),
            sse_keepalive_seconds=float(data.get("sse_keepalive_seconds", defaults.sse_keepalive_seconds)),
            auto_sync_interval_seconds=float(
                env.get(
                    "AUTO_SYNC_INTERVAL", data.get("auto_sync_interval_seconds", defaults.auto_sync_interval_seconds)
                )
            ),
            plugins=plugins,
        )
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Ungültiger Wert in der Konfiguration: {exc}") from exc


def _read(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Konfiguration {path} nicht lesbar: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Konfiguration {path} muss ein JSON-Objekt sein")
    return data

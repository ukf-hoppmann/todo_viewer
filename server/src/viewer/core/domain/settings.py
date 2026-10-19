"""Konfiguration des Core als reiner Datentyp (gelesen wird in `infrastructure`)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 5411
    log_dir: str = "logs"
    db_path: str = "configs/viewer.db"
    backup_dir: str = "configs/backups"
    #: Das gebaute Frontend; besteht der Ordner nicht, liefert der Server nur die API.
    static_dir: str = "client/dist"
    sse_keepalive_seconds: float = 15.0
    auto_sync_interval_seconds: float = 30.0
    plugins: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)

    def for_plugin(self, plugin_id: str) -> Mapping[str, Any]:
        return self.plugins.get(plugin_id, {})

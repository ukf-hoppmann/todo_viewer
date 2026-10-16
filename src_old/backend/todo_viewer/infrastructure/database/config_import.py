"""Takes over what earlier versions kept in JSON files: the sources in config.json and ui_state.json.

Runs before every access to projects or UI state and does nothing once the files are taken over. Sources
that appear in config.json again later are taken over too (markdown folders already known are skipped).
"""
from __future__ import annotations

import dataclasses
import threading
import uuid
from collections.abc import Callable

import sqlalchemy as sa
import structlog

from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.config import JsonFile, JsonSourceRepository, JsonUiStateStore, LegacySourceMigrator

from .engine import Database
from .schema import items, projects, ui_state
from .sources import read_sources, write_sources
from .ui_state import save_ui_state

log = structlog.get_logger(__name__)

MARKDOWN = "markdown"


def new_project_id() -> str:
    return str(uuid.uuid4())


class LegacyConfigImport:
    def __init__(self, db: Database, config: JsonFile, ui_state_file: JsonFile,
                 new_id: Callable[[], str] = new_project_id):
        self._db = db
        self._config = config
        self._ui_state = ui_state_file
        self._new_id = new_id
        self._lock = threading.Lock()

    def sources(self) -> None:
        """Moves `sources` from config.json into the database; config.json keeps everything else."""
        with self._lock:
            if not self._config.exists() or "sources" not in self._config.read():
                return
            original = self._config.path.read_text(encoding="utf-8")
            legacy = JsonSourceRepository(self._config, LegacySourceMigrator()).all()
            with self._db.begin() as conn:
                current = read_sources(conn)
                known = {s.path for s in current if s.backend == MARKDOWN}
                taken = [self._take_over(conn, s) for s in legacy if s.backend != MARKDOWN or s.path not in known]
                write_sources(conn, current, current + taken)
            self._config.path.with_name(f"{self._config.path.name}.bak").write_text(original, encoding="utf-8")
            rest = {k: v for k, v in self._config.read().items() if k != "sources"}
            self._config.write(rest)
            log.info("sources_taken_over", count=len(taken), skipped=len(legacy) - len(taken))

    def ui_state(self) -> None:
        """Moves ui_state.json into the database unless it has a UI state already, then renames the file."""
        with self._lock:
            if not self._ui_state.exists():
                return
            state = JsonUiStateStore(self._ui_state).load()
            with self._db.begin() as conn:
                if conn.execute(sa.select(ui_state.c.id)).first() is None:
                    save_ui_state(conn, state)
            self._ui_state.path.replace(self._ui_state.path.with_name(f"{self._ui_state.path.name}.bak"))
            log.info("ui_state_taken_over")

    def _take_over(self, conn: sa.Connection, source: Source) -> Source:
        """The source with a new id; a database project's items move from its old path-based id."""
        new_id = self._new_id()
        if source.backend == MARKDOWN:
            return dataclasses.replace(source, id=new_id)
        taken = dataclasses.replace(source, id=new_id, path="")
        conn.execute(sa.insert(projects).values(id=new_id))
        conn.execute(sa.update(items).where(items.c.project_id == source.id).values(project_id=new_id))
        conn.execute(sa.delete(projects).where(projects.c.id == source.id))
        return taken

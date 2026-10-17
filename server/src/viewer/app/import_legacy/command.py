"""Der Befehl `python -m viewer.app.import_legacy`: alte Datenbank prüfen, sichern, übernehmen, berichten."""

from __future__ import annotations

import argparse
import sqlite3
import sys
import tempfile
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from viewer.app.composition import create_app
from viewer.app.import_legacy.reader import LegacyError, read_legacy
from viewer.app.import_legacy.report import Report
from viewer.app.import_legacy.validate import validate
from viewer.app.import_legacy.writer import Importer
from viewer.core.domain.settings import Settings
from viewer.core.infrastructure.clock import SystemClock
from viewer.core.infrastructure.database import SqliteBackupMaker, SqliteDatabase


def _target_in_use(target: Path) -> str | None:
    """Warum das Ziel nicht leer ist, sonst `None`: es darf nur das eingebaute Projekt und keine Elemente enthalten."""
    if not target.is_file():
        return None
    connection = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "workspace_elements" not in tables:
            return None
        elements = connection.execute("SELECT COUNT(*) FROM workspace_elements").fetchone()[0]
        others = connection.execute("SELECT COUNT(*) FROM workspace_projects WHERE position > 0").fetchone()[0]
    finally:
        connection.close()
    return f"{elements} Elemente, {others} weitere Projekte" if elements or others else None


def import_legacy(
    legacy_db: Path,
    target: Path,
    *,
    dry_run: bool = False,
    backup_dir: Path = Path("configs/backups"),
    now: datetime | None = None,
) -> Report:
    """Übernimmt die alte Datenbank in `target` (eine neue oder eine ohne Inhalt). Gibt den Bericht zurück; wirft
    `LegacyError`, wenn nichts übernommen werden darf. Ein Probelauf schreibt in eine Wegwerf-Kopie."""
    legacy = read_legacy(legacy_db)
    validate(legacy)
    used = _target_in_use(target)
    if used is not None:
        raise LegacyError(f"Die Zieldatenbank ist nicht leer ({used}): {target}")
    moment = (now or datetime.now(UTC)).isoformat()
    report = Report()
    with tempfile.TemporaryDirectory() as scratch:
        work = Path(scratch) / "viewer.db" if dry_run else target
        if not dry_run:
            work.parent.mkdir(parents=True, exist_ok=True)
            if work.is_file():
                backup = SqliteDatabase(work)
                try:
                    SqliteBackupMaker(backup, backup_dir, SystemClock()).create("import")
                finally:
                    backup.dispose()
        settings = Settings(
            db_path=str(work), backup_dir=str(Path(scratch) / "backups" if dry_run else backup_dir), log_dir=scratch
        )
        app = create_app(settings)
        database = app.state.database
        try:
            with database.transaction() as tx:
                Importer(legacy, tx, report, moment).run()
        finally:
            database.dispose()
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m viewer.app.import_legacy", description=__doc__)
    parser.add_argument("--legacy-db", type=Path, default=Path("configs/todo.db"))
    parser.add_argument("--target", type=Path, default=Path("configs/viewer.db"))
    parser.add_argument("--backup-dir", type=Path, default=Path("configs/backups"))
    parser.add_argument("--log-dir", type=Path, default=Path("logs"))
    parser.add_argument("--dry-run", action="store_true", help="alles prüfen und berichten, nichts schreiben")
    args = parser.parse_args(argv)
    now = datetime.now(UTC)
    try:
        report = import_legacy(args.legacy_db, args.target, dry_run=args.dry_run, backup_dir=args.backup_dir, now=now)
    except LegacyError as exc:
        print(exc, file=sys.stderr)
        return 1
    text = report.render(dry_run=args.dry_run)
    sys.stdout.write(text)
    if not args.dry_run:
        args.log_dir.mkdir(parents=True, exist_ok=True)
        (args.log_dir / f"import-{now.strftime('%Y%m%dT%H%M%SZ')}.log").write_text(text, encoding="utf-8")
    return 0

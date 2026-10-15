"""Names and retention of the automatic backups of the central database."""
from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import datetime

# How many automatic backups are kept; older ones are removed when a new one is made.
KEEP_AUTOMATIC = 10
REASON_MIGRATION = "migration"
REASON_SYNC = "sync"

_NAME = re.compile(rf"^todo-(\d{{8}}-\d{{6}})-({REASON_MIGRATION}|{REASON_SYNC})(?:-(\d+))?\.db$")


def backup_file_name(at: datetime, reason: str, attempt: int = 1) -> str:
    """`todo-<JJJJMMTT-HHMMSS>-<reason>.db`; a further backup of the same second gets `-<attempt>` (from 2)."""
    suffix = f"-{attempt}" if attempt > 1 else ""
    return f"todo-{at.strftime('%Y%m%d-%H%M%S')}-{reason}{suffix}.db"


def backups_to_remove(names: Iterable[str], keep: int = KEEP_AUTOMATIC) -> list[str]:
    """The oldest automatic backups beyond the newest `keep`. Names of any other pattern are never returned."""
    automatic = []
    for name in names:
        found = _NAME.match(name)
        if found:
            automatic.append(((found.group(1), int(found.group(3) or 1)), name))
    automatic.sort()
    return [name for _, name in automatic[: max(len(automatic) - keep, 0)]]

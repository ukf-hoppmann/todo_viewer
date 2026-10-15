"""Names and retention of the automatic backups of the central database."""
from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import datetime, timedelta

# How many automatic backups are kept; older ones are removed when a new one is made.
KEEP_AUTOMATIC = 10
REASON_MIGRATION = "migration"
REASON_SYNC = "sync"
REASON_AUTO = "auto"  # a run of the automatic sync
# With a clock, the newest backup of each of the last days is kept as well, so frequent runs do not push out older ones.
KEEP_DAYS = 14
# An automatic run does not make a new backup while one this young exists.
AUTO_INTERVAL = timedelta(hours=1)

_NAME = re.compile(rf"^todo-(\d{{8}}-\d{{6}})-({REASON_MIGRATION}|{REASON_SYNC}|{REASON_AUTO})(?:-(\d+))?\.db$")


def backup_file_name(at: datetime, reason: str, attempt: int = 1) -> str:
    """`todo-<JJJJMMTT-HHMMSS>-<reason>.db`; a further backup of the same second gets `-<attempt>` (from 2)."""
    suffix = f"-{attempt}" if attempt > 1 else ""
    return f"todo-{at.strftime('%Y%m%d-%H%M%S')}-{reason}{suffix}.db"


def backups_to_remove(names: Iterable[str], keep: int = KEEP_AUTOMATIC, now: datetime | None = None) -> list[str]:
    """The oldest automatic backups beyond the newest `keep`, except (given `now`) the newest of each of the last
    `KEEP_DAYS` days. Names of any other pattern are never returned."""
    automatic = []
    for name in names:
        found = _NAME.match(name)
        if found:
            automatic.append(((found.group(1), int(found.group(3) or 1)), name))
    automatic.sort()
    candidates = automatic[: max(len(automatic) - keep, 0)]
    if now is None:
        return [name for _, name in candidates]
    since = (now - timedelta(days=KEEP_DAYS)).strftime("%Y%m%d")
    newest_of_day = {key[0][:8]: name for key, name in automatic if key[0][:8] > since}
    protected = set(newest_of_day.values())
    return [name for _, name in candidates if name not in protected]


def recent_backup(names: Iterable[str], now: datetime) -> str | None:
    """The newest automatic backup made within `AUTO_INTERVAL` before `now`, if any."""
    stamps = []
    for name in names:
        found = _NAME.match(name)
        if found:
            stamps.append(((found.group(1), int(found.group(3) or 1)), name))
    if not stamps:
        return None
    key, name = max(stamps)
    made = datetime.strptime(key[0], "%Y%m%d-%H%M%S")
    return name if timedelta(0) <= now - made < AUTO_INTERVAL else None

"""Names and retention of the automatic database backups."""
from __future__ import annotations

from datetime import datetime

from todo_viewer.domain.database_backup import KEEP_AUTOMATIC, backup_file_name, backups_to_remove


def test_the_name_has_the_time_and_the_reason():
    at = datetime(2026, 10, 14, 15, 27, 48)

    assert backup_file_name(at, "sync") == "todo-20261014-152748-sync.db"
    assert backup_file_name(at, "migration") == "todo-20261014-152748-migration.db"


def test_a_second_backup_in_the_same_second_gets_a_number():
    at = datetime(2026, 10, 14, 15, 27, 48)

    assert backup_file_name(at, "sync", attempt=2) == "todo-20261014-152748-sync-2.db"


def _name(second: int, reason: str = "sync") -> str:
    return backup_file_name(datetime(2026, 10, 14, 15, 0, second), reason)


def test_the_newest_ten_automatic_backups_are_kept():
    names = [_name(s, "sync" if s % 2 else "migration") for s in range(11)]

    assert backups_to_remove(names) == [_name(0, "migration")]
    assert KEEP_AUTOMATIC == 10


def test_nothing_is_removed_up_to_the_limit():
    assert backups_to_remove([_name(s) for s in range(10)]) == []


def test_files_that_are_not_automatic_backups_are_never_removed():
    manual = ["todo-20261014-152748-vor-notes-sync.db", "notes.txt", "todo.db", "todo-20261014-152748-sync.db.partial"]

    assert backups_to_remove([*manual, *(_name(s) for s in range(12))]) == [_name(0), _name(1)]


def test_the_number_of_the_attempt_orders_backups_of_one_second():
    at = datetime(2026, 10, 14, 15, 0, 0)
    names = [backup_file_name(at, "sync", n) for n in range(1, 12)]

    assert backups_to_remove(names) == [names[0]]


# --- automatic syncs: at most one backup an hour, retention by age (STORY-059) ---

from todo_viewer.domain.database_backup import KEEP_DAYS, recent_backup  # noqa: E402

NOW = datetime(2026, 10, 14, 12, 0, 0)


def _at(day: int, hour: int, reason: str = "auto") -> str:
    return backup_file_name(datetime(2026, 10, day, hour, 0, 0), reason)


def test_the_automatic_reason_is_an_automatic_backup_too():
    assert backup_file_name(NOW, "auto") == "todo-20261014-120000-auto.db"
    assert backups_to_remove([_at(1, h) for h in range(11)]) == [_at(1, 0)]


def test_frequent_runs_do_not_push_out_older_days():
    """Twelve backups today would leave only today's; the newest of each of the last 14 days stays as well."""
    today = [_at(14, h) for h in range(1, 12)]
    older = [_at(13, 9), _at(13, 18), _at(10, 7), _at(2, 7)]  # the 2nd is 12 days back
    ancient = [backup_file_name(datetime(2026, 9, 1, 8, 0, 0), "sync")]

    removed = backups_to_remove([*ancient, *older, *today], now=NOW)

    assert sorted(removed) == sorted([*ancient, _at(13, 9), _at(14, 1)])  # 13th: only its newest; today: beyond ten
    assert KEEP_DAYS == 14


def test_without_a_clock_only_the_count_counts():
    assert backups_to_remove([_at(1, 0), *(_at(14, h) for h in range(1, 11))]) == [_at(1, 0)]


def test_a_backup_of_the_last_hour_is_found_whatever_its_reason():
    young = backup_file_name(datetime(2026, 10, 14, 11, 30, 0), "auto")
    names = [_at(14, 10, "sync"), young, "todo-20261014-115900-vor-notes-sync.db"]

    assert recent_backup(names, NOW) == young
    assert recent_backup([_at(14, 10, "sync")], NOW) is None
    assert recent_backup([], NOW) is None

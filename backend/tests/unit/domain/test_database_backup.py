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

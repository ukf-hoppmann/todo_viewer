"""What the central database reports about itself: its type, where it is, and its schema version."""
from __future__ import annotations

from pathlib import Path

from todo_viewer.application.ports import StorageDescription
from todo_viewer.infrastructure.database.engine import Database, describe_url
from todo_viewer.infrastructure.database.migrations import CURRENT_VERSION


def test_a_sqlite_database_reports_its_file_and_schema_version(tmp_path: Path):
    db = Database(f"sqlite:///{tmp_path / 'data' / 'todo.db'}")

    assert db.describe() == StorageDescription(kind="sqlite", location=str(tmp_path / "data" / "todo.db"),
                                               schema_version=CURRENT_VERSION)


def test_the_password_of_a_server_database_is_never_reported():
    kind, location = describe_url("postgresql://todo:s3cret@db.example.org:5432/backlog")

    assert kind == "postgresql"
    assert "s3cret" not in location and "db.example.org" in location and "backlog" in location


def test_an_in_memory_database_has_no_file():
    assert describe_url("sqlite://") == ("sqlite", ":memory:")

"""An existing installation: sources and UI state move from the JSON files into the database on first access."""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import pytest

from todo_viewer.domain.item import Item
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.config import JsonFile, legacy_source_id
from todo_viewer.infrastructure.database import Database, DatabaseBacklogRepository
from todo_viewer.infrastructure.database.config_import import LegacyConfigImport
from todo_viewer.infrastructure.database.sources import DatabaseSourceRepository
from todo_viewer.infrastructure.database.ui_state import DatabaseUiStateStore


class Setup:
    def __init__(self, tmp_path: Path):
        self.dir = tmp_path
        self.db = Database(f"sqlite:///{tmp_path / 'todo.db'}")
        counter = itertools.count(1)
        self.importer = LegacyConfigImport(self.db, JsonFile(tmp_path / "config.json"),
                                           JsonFile(tmp_path / "ui_state.json"), lambda: f"uuid-{next(counter)}")
        self.sources = DatabaseSourceRepository(self.db, self.importer.sources)
        self.ui_state = DatabaseUiStateStore(self.db, self.importer.ui_state)

    def write(self, name: str, data: object) -> None:
        (self.dir / name).write_text(json.dumps(data), encoding="utf-8")

    def read(self, name: str) -> object:
        return json.loads((self.dir / name).read_text(encoding="utf-8"))


@pytest.fixture
def setup(tmp_path: Path) -> Setup:
    return Setup(tmp_path)


CONFIG = {"storage_url": "sqlite:///x.db", "other": "kept", "sources": [
    {"project": "A", "path": "/repos/a/docs"}, {"project": "B", "path": "/repos/b/docs", "color": "red"}]}


def test_sources_and_ui_state_move_into_the_database(setup: Setup):
    setup.write("config.json", CONFIG)
    setup.write("ui_state.json", {"hiddenStatuses": ["Completed"]})

    sources = setup.sources.all()

    assert sources == [Source(project="A", path="/repos/a/docs", id="uuid-1"),
                       Source(project="B", path="/repos/b/docs", id="uuid-2")]
    assert sources[1].extra == {"color": "red"}
    assert setup.read("config.json") == {"storage_url": "sqlite:///x.db", "other": "kept"}
    assert setup.read("config.json.bak") == CONFIG
    assert setup.ui_state.load() == {"hiddenStatuses": ["Completed"]}
    assert not (setup.dir / "ui_state.json").exists()
    assert setup.read("ui_state.json.bak") == {"hiddenStatuses": ["Completed"]}


def test_a_second_start_changes_nothing(setup: Setup):
    setup.write("config.json", CONFIG)
    first = setup.sources.all()

    again = Setup(setup.dir)

    assert again.sources.all() == first
    assert setup.read("config.json.bak") == CONFIG


def test_without_ui_state_file_the_ui_state_is_empty(setup: Setup):
    setup.write("config.json", CONFIG)

    assert setup.ui_state.load() == {}
    assert len(setup.sources.all()) == 2


def test_without_any_config_there_are_no_projects(setup: Setup):
    assert setup.sources.all() == []
    assert not (setup.dir / "config.json").exists()


def test_sources_added_to_config_later_are_taken_over_once(setup: Setup):
    setup.write("config.json", CONFIG)
    setup.sources.all()

    setup.write("config.json", {"sources": [{"project": "A again", "path": "/repos/a/docs"},
                                            {"project": "C", "path": "/repos/c/docs"}]})

    assert [(s.project, s.path) for s in setup.sources.all()] == [
        ("A", "/repos/a/docs"), ("B", "/repos/b/docs"), ("C", "/repos/c/docs")]


def test_a_database_project_keeps_its_items_under_its_new_id(setup: Setup):
    old = Source(project="Central", path="central", backend="database", id=legacy_source_id("central"))
    DatabaseBacklogRepository(setup.db).store_all(old, [Item(id="TASK-001", title="Kept", project="Central")])
    setup.write("config.json", {"sources": [{"project": "Central", "path": "central", "backend": "database"}]})

    (central,) = setup.sources.all()

    assert (central.id, central.path, central.backend) == ("uuid-1", "", "database")
    assert [i.title for i in DatabaseBacklogRepository(setup.db).load(central).items] == ["Kept"]
    assert DatabaseBacklogRepository(setup.db).load(old).items == []

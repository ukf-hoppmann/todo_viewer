"""Every implementation of the sync state port keeps versions per project, markdown folder, and entry."""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.fakes import InMemorySyncStateStore
from todo_viewer.application.ports import SyncStateStore
from todo_viewer.domain.sync import EntryKey, EntryState
from todo_viewer.infrastructure.database.engine import Database
from todo_viewer.infrastructure.database.sync_state import DatabaseSyncStateStore

ITEM = EntryKey("item", "TASK-001")
DOC = EntryKey("document", "TASK-001", "TASK-001_notes.md")
STATE = EntryState("a1", "m1")


@pytest.fixture(params=["memory", "database"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> SyncStateStore:
    if request.param == "memory":
        return InMemorySyncStateStore()
    return DatabaseSyncStateStore(Database(f"sqlite:///{tmp_path / 'todo.db'}"))


def test_a_project_that_never_synced_has_no_state(store: SyncStateStore):
    assert store.load("p", "/md") == {}


def test_saved_states_come_back_as_saved(store: SyncStateStore):
    store.save("p", "/md", {ITEM: STATE, DOC: EntryState("a2", "m2")}, [])

    assert store.load("p", "/md") == {ITEM: STATE, DOC: EntryState("a2", "m2")}


def test_saving_replaces_a_state_and_removes_the_forgotten_ones(store: SyncStateStore):
    store.save("p", "/md", {ITEM: STATE, DOC: STATE}, [])

    store.save("p", "/md", {ITEM: EntryState("a9", "m9")}, [DOC])

    assert store.load("p", "/md") == {ITEM: EntryState("a9", "m9")}


def test_states_belong_to_the_project_and_the_folder(store: SyncStateStore):
    store.save("p", "/md", {ITEM: STATE}, [])

    assert store.load("q", "/md") == {} and store.load("p", "/other") == {}
    store.save("p", "/other", {ITEM: EntryState("x", "y")}, [])
    assert store.load("p", "/md") == {ITEM: STATE}

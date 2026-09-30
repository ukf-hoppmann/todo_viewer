"""Projects and the UI state in the central database."""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest
import sqlalchemy as sa

from todo_viewer.domain.errors import ProjectNotEmptyError
from todo_viewer.domain.item import Item
from todo_viewer.domain.source import Source, SyncBaseline
from todo_viewer.infrastructure.database import Database, DatabaseBacklogRepository
from todo_viewer.infrastructure.database.migrations import MIGRATIONS, migrate
from todo_viewer.infrastructure.database.sources import DatabaseSourceRepository
from todo_viewer.infrastructure.database.ui_state import DatabaseUiStateStore

FILES = Source(project="Files", path="/repos/a/docs", id="aaaaaaaa-0000-4000-8000-000000000001",
               extra={"color": "red"})
CENTRAL = Source(project="Central", path="", backend="database", sync_path="/repos/b/docs",
                 id="bbbbbbbb-0000-4000-8000-000000000002")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(f"sqlite:///{tmp_path / 'todo.db'}")


def test_projects_are_stored_with_all_their_settings_in_order(db: Database):
    repo = DatabaseSourceRepository(db)

    with repo.edit() as sources:
        sources += [FILES, CENTRAL]

    assert repo.all() == [FILES, CENTRAL]
    assert repo.all()[0].extra == {"color": "red"}
    assert repo.all()[1].sync_path == "/repos/b/docs"


def test_projects_can_be_changed_reordered_and_removed(db: Database):
    repo = DatabaseSourceRepository(db)
    with repo.edit() as sources:
        sources += [FILES, CENTRAL]

    with repo.edit() as sources:
        sources[:] = [sources[1], sources[0].updated("Renamed", "/repos/c/docs")]
    with repo.edit() as sources:
        sources.pop(0)

    assert repo.all() == [FILES.updated("Renamed", "/repos/c/docs")]


def test_nothing_is_saved_when_the_edit_fails(db: Database):
    repo = DatabaseSourceRepository(db)

    with pytest.raises(RuntimeError), repo.edit() as sources:
        sources.append(FILES)
        raise RuntimeError("validation failed")

    assert repo.all() == []


def test_a_database_project_with_items_cannot_be_removed(db: Database):
    repo = DatabaseSourceRepository(db)
    with repo.edit() as sources:
        sources += [FILES, CENTRAL]
    DatabaseBacklogRepository(db).store_all(CENTRAL, [Item(id="TASK-001", title="t", project="Central")])

    with pytest.raises(ProjectNotEmptyError) as err, repo.edit() as sources:
        sources.remove(CENTRAL)

    assert (err.value.code, err.value.details) == ("project_not_empty", {"project": "Central"})
    assert repo.all() == [FILES, CENTRAL]


def test_removing_a_markdown_project_drops_the_copy_a_sync_left_in_the_database(db: Database):
    repo = DatabaseSourceRepository(db)
    with repo.edit() as sources:
        sources += [FILES, CENTRAL]
    DatabaseBacklogRepository(db).store_all(FILES, [Item(id="TASK-001", title="copy", project="Files")])

    with repo.edit() as sources:
        sources.remove(FILES)  # the files are the truth of a markdown project; the copy is not worth a refusal

    assert repo.all() == [CENTRAL]
    with db.begin() as conn:
        assert conn.execute(sa.text("SELECT count(*) FROM items")).scalar() == 0


def test_switching_the_database_mirror_off_drops_the_copy_and_switching_it_on_keeps_what_is_there(db: Database):
    repo = DatabaseSourceRepository(db)
    with repo.edit() as sources:
        sources.append(dataclasses.replace(FILES, mirror_database=True))
    DatabaseBacklogRepository(db).store_all(FILES, [Item(id="TASK-001", title="copy", project="Files")])

    with repo.edit() as sources:
        sources[0] = dataclasses.replace(sources[0], project="Renamed")  # mirror stays on: the copy stays
    with db.begin() as conn:
        kept = conn.execute(sa.text("SELECT COUNT(*) FROM items")).scalar_one()
    with repo.edit() as sources:
        sources[0] = dataclasses.replace(sources[0], mirror_database=False)

    assert kept == 1
    with db.begin() as conn:
        assert conn.execute(sa.text("SELECT COUNT(*) FROM items")).scalar_one() == 0
    assert [(s.project, s.mirror_database) for s in repo.all()] == [("Renamed", False)]


def test_projects_created_only_for_items_are_not_listed(db: Database):
    DatabaseBacklogRepository(db).store_all(CENTRAL, [])

    assert DatabaseSourceRepository(db).all() == []


def test_ui_state_is_empty_until_saved(db: Database):
    store = DatabaseUiStateStore(db)

    assert store.load() == {}
    store.save({"hiddenStatuses": ["Completed"], "search": "x"})
    store.save({"hiddenStatuses": ["Rejected"]})

    assert store.load() == {"hiddenStatuses": ["Rejected"]}


def test_a_version_1_database_is_upgraded_and_keeps_its_items(tmp_path: Path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'todo.db'}")
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE schema_version (version INTEGER NOT NULL)"))
        conn.execute(sa.text("INSERT INTO schema_version (version) VALUES (1)"))
        for statement in MIGRATIONS[1]:
            conn.execute(sa.text(statement))
        conn.execute(sa.text("INSERT INTO projects (id) VALUES ('old')"))
        conn.execute(sa.text("INSERT INTO items (uid, project_id, label, item_type, title, status, location, position)"
                             " VALUES ('u', 'old', 'TASK-001', 'Task', 'Kept', 'Open', 'active', 0)"))
    with engine.begin() as conn:
        migrate(conn)

    old = Source(project="Old", path="", backend="database", id="old")
    assert [i.title for i in DatabaseBacklogRepository(Database(str(engine.url))).load(old).items] == ["Kept"]


def test_the_database_mirror_of_a_markdown_project_is_stored(db: Database):
    repo = DatabaseSourceRepository(db)
    mirrored = dataclasses.replace(FILES, mirror_database=True)

    with repo.edit() as sources:
        sources += [mirrored, CENTRAL]

    assert [s.mirror_database for s in repo.all()] == [True, False]


def test_projects_of_an_older_database_get_no_mirror_and_keep_their_items(tmp_path: Path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'todo.db'}")
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE schema_version (version INTEGER NOT NULL)"))
        conn.execute(sa.text("INSERT INTO schema_version (version) VALUES (0)"))
        migrate_to(conn, 2)
        conn.execute(sa.text("INSERT INTO projects (id, name, backend, path, position) "
                             "VALUES ('p1', 'Old', 'markdown', '/repos/a/docs', 0)"))
        conn.execute(sa.text("INSERT INTO items (uid, project_id, label, item_type, title, status, location, position)"
                             " VALUES ('u', 'p1', 'TASK-001', 'Task', 'Kept', 'Open', 'active', 0)"))
    with engine.begin() as conn:
        migrate(conn)

    repo = DatabaseSourceRepository(Database(str(engine.url)))
    old = repo.all()[0]
    assert (old.project, old.mirror_database) == ("Old", False)
    assert [i.title for i in DatabaseBacklogRepository(Database(str(engine.url))).load(old).items] == ["Kept"]


BASELINE = SyncBaseline(at="2026-09-30T10:00:00+02:00", primary="aaaa", mirror="bbbb")


def test_the_state_after_the_last_sync_is_stored_and_survives_other_changes(db: Database):
    repo = DatabaseSourceRepository(db)
    with repo.edit() as sources:
        sources += [dataclasses.replace(CENTRAL, baseline=BASELINE), FILES]

    with repo.edit() as sources:
        sources[1] = sources[1].updated("Renamed", FILES.path)

    stored = repo.all()
    assert stored[0].baseline == BASELINE and stored[1].baseline is None
    with repo.edit() as sources:
        sources[0] = dataclasses.replace(sources[0], baseline=None)
    assert repo.all()[0].baseline is None


def test_projects_of_a_v3_database_have_no_last_sync(tmp_path: Path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'todo.db'}")
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE schema_version (version INTEGER NOT NULL)"))
        conn.execute(sa.text("INSERT INTO schema_version (version) VALUES (0)"))
        migrate_to(conn, 3)
        conn.execute(sa.text("INSERT INTO projects (id, name, backend, path, sync_path, position) "
                             "VALUES ('p1', 'Old', 'database', '', '/md', 0)"))
    with engine.begin() as conn:
        migrate(conn)

    [old] = DatabaseSourceRepository(Database(str(engine.url))).all()
    assert (old.project, old.sync_path, old.baseline) == ("Old", "/md", None)


def migrate_to(conn: sa.Connection, version: int) -> None:
    """Applies the migrations up to `version`, like a database last used by an older release."""
    for number in range(1, version + 1):
        for statement in MIGRATIONS[number]:
            conn.execute(sa.text(statement))
        conn.execute(sa.text("UPDATE schema_version SET version = :v"), {"v": number})


def test_a_database_project_with_its_mirror_off_keeps_the_folder_and_the_flag(db: Database):
    repo = DatabaseSourceRepository(db)
    off = dataclasses.replace(CENTRAL, mirror_disabled=True)

    with repo.edit() as sources:
        sources += [off, FILES]

    stored = repo.all()
    assert (stored[0].sync_path, stored[0].mirror_disabled, stored[0].mirror) == ("/repos/b/docs", True, "none")
    assert stored[1].mirror_disabled is False
    with repo.edit() as sources:
        sources[0] = dataclasses.replace(sources[0], mirror_disabled=False)
    assert repo.all()[0].mirror == "markdown"


def test_projects_of_a_v4_database_keep_their_mirror_folder_switched_on(tmp_path: Path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'todo.db'}")
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE schema_version (version INTEGER NOT NULL)"))
        conn.execute(sa.text("INSERT INTO schema_version (version) VALUES (0)"))
        migrate_to(conn, 4)
        conn.execute(sa.text("INSERT INTO projects (id, name, backend, path, sync_path, position) "
                             "VALUES ('p1', 'Old', 'database', '', '/md', 0)"))
    with engine.begin() as conn:
        migrate(conn)

    [old] = DatabaseSourceRepository(Database(str(engine.url))).all()
    assert (old.sync_path, old.mirror_disabled, old.mirror) == ("/md", False, "markdown")

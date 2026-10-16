import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, insert, select
from viewer.core.domain.errors import NotFound, VersionConflict
from viewer.core.infrastructure.database import SqliteDatabase, update_with_revision

metadata = MetaData()
things = Table(
    "a_things",
    metadata,
    Column("uid", String, primary_key=True),
    Column("title", String, nullable=False),
    Column("revision", Integer, nullable=False),
)


def seeded(database: SqliteDatabase) -> None:
    with database.transaction() as tx:
        metadata.create_all(tx.connection)
        tx.connection.execute(insert(things).values(uid="u1", title="alt", revision=1))


def test_update_with_matching_revision_increments_it(database: SqliteDatabase) -> None:
    seeded(database)
    with database.transaction() as tx:
        new = update_with_revision(tx.connection, things, things.c.uid == "u1", 1, {"title": "neu"})
        row = tx.connection.execute(select(things.c.title, things.c.revision)).one()
    assert new == 2 and tuple(row) == ("neu", 2)


def test_stale_revision_raises_version_conflict_and_changes_nothing(database: SqliteDatabase) -> None:
    seeded(database)
    with database.transaction() as tx:
        update_with_revision(tx.connection, things, things.c.uid == "u1", 1, {"title": "zuerst"})
    with pytest.raises(VersionConflict) as err, database.transaction() as tx:
        update_with_revision(tx.connection, things, things.c.uid == "u1", 1, {"title": "zu spät"})
    assert err.value.code == "version_conflict"
    assert err.value.details == {"table": "a_things", "expected": 1, "current": 2}
    with database.transaction() as tx:
        assert tx.connection.execute(select(things.c.title)).scalar() == "zuerst"


def test_missing_row_raises_not_found(database: SqliteDatabase) -> None:
    seeded(database)
    with pytest.raises(NotFound), database.transaction() as tx:
        update_with_revision(tx.connection, things, things.c.uid == "nope", 1, {"title": "x"})

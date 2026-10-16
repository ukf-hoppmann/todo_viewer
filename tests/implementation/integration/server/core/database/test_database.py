import pytest
from sqlalchemy.exc import IntegrityError
from viewer.core.infrastructure.database import SqliteDatabase


def test_foreign_keys_are_on(database: SqliteDatabase) -> None:
    with database.transaction() as tx:
        assert tx.connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        tx.connection.exec_driver_sql("CREATE TABLE p (id INTEGER PRIMARY KEY)")
        tx.connection.exec_driver_sql("CREATE TABLE c (id INTEGER PRIMARY KEY, p INTEGER REFERENCES p(id))")
    with pytest.raises(IntegrityError), database.transaction() as tx:
        tx.connection.exec_driver_sql("INSERT INTO c(id, p) VALUES (1, 99)")


def test_exception_rolls_back_data_and_ddl(database: SqliteDatabase) -> None:
    with database.transaction() as tx:
        tx.connection.exec_driver_sql("CREATE TABLE t (id INTEGER)")
    with pytest.raises(RuntimeError), database.transaction() as tx:
        tx.connection.exec_driver_sql("INSERT INTO t VALUES (1)")
        tx.connection.exec_driver_sql("CREATE TABLE u (id INTEGER)")
        raise RuntimeError("abbruch")
    with database.transaction() as tx:
        assert tx.connection.exec_driver_sql("SELECT count(*) FROM t").scalar() == 0
        names = {r[0] for r in tx.connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "u" not in names


def test_creates_missing_parent_folder(database: SqliteDatabase) -> None:
    assert database.path.parent.is_dir()

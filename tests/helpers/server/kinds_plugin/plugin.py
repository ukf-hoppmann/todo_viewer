"""Test-Plugin, das Elementtypen im Register von `workspace` anmeldet und es benutzt wie ein Fach-Plugin.

Es hat eine kleine Eltern/Kind-Tabelle (`kinds_test_nodes`) und meldet dem Papierkorb Kinder, Regel und Aufräumen an:
ein Element lässt sich nicht unter einem Elternteil im Papierkorb wiederherstellen.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Connection, text
from viewer.core.application.plugin import PluginContext, PluginDefinition
from viewer.core.application.ports import Transaction
from viewer.core.domain.errors import DomainError
from viewer.core.domain.plugin import ElementKind, Migration
from viewer.core.infrastructure.database import SqlTransaction

KINDS = (
    ElementKind("epic", "EPIC"),
    ElementKind("story", "STORY"),
    ElementKind("task", "TASK"),
)


class ParentInTrash(DomainError):
    code = "parent_in_trash"


def _conn(tx: Transaction) -> Connection:
    assert isinstance(tx, SqlTransaction)
    return tx.connection


def _v1(connection: Connection) -> None:
    connection.exec_driver_sql(
        "CREATE TABLE kinds_test_nodes (uid TEXT PRIMARY KEY REFERENCES workspace_elements(uid),"
        " parent_uid TEXT REFERENCES kinds_test_nodes(uid))"
    )


class KindsServices:
    def __init__(self, context: PluginContext) -> None:
        self.database = context.database
        self.registry: Any = context.required["workspace"].registry
        self.links: Any = context.required["workspace"].links
        self.purged: list[str] = []
        trash = context.required["workspace"].trash
        for kind in KINDS:
            trash.register(kind.kind, children=self._children, restore_guard=self._guard, purger=self._purge)

    def run(self, action: Any) -> Any:
        """Führt `action(registry, tx)` in einer Transaktion aus (wie ein Fach-Plugin)."""
        with self.database.transaction() as tx:
            return action(self.registry, tx)

    def run_links(self, action: Any) -> Any:
        """Führt `action(links, tx)` in einer Transaktion aus (Port `Links`)."""
        with self.database.transaction() as tx:
            return action(self.links, tx)

    def add(self, project: str, kind: str, parent: str | None = None, title: str = "") -> Any:
        """Legt ein Element mit einem Platz im Baum an (unter `parent`)."""
        with self.database.transaction() as tx:
            element = self.registry.register(tx, project, kind, title)
            _conn(tx).execute(
                text("INSERT INTO kinds_test_nodes(uid, parent_uid) VALUES (:u, :p)"), {"u": element.uid, "p": parent}
            )
            return element

    def _children(self, tx: Transaction, uid: str) -> list[str]:
        rows = _conn(tx).execute(
            text("SELECT uid FROM kinds_test_nodes WHERE parent_uid = :u ORDER BY uid"), {"u": uid}
        )
        return [str(row[0]) for row in rows]

    def _guard(self, tx: Transaction, element: Any) -> None:
        row = (
            _conn(tx)
            .execute(
                text(
                    "SELECT p.deleted_at FROM kinds_test_nodes n JOIN workspace_elements p ON p.uid = n.parent_uid "
                    "WHERE n.uid = :u"
                ),
                {"u": element.uid},
            )
            .first()
        )
        if row is not None and row[0] is not None:
            raise ParentInTrash("Das Elternelement liegt im Papierkorb", details={"uid": element.uid})

    def _purge(self, tx: Transaction, uid: str) -> None:
        _conn(tx).execute(text("DELETE FROM kinds_test_nodes WHERE uid = :u"), {"u": uid})
        self.purged.append(uid)


def _build(context: PluginContext) -> KindsServices:
    return KindsServices(context)


KINDS_PLUGIN = PluginDefinition(
    id="kinds-test",
    build=_build,
    requires=("workspace",),
    element_kinds=KINDS,
    migrations=(Migration(1, _v1),),
)

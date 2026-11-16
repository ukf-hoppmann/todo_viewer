from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import Connection, Row, text

from viewer.core.application.ports import Transaction
from viewer.core.infrastructure.database import SqlTransaction
from viewer.plugins.mindmap.domain.model import Node, Placement, Tree

_NODE = """
SELECT e.uid, e.project_uid, e.label, e.revision, e.deleted_at, n.title, n.text
FROM mindmap_nodes n JOIN workspace_elements e ON e.uid = n.uid
"""


def _conn(tx: Transaction) -> Connection:
    assert isinstance(tx, SqlTransaction)
    return tx.connection


def _node(row: Row[Any]) -> Node:
    deleted = row.deleted_at
    return Node(
        uid=row.uid,
        project_uid=row.project_uid,
        label=row.label,
        title=row.title,
        text=row.text,
        revision=row.revision,
        deleted_at=datetime.fromisoformat(deleted) if deleted else None,
    )


def _placement(row: Row[Any]) -> Placement:
    return Placement(row.tree_uid, row.node_uid, row.parent_uid, row.position)


class SqlMindmapRepository:
    def tree_of_project(self, tx: Transaction, project_uid: str) -> Tree | None:
        row = (
            _conn(tx)
            .execute(
                text("SELECT uid, project_uid, kind FROM mindmap_trees WHERE project_uid = :p AND kind = 'project'"),
                {"p": project_uid},
            )
            .first()
        )
        return Tree(row.uid, row.project_uid, row.kind) if row else None

    def get_tree(self, tx: Transaction, uid: str) -> Tree | None:
        row = (
            _conn(tx)
            .execute(text("SELECT uid, project_uid, kind FROM mindmap_trees WHERE uid = :u"), {"u": uid})
            .first()
        )
        return Tree(row.uid, row.project_uid, row.kind) if row else None

    def insert_tree(self, tx: Transaction, tree: Tree) -> None:
        _conn(tx).execute(
            text("INSERT INTO mindmap_trees(uid, project_uid, kind) VALUES (:u, :p, :k)"),
            {"u": tree.uid, "p": tree.project_uid, "k": tree.kind},
        )

    def insert_node(self, tx: Transaction, node: Node) -> None:
        _conn(tx).execute(
            text("INSERT INTO mindmap_nodes(uid, title, text) VALUES (:u, :t, :x)"),
            {"u": node.uid, "t": node.title, "x": node.text},
        )

    def update_node(self, tx: Transaction, node: Node) -> None:
        _conn(tx).execute(
            text("UPDATE mindmap_nodes SET title = :t, text = :x WHERE uid = :u"),
            {"u": node.uid, "t": node.title, "x": node.text},
        )

    def get_node(self, tx: Transaction, uid: str) -> Node | None:
        row = _conn(tx).execute(text(_NODE + " WHERE n.uid = :u"), {"u": uid}).first()
        return _node(row) if row else None

    def nodes_in_tree(self, tx: Transaction, tree_uid: str, *, include_deleted: bool = False) -> list[Node]:
        query = _NODE + " JOIN mindmap_placements p ON p.node_uid = n.uid WHERE p.tree_uid = :t"
        if not include_deleted:
            query += " AND e.deleted_at IS NULL"
        return [_node(row) for row in _conn(tx).execute(text(query + " ORDER BY e.label"), {"t": tree_uid})]

    def placements(self, tx: Transaction, tree_uid: str) -> list[Placement]:
        rows = _conn(tx).execute(
            text(
                "SELECT tree_uid, node_uid, parent_uid, position FROM mindmap_placements WHERE tree_uid = :t "
                "ORDER BY parent_uid, position, node_uid"
            ),
            {"t": tree_uid},
        )
        return [_placement(row) for row in rows]

    def placements_of(self, tx: Transaction, node_uid: str) -> list[Placement]:
        rows = _conn(tx).execute(
            text(
                "SELECT tree_uid, node_uid, parent_uid, position FROM mindmap_placements WHERE node_uid = :n "
                "ORDER BY tree_uid"
            ),
            {"n": node_uid},
        )
        return [_placement(row) for row in rows]

    def upsert_placements(self, tx: Transaction, placements: Sequence[Placement]) -> None:
        for p in placements:
            _conn(tx).execute(
                text(
                    "INSERT INTO mindmap_placements(tree_uid, node_uid, parent_uid, position) "
                    "VALUES (:t, :n, :p, :s) ON CONFLICT(tree_uid, node_uid) "
                    "DO UPDATE SET parent_uid = excluded.parent_uid, position = excluded.position"
                ),
                {"t": p.tree_uid, "n": p.node_uid, "p": p.parent_uid, "s": p.position},
            )

    def child_uids(self, tx: Transaction, node_uid: str) -> list[str]:
        rows = _conn(tx).execute(
            text("SELECT DISTINCT node_uid FROM mindmap_placements WHERE parent_uid = :n ORDER BY node_uid"),
            {"n": node_uid},
        )
        return [row.node_uid for row in rows]

    def delete_node(self, tx: Transaction, uid: str) -> None:
        _conn(tx).execute(text("DELETE FROM mindmap_placements WHERE node_uid = :u"), {"u": uid})
        _conn(tx).execute(text("DELETE FROM mindmap_nodes WHERE uid = :u"), {"u": uid})

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import Connection, Row, bindparam, text

from viewer.core.application.ports import Transaction
from viewer.core.domain.errors import VersionConflict
from viewer.core.infrastructure.database import SqlTransaction
from viewer.plugins.mindmap.application.ports import Document
from viewer.plugins.mindmap.domain.documents import NOTES, document_kind
from viewer.plugins.mindmap.domain.model import Node, Placement, Tree

_NODE = """
SELECT e.uid, e.project_uid, e.label, e.revision, e.deleted_at, n.title, n.text, n.mark
FROM mindmap_nodes n JOIN workspace_elements e ON e.uid = n.uid
"""


_TREE = "SELECT uid, project_uid, kind, name, revision, deleted_at FROM mindmap_trees"


def _tree(row: Row[Any]) -> Tree:
    deleted = row.deleted_at
    return Tree(
        row.uid, row.project_uid, row.kind, row.name, row.revision, datetime.fromisoformat(deleted) if deleted else None
    )


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
        mark=row.mark,
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
                text(f"{_TREE} WHERE project_uid = :p AND kind = 'project'"),
                {"p": project_uid},
            )
            .first()
        )
        return _tree(row) if row else None

    def get_tree(self, tx: Transaction, uid: str) -> Tree | None:
        row = _conn(tx).execute(text(f"{_TREE} WHERE uid = :u"), {"u": uid}).first()
        return _tree(row) if row else None

    def insert_tree(self, tx: Transaction, tree: Tree) -> None:
        _conn(tx).execute(
            text("INSERT INTO mindmap_trees(uid, project_uid, kind, name) VALUES (:u, :p, :k, :n)"),
            {"u": tree.uid, "p": tree.project_uid, "k": tree.kind, "n": tree.name},
        )

    def free_maps(self, tx: Transaction, project_uid: str) -> list[Tree]:
        rows = _conn(tx).execute(
            text(f"{_TREE} WHERE project_uid = :p AND kind = 'free' AND deleted_at IS NULL ORDER BY rowid"),
            {"p": project_uid},
        )
        return [_tree(row) for row in rows]

    def deleted_maps(self, tx: Transaction, project_uids: Sequence[str] | None) -> list[Tree]:
        query = f"{_TREE} WHERE kind = 'free' AND deleted_at IS NOT NULL"
        if project_uids is None:
            rows = _conn(tx).execute(text(query + " ORDER BY rowid"))
        else:
            if not project_uids:
                return []
            statement = text(query + " AND project_uid IN :ps ORDER BY rowid").bindparams(
                bindparam("ps", expanding=True)
            )
            rows = _conn(tx).execute(statement, {"ps": list(project_uids)})
        return [_tree(row) for row in rows]

    def rename_tree(self, tx: Transaction, uid: str, name: str, expected: int) -> int:
        result = _conn(tx).execute(
            text("UPDATE mindmap_trees SET name = :n, revision = revision + 1 WHERE uid = :u AND revision = :r"),
            {"n": name, "u": uid, "r": expected},
        )
        if result.rowcount != 1:
            raise VersionConflict("Die Map wurde inzwischen geändert", details={"uid": uid, "expected": expected})
        return expected + 1

    def set_tree_deleted(self, tx: Transaction, uid: str, at: datetime | None, expected: int | None = None) -> int:
        query = "UPDATE mindmap_trees SET deleted_at = :d, revision = revision + 1 WHERE uid = :u"
        params: dict[str, Any] = {"d": at.isoformat() if at else None, "u": uid}
        if expected is not None:
            query += " AND revision = :r"
            params["r"] = expected
        result = _conn(tx).execute(text(query), params)
        if result.rowcount != 1:
            raise VersionConflict("Die Map wurde inzwischen geändert", details={"uid": uid, "expected": expected})
        return int(
            _conn(tx).execute(text("SELECT revision FROM mindmap_trees WHERE uid = :u"), {"u": uid}).scalar_one()
        )

    def delete_tree(self, tx: Transaction, uid: str) -> None:
        _conn(tx).execute(text("DELETE FROM mindmap_placements WHERE tree_uid = :u"), {"u": uid})
        _conn(tx).execute(text("DELETE FROM mindmap_trees WHERE uid = :u"), {"u": uid})

    def node_count(self, tx: Transaction, tree_uid: str) -> int:
        return int(
            _conn(tx)
            .execute(
                text(
                    "SELECT COUNT(*) FROM mindmap_placements p JOIN workspace_elements e ON e.uid = p.node_uid "
                    "WHERE p.tree_uid = :t AND e.deleted_at IS NULL"
                ),
                {"t": tree_uid},
            )
            .scalar_one()
        )

    def shared_count(self, tx: Transaction, tree_uid: str) -> int:
        return int(
            _conn(tx)
            .execute(
                text(
                    "SELECT COUNT(*) FROM mindmap_placements p JOIN workspace_elements e ON e.uid = p.node_uid "
                    "WHERE p.tree_uid = :t AND e.deleted_at IS NULL AND EXISTS ("
                    "SELECT 1 FROM mindmap_placements q WHERE q.node_uid = p.node_uid AND q.tree_uid <> p.tree_uid)"
                ),
                {"t": tree_uid},
            )
            .scalar_one()
        )

    def insert_node(self, tx: Transaction, node: Node) -> None:
        _conn(tx).execute(
            text("INSERT INTO mindmap_nodes(uid, title, text, mark) VALUES (:u, :t, :x, :m)"),
            {"u": node.uid, "t": node.title, "x": node.text, "m": node.mark},
        )

    def update_node(self, tx: Transaction, node: Node) -> None:
        _conn(tx).execute(
            text("UPDATE mindmap_nodes SET title = :t, text = :x, mark = :m WHERE uid = :u"),
            {"u": node.uid, "t": node.title, "x": node.text, "m": node.mark},
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
            text(
                "SELECT DISTINCT c.node_uid FROM mindmap_placements c WHERE c.parent_uid = :n AND NOT EXISTS ("
                "SELECT 1 FROM mindmap_placements o WHERE o.node_uid = c.node_uid "
                "AND (o.parent_uid IS NULL OR o.parent_uid <> :n)) ORDER BY c.node_uid"
            ),
            {"n": node_uid},
        )
        return [row.node_uid for row in rows]

    def delete_placements(self, tx: Transaction, placements: Sequence[Placement]) -> None:
        for p in placements:
            _conn(tx).execute(
                text("DELETE FROM mindmap_placements WHERE tree_uid = :t AND node_uid = :n"),
                {"t": p.tree_uid, "n": p.node_uid},
            )

    def live_trees_of(self, tx: Transaction, node_uids: Sequence[str]) -> dict[str, set[str]]:
        found: dict[str, set[str]] = {}
        if not node_uids:
            return found
        statement = text(
            "SELECT p.node_uid, p.tree_uid FROM mindmap_placements p JOIN mindmap_trees t ON t.uid = p.tree_uid "
            "WHERE t.deleted_at IS NULL AND p.node_uid IN :uids"
        ).bindparams(bindparam("uids", expanding=True))
        for row in _conn(tx).execute(statement, {"uids": list(node_uids)}):
            found.setdefault(row.node_uid, set()).add(row.tree_uid)
        return found

    def live_tree_counts(self, tx: Transaction, tree_uid: str) -> dict[str, int]:
        rows = _conn(tx).execute(
            text(
                "SELECT p.node_uid, COUNT(*) AS n FROM mindmap_placements p "
                "JOIN mindmap_placements q ON q.node_uid = p.node_uid "
                "JOIN mindmap_trees t ON t.uid = q.tree_uid AND t.deleted_at IS NULL "
                "WHERE p.tree_uid = :t GROUP BY p.node_uid"
            ),
            {"t": tree_uid},
        )
        return {row.node_uid: int(row.n) for row in rows}

    def delete_node(self, tx: Transaction, uid: str) -> None:
        _conn(tx).execute(text("DELETE FROM mindmap_documents WHERE node_uid = :u"), {"u": uid})
        _conn(tx).execute(text("DELETE FROM mindmap_placements WHERE node_uid = :u"), {"u": uid})
        _conn(tx).execute(text("DELETE FROM mindmap_nodes WHERE uid = :u"), {"u": uid})


class SqlDocumentRepository:
    def list_for(self, tx: Transaction, node_uid: str) -> list[Document]:
        rows = _conn(tx).execute(
            text(
                "SELECT d.*, e.label FROM mindmap_documents d JOIN workspace_elements e ON e.uid = d.node_uid "
                "WHERE d.node_uid = :u"
            ),
            {"u": node_uid},
        )
        return sorted((self._document(row) for row in rows), key=lambda d: (d.kind != NOTES, d.name))

    def names_of(self, tx: Transaction, node_uids: Sequence[str]) -> dict[str, list[str]]:
        if not node_uids:
            return {}
        query = text(
            "SELECT d.node_uid, d.name, e.label FROM mindmap_documents d "
            "JOIN workspace_elements e ON e.uid = d.node_uid WHERE d.node_uid IN :uids"
        ).bindparams(bindparam("uids", expanding=True))
        found: dict[str, list[tuple[bool, str]]] = {}
        for row in _conn(tx).execute(query, {"uids": list(node_uids)}):
            found.setdefault(row.node_uid, []).append((document_kind(row.label, row.name) != NOTES, row.name))
        return {uid: [name for _, name in sorted(pairs)] for uid, pairs in found.items()}

    def get(self, tx: Transaction, node_uid: str, name: str) -> Document | None:
        row = (
            _conn(tx)
            .execute(
                text(
                    "SELECT d.*, e.label FROM mindmap_documents d JOIN workspace_elements e ON e.uid = d.node_uid "
                    "WHERE d.node_uid = :u AND d.name = :n"
                ),
                {"u": node_uid, "n": name},
            )
            .first()
        )
        return self._document(row) if row else None

    @staticmethod
    def _document(row: Row[Any]) -> Document:
        kind = document_kind(row.label, row.name) or "spec"
        return Document(row.node_uid, row.name, kind, row.content, row.revision, datetime.fromisoformat(row.updated_at))

    def insert(self, tx: Transaction, document: Document) -> None:
        _conn(tx).execute(
            text(
                "INSERT INTO mindmap_documents(node_uid, name, content, revision, updated_at) "
                "VALUES (:u, :n, :c, :r, :t)"
            ),
            {
                "u": document.node_uid,
                "n": document.name,
                "c": document.content,
                "r": document.revision,
                "t": document.updated_at.isoformat(),
            },
        )

    def update(self, tx: Transaction, node_uid: str, name: str, content: str, expected: int, at: datetime) -> int:
        result = _conn(tx).execute(
            text(
                "UPDATE mindmap_documents SET content = :c, revision = revision + 1, updated_at = :t "
                "WHERE node_uid = :u AND name = :n AND revision = :r"
            ),
            {"c": content, "t": at.isoformat(), "u": node_uid, "n": name, "r": expected},
        )
        if result.rowcount != 1:
            raise VersionConflict(
                "Das Dokument wurde inzwischen geändert", details={"name": name, "expected": expected}
            )
        return expected + 1

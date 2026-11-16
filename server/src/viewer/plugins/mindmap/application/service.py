"""Anwendungsfälle der Mindmap: Baum lesen, Knoten anlegen, ändern und umhängen oder umordnen.

Papierkorb und Wiederherstellen gehen über `workspace` (`delete_element`, `restore_elements`); das Plugin meldet dort
an, wie ein Ast behandelt wird (siehe `plugin.py`).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, replace

from viewer.core.application.ports import Database, EventBus, Transaction
from viewer.core.domain.errors import InvalidInput, NotFound
from viewer.core.domain.events import Event
from viewer.plugins.mindmap.application.ports import MindmapRepository
from viewer.plugins.mindmap.domain import tree as rules
from viewer.plugins.mindmap.domain.model import TREE_PROJECT, MindmapViolation, Node, Placement, Tree
from viewer.plugins.workspace import ElementRegistry, Projects

NODE_TOPIC = "mindmap.node.changed"
KIND = "mindmap_node"
_LABEL = re.compile(r"^[A-Z]+-\d+$")


@dataclass(frozen=True)
class TreeView:
    """Der Baum eines Projekts. `tree` ist `None`, solange noch kein Knoten angelegt wurde."""

    project_uid: str
    tree: Tree | None
    #: Die lebenden Knoten mit ihrer Platzierung, nach Eltern vor Kindern und Stelle geordnet.
    nodes: list[tuple[Node, Placement]]


@dataclass(frozen=True)
class NodeView:
    node: Node
    placement: Placement


def title_of(value: object) -> str:
    """Der Titel ist eine Zeile ohne überflüssige Leerzeichen und nicht leer."""
    cleaned = " ".join(value.split()) if isinstance(value, str) else ""
    if not cleaned:
        raise InvalidInput("title fehlt", details={"field": "title"})
    return cleaned


class MindmapService:
    def __init__(
        self,
        repository: MindmapRepository,
        registry: ElementRegistry,
        projects: Projects,
        database: Database,
        events: EventBus,
        new_uid: Callable[[], str],
    ) -> None:
        self._repository = repository
        self._registry = registry
        self._projects = projects
        self._database = database
        self._events = events
        self._new_uid = new_uid

    # --- Lesen ----------------------------------------------------------------------------------------------------

    def get_tree(self, project_uid: str) -> TreeView:
        with self._database.transaction() as tx:
            self._require_project(tx, project_uid)
            tree = self._repository.tree_of_project(tx, project_uid)
            if tree is None:
                return TreeView(project_uid, None, [])
            return TreeView(project_uid, tree, self._ordered(tx, tree))

    def get_node(self, ref: str, project_uid: str | None, tree_uid: str | None = None) -> NodeView:
        with self._database.transaction() as tx:
            node = self._resolve(tx, ref, project_uid)
            return self._view(tx, node, tree_uid)

    # --- Schreiben ------------------------------------------------------------------------------------------------

    def create_node(
        self, project_uid: str, title: object, text: str | None, parent: str | None, position: int | None
    ) -> str:
        clean = title_of(title)
        with self._database.transaction() as tx:
            self._require_project(tx, project_uid)
            tree = self._tree_for(tx, project_uid)
            placements = self._repository.placements(tx, tree.uid)
            live = self._live(tx, tree.uid)
            parent_uid = self._parent_uid(tx, parent, project_uid)
            element = self._registry.register(tx, project_uid, KIND, clean)
            rules.check_project(tree.project_uid, element.project_uid)
            rules.check_new(placements, element.uid, parent_uid, live)
            self._repository.insert_node(tx, Node(element.uid, project_uid, element.label, clean, text or None, 1))
            changed = rules.arrange(placements, tree.uid, element.uid, parent_uid, position, live | {element.uid})
            self._repository.upsert_placements(tx, changed)
        self._changed(element.uid, project_uid, "created", tree.uid)
        return str(element.uid)

    def update_node(
        self, ref: str, project_uid: str | None, version: int, title: object | None, text: str | None
    ) -> str:
        if title is None and text is None:
            raise InvalidInput("Nichts zu ändern: title oder text angeben", details={"field": "title"})
        with self._database.transaction() as tx:
            node = self._resolve(tx, ref, project_uid)
            self._require_alive(node)
            updated = node
            if title is not None:
                updated = replace(updated, title=title_of(title))
            if text is not None:
                updated = replace(updated, text=text or None)  # "" löscht den Text
            self._registry.bump_revision(tx, node.uid, version)
            self._repository.update_node(tx, updated)
            if updated.title != node.title:
                self._registry.set_title(tx, node.uid, updated.title)
        self._changed(node.uid, node.project_uid, "updated")
        return node.uid

    def move_node(
        self,
        ref: str,
        project_uid: str | None,
        version: int,
        parent: str | None,
        position: int | None,
        tree_uid: str | None,
    ) -> str:
        """Hängt den Knoten samt Ast unter `parent` (`None`: unter die Wurzel) an die Stelle `position` oder ordnet
        ihn unter demselben Parent um."""
        with self._database.transaction() as tx:
            node = self._resolve(tx, ref, project_uid)
            self._require_alive(node)
            tree = self._tree_of_node(tx, node, tree_uid)
            rules.check_project(tree.project_uid, node.project_uid)
            placements = self._repository.placements(tx, tree.uid)
            live = self._live(tx, tree.uid)
            parent_uid = self._parent_uid(tx, parent, node.project_uid)
            rules.check_move(placements, node.uid, parent_uid, live)
            self._registry.bump_revision(tx, node.uid, version)
            self._repository.upsert_placements(
                tx, rules.arrange(placements, tree.uid, node.uid, parent_uid, position, live)
            )
        self._changed(node.uid, node.project_uid, "moved", tree.uid)
        return node.uid

    # --- Papierkorb (vom Papierkorb von `workspace` gerufen) -------------------------------------------------------

    def children(self, tx: Transaction, uid: str) -> list[str]:
        return self._repository.child_uids(tx, uid)

    def restore_guard(self, tx: Transaction, uid: str) -> None:
        """Ein Knoten kommt nicht zurück, solange sein Parent im Papierkorb liegt."""
        for placement in self._repository.placements_of(tx, uid):
            parent = self._repository.get_node(tx, placement.parent_uid) if placement.parent_uid else None
            if parent is not None and parent.deleted_at is not None:
                raise MindmapViolation(
                    "mindmap_parent_in_trash",
                    f"{parent.label} liegt im Papierkorb; erst diesen Knoten wiederherstellen",
                    parent=parent.label,
                )

    def purge(self, tx: Transaction, uid: str) -> None:
        self._repository.delete_node(tx, uid)

    def announce(self, uids: list[str], change: str) -> None:
        """Meldet gelöschte oder wiederhergestellte Knoten, die der Papierkorb von `workspace` bewegt hat."""
        with self._database.transaction() as tx:
            nodes = [n for uid in uids if (n := self._repository.get_node(tx, uid)) is not None]
        for node in nodes:
            self._changed(node.uid, node.project_uid, change)

    # --- Hilfen ---------------------------------------------------------------------------------------------------

    def _require_project(self, tx: Transaction, project_uid: str) -> None:
        project = self._projects.get(tx, project_uid)
        if project is None or project.deleted_at is not None:
            raise NotFound(f"Projekt {project_uid} gibt es nicht", details={"project": project_uid})

    @staticmethod
    def _require_alive(node: Node) -> None:
        if node.deleted_at is not None:
            raise MindmapViolation("mindmap_node_deleted", f"{node.label} liegt im Papierkorb", node=node.label)

    def _tree_for(self, tx: Transaction, project_uid: str) -> Tree:
        """Der Projektbaum; beim ersten Knoten wird er angelegt."""
        existing = self._repository.tree_of_project(tx, project_uid)
        if existing is not None:
            return existing
        tree = Tree(self._new_uid(), project_uid, TREE_PROJECT)
        self._repository.insert_tree(tx, tree)
        return tree

    def _tree_of_node(self, tx: Transaction, node: Node, tree_uid: str | None) -> Tree:
        placements = self._repository.placements_of(tx, node.uid)
        if tree_uid is None:
            if len(placements) != 1:
                raise InvalidInput(
                    "Der Knoten steht in keinem oder mehreren Bäumen; tree angeben", details={"field": "tree"}
                )
            tree_uid = placements[0].tree_uid
        elif tree_uid not in {p.tree_uid for p in placements}:
            raise MindmapViolation("mindmap_node_not_in_tree", "Der Knoten steht nicht in diesem Baum", node=node.label)
        tree = self._repository.get_tree(tx, tree_uid)
        assert tree is not None
        return tree

    def _live(self, tx: Transaction, tree_uid: str) -> set[str]:
        return {n.uid for n in self._repository.nodes_in_tree(tx, tree_uid)}

    def _parent_uid(self, tx: Transaction, parent: str | None, project_uid: str) -> str | None:
        if parent in (None, ""):
            return None
        return self._resolve(tx, str(parent), project_uid).uid

    def _resolve(self, tx: Transaction, ref: str, project_uid: str | None) -> Node:
        node = self._repository.get_node(tx, ref)
        if node is None and project_uid is not None and _LABEL.match(ref.strip()):
            element = self._registry.find_by_label(tx, project_uid, ref.strip())
            node = self._repository.get_node(tx, element.uid) if element else None
        if node is None:
            if project_uid is None and _LABEL.match(ref.strip()):
                raise InvalidInput(
                    f"'{ref}' ist keine uid; für ein Label braucht es das Projekt", details={"field": "project"}
                )
            raise NotFound(f"Knoten {ref} gibt es nicht", details={"ref": ref})
        return node

    def _ordered(self, tx: Transaction, tree: Tree) -> list[tuple[Node, Placement]]:
        nodes = {n.uid: n for n in self._repository.nodes_in_tree(tx, tree.uid)}
        placements = rules.compacted(self._repository.placements(tx, tree.uid), nodes.keys())
        ordered: list[tuple[Node, Placement]] = []
        queue: list[str | None] = [None]
        while queue:
            parent = queue.pop(0)
            for placement in rules.children_of(placements, parent):
                ordered.append((nodes[placement.node_uid], placement))
                queue.append(placement.node_uid)
        return ordered

    def _view(self, tx: Transaction, node: Node, tree_uid: str | None) -> NodeView:
        tree = self._tree_of_node(tx, node, tree_uid)
        placements = self._repository.placements(tx, tree.uid)
        live = {n.uid for n in self._repository.nodes_in_tree(tx, tree.uid)}
        placement = rules.find(rules.compacted(placements, live | {node.uid}), node.uid)
        assert placement is not None
        return NodeView(node, placement)

    def _changed(self, uid: str, project_uid: str, change: str, tree_uid: str | None = None) -> None:
        payload: dict[str, object] = {"uid": uid, "project_uid": project_uid, "change": change}
        if tree_uid is not None:
            payload["tree_uid"] = tree_uid
        self._events.publish(Event(NODE_TOPIC, payload, public=True))

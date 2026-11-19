"""Äste zwischen Bäumen (`TASK-063`): umhängen, übertragen, „Hier entfernen“, „Knoten löschen“ und „wiederherstellen
und umziehen“.

Ein Ast ist ein Knoten mit seinen Unterknoten in einem Baum. Nichts wird kopiert: ein übertragener Ast ist derselbe
Datensatz mit einer weiteren Platzierung je Knoten. Die Rechnung steht in `domain/branches.py`; hier wird gelesen,
gespeichert und gemeldet.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from viewer.core.application.ports import Clock, Database, EventBus, Transaction
from viewer.core.domain.errors import InvalidInput, VersionConflict
from viewer.plugins.mindmap.application.ports import MindmapRepository
from viewer.plugins.mindmap.application.service import MindmapService
from viewer.plugins.mindmap.domain import branches as branch_rules
from viewer.plugins.mindmap.domain import tree as rules
from viewer.plugins.mindmap.domain.model import TREE_PROJECT, MindmapViolation, Node, RemovedPlacement, Tree
from viewer.plugins.workspace import ElementRegistry, Projects

Restore = Callable[[Sequence[str]], list[str]]


@dataclass(frozen=True)
class BranchMoved:
    node: Node
    target: Tree
    #: Die Knoten des Asts (mit dem Knoten selbst), die im Ziel stehen.
    nodes: int


@dataclass(frozen=True)
class Removal:
    node: Node
    #: Die Knoten, die in den Papierkorb gingen (der Knoten selbst, wenn er seine letzte Platzierung verlor, und die
    #: heimatlos gewordenen Unterknoten).
    nodes_deleted: int
    #: Die Knoten des Asts, die in einem anderen Baum stehen und dort erhalten bleiben.
    kept_elsewhere: int


@dataclass(frozen=True)
class NodeTree:
    tree: Tree
    #: Bei freien Maps der Name, beim Projektbaum der Name des Projekts.
    name: str
    parent_uid: str | None


@dataclass(frozen=True)
class PlacementRestored:
    node: Node
    tree: Tree
    #: Die Knoten, die wieder im Baum stehen (der Knoten und seine Unterknoten aus derselben Entfernung).
    nodes: int
    #: Die Knoten im Papierkorb, die als entfernt gemerkt bleiben.
    skipped: int
    parent_uid: str | None
    #: Der alte Parent fehlte: der Ast steht unter der Wurzel der Map.
    fell_back: bool


@dataclass(frozen=True)
class RemovedFrom:
    tree: Tree
    name: str
    #: Der Parent von damals; leer unter der Wurzel.
    parent_uid: str | None
    #: Ob der Parent von damals noch im Baum steht (sonst käme der Ast unter die Wurzel).
    parent_available: bool
    #: Die Knoten, die mit ihm zurückkämen (er selbst und seine Unterknoten aus derselben Entfernung).
    nodes: int


@dataclass(frozen=True)
class CutResult:
    removal: Removal
    trashed: list[Node]
    kept: list[Node]


class BranchService:
    def __init__(
        self,
        repository: MindmapRepository,
        mindmap: MindmapService,
        registry: ElementRegistry,
        projects: Projects,
        database: Database,
        events: EventBus,
        clock: Clock,
        restore: Restore,
    ) -> None:
        self._repository = repository
        self._mindmap = mindmap
        self._registry = registry
        self._projects = projects
        self._database = database
        self._events = events
        self._clock = clock
        self._restore = restore

    # --- Umhängen und Übertragen ----------------------------------------------------------------------------------

    def move_to_map(
        self, ref: str, project_uid: str | None, version: int, tree_uid: str | None, target_uid: str
    ) -> BranchMoved:
        """Hängt den Ast aus seinem Baum weg und unter die Wurzel der Ziel-Map (am Ende). Ist das Ziel der eigene Baum,
        wandert der Ast unter die Wurzel dieses Baums."""
        with self._database.transaction() as tx:
            node = self._branch_node(tx, ref, project_uid)
            source = self._mindmap.tree_of_node(tx, node, tree_uid)
            target = self._mindmap.existing_tree(tx, node.project_uid, target_uid)
            source_placements = self._repository.placements(tx, source.uid)
            if source.uid == target.uid:
                live = self._mindmap.live_set(tx, source.uid)
                rules.check_move(source_placements, node.uid, None, live)
                self._registry.bump_revision(tx, node.uid, version)
                self._repository.upsert_placements(
                    tx, rules.arrange(source_placements, source.uid, node.uid, None, None, live)
                )
                members = [node.uid]
            else:
                members = branch_rules.branch_uids(source_placements, node.uid)
                target_placements = self._repository.placements(tx, target.uid)
                branch_rules.check_target_free(target_placements, members, set(members))
                self._registry.bump_revision(tx, node.uid, version)
                made = branch_rules.graft(source_placements, node.uid, members, target.uid, target_placements)
                self._repository.upsert_placements(tx, made)
                by_node = {p.node_uid: p for p in source_placements}
                self._repository.delete_placements(tx, [by_node[uid] for uid in reversed(members)])
            nodes = self._nodes(tx, members)
        self._mindmap.announce_nodes(nodes, "moved", target.uid)
        return BranchMoved(node, target, len(members))

    def transfer_to_map(
        self, ref: str, project_uid: str | None, version: int, tree_uid: str | None, target_uid: str
    ) -> BranchMoved:
        """Der Ast steht danach auch in der Ziel-Map (unter der Wurzel, am Ende). Nur zwischen verschiedenen Bäumen.
        Unterknoten im Papierkorb gehen nicht mit."""
        with self._database.transaction() as tx:
            node = self._branch_node(tx, ref, project_uid)
            source = self._mindmap.tree_of_node(tx, node, tree_uid)
            target = self._mindmap.existing_tree(tx, node.project_uid, target_uid)
            if source.uid == target.uid:
                raise MindmapViolation(
                    "mindmap_transfer_same_tree",
                    "Ein Ast lässt sich nicht in denselben Baum übertragen",
                    tree=source.uid,
                )
            source_placements = self._repository.placements(tx, source.uid)
            members = branch_rules.branch_uids(source_placements, node.uid, self._mindmap.live_set(tx, source.uid))
            target_placements = self._repository.placements(tx, target.uid)
            branch_rules.check_target_free(target_placements, members, set(members))
            self._registry.bump_revision(tx, node.uid, version)
            self._repository.upsert_placements(
                tx, branch_rules.graft(source_placements, node.uid, members, target.uid, target_placements)
            )
            nodes = self._nodes(tx, members)
        self._mindmap.announce_nodes(nodes, "transferred", target.uid)
        return BranchMoved(node, target, len(members))

    # --- Entfernen und Löschen -----------------------------------------------------------------------------------

    def remove_from_map(self, ref: str, project_uid: str | None, version: int, tree_uid: str | None) -> Removal:
        """„Hier entfernen“: nimmt den Ast nur aus diesem Baum. Verliert ein Knoten damit seine letzte Platzierung,
        kommt er mit den heimatlos gewordenen Unterknoten in den Papierkorb."""
        with self._database.transaction() as tx:
            node = self._branch_node(tx, ref, project_uid)
            tree = self._mindmap.tree_of_node(tx, node, tree_uid)
            result = self._cut(tx, node, [tree.uid], version)
        self._announce(result)
        return result.removal

    def delete_node(self, ref: str, project_uid: str | None, version: int) -> Removal:
        """„Knoten löschen“: nimmt den Ast aus allen Bäumen. Unterknoten, die anderswo noch stehen, bleiben dort."""
        with self._database.transaction() as tx:
            node = self._branch_node(tx, ref, project_uid)
            trees = [p.tree_uid for p in self._repository.placements_of(tx, node.uid)]
            result = self._cut(tx, node, trees, version)
        self._announce(result)
        return result.removal

    # --- Papierkorb ----------------------------------------------------------------------------------------------

    def restore_and_move(
        self,
        ref: str,
        project_uid: str | None,
        version: int,
        tree_uid: str | None,
        parent: str | None,
        position: int | None,
    ) -> Node:
        """Holt einen Knoten aus dem Papierkorb und stellt ihn in einem Schritt an eine neue Stelle: sie ersetzt seine
        Platzierung im Baum; Platzierungen in anderen Bäumen kommen wie vorher zurück."""
        with self._database.transaction() as tx:
            node = self._mindmap.resolve(tx, ref, project_uid)
            if node.deleted_at is None:
                raise MindmapViolation(
                    "mindmap_node_not_deleted", f"{node.label} liegt nicht im Papierkorb", node=node.label
                )
            if node.revision != version:
                raise VersionConflict(
                    "Der Knoten wurde inzwischen geändert",
                    details={"uid": node.uid, "expected": version, "current": node.revision},
                )
            tree = self._tree_to_restore(tx, node, tree_uid)
            placements = self._repository.placements(tx, tree.uid)
            live = self._mindmap.live_set(tx, tree.uid) | {node.uid}
            parent_uid = self._mindmap.parent_uid(tx, parent, node.project_uid)
            rules.check_move(placements, node.uid, parent_uid, live)
            for other in self._repository.placements_of(tx, node.uid):
                if other.tree_uid != tree.uid and other.parent_uid is not None:
                    above = self._repository.get_node(tx, other.parent_uid)
                    if above is not None and above.deleted_at is not None:
                        raise MindmapViolation(
                            "mindmap_parent_in_trash",
                            f"{above.label} liegt im Papierkorb; erst diesen Knoten wiederherstellen",
                            parent=above.label,
                        )
            self._repository.upsert_placements(
                tx, rules.arrange(placements, tree.uid, node.uid, parent_uid, position, live)
            )
        self._restore([node.uid])
        with self._database.transaction() as tx:
            restored = self._repository.get_node(tx, node.uid)
        assert restored is not None
        return restored

    def restore_placement(
        self, ref: str, project_uid: str | None, version: int, tree_uid: str | None
    ) -> PlacementRestored:
        """Setzt einen entfernten Ast wieder in den Baum, in dem er stand: an den alten Parent und die alte Stelle, mit
        den Unterknoten, die mit ihm entfernt wurden. Fehlt der alte Parent, steht er unter der Wurzel der Map."""
        with self._database.transaction() as tx:
            node = self._branch_node(tx, ref, project_uid)
            removed = self._repository.removed_placements_of(tx, node.uid)
            tree = self._removed_tree(tx, node, removed, tree_uid)
            placements = self._repository.placements(tx, tree.uid)
            alive = {n.uid for n in self._repository.nodes_in_tree(tx, tree.uid)}
            group = self._repository.removed_placements(tx, tree.uid)
            alive |= {r.node_uid for r in group if self._is_alive(tx, r.node_uid)}
            plan = branch_rules.plan_restore(group, node.uid, placements, alive)
            self._registry.bump_revision(tx, node.uid, version)
            self._repository.upsert_placements(tx, plan.placements)
            restored = self._nodes(tx, plan.restored)
        self._mindmap.announce_nodes(restored, "restored", tree.uid)
        return PlacementRestored(node, tree, len(plan.restored), len(plan.skipped), plan.parent_uid, plan.fell_back)

    # --- Lesen ---------------------------------------------------------------------------------------------------

    def node_trees(self, ref: str, project_uid: str | None) -> list[NodeTree]:
        """Die Bäume außerhalb des Papierkorbs, in denen der Knoten steht: der Projektbaum zuerst, dann die freien Maps
        in der Reihenfolge des Anlegens."""
        with self._database.transaction() as tx:
            node = self._mindmap.resolve(tx, ref, project_uid)
            project = self._projects.get(tx, node.project_uid)
            found: list[NodeTree] = []
            for placement in self._repository.placements_of(tx, node.uid):
                tree = self._repository.get_tree(tx, placement.tree_uid)
                if tree is not None and tree.deleted_at is None:
                    name = (project.name if project else "") if tree.kind == TREE_PROJECT else tree.name or ""
                    found.append(NodeTree(tree, name, placement.parent_uid))
        return sorted(found, key=lambda t: (t.tree.kind != TREE_PROJECT, t.tree.uid))

    def removed_from(self, ref: str, project_uid: str | None) -> list[RemovedFrom]:
        """Die Bäume (ohne Papierkorb), aus denen der Knoten entfernt wurde und in die er zurück kann („Früher in …“):
        der Projektbaum zuerst, dann die freien Maps."""
        with self._database.transaction() as tx:
            node = self._mindmap.resolve(tx, ref, project_uid)
            project = self._projects.get(tx, node.project_uid)
            found: list[RemovedFrom] = []
            for removed in self._repository.removed_placements_of(tx, node.uid):
                tree = self._repository.get_tree(tx, removed.tree_uid)
                if tree is None or tree.deleted_at is not None:
                    continue
                group = self._repository.removed_placements(tx, tree.uid)
                placements = self._repository.placements(tx, tree.uid)
                alive = {n.uid for n in self._repository.nodes_in_tree(tx, tree.uid)}
                alive |= {r.node_uid for r in group if self._is_alive(tx, r.node_uid)}
                try:
                    plan = branch_rules.plan_restore(group, node.uid, placements, alive)
                except MindmapViolation:
                    continue
                name = (project.name if project else "") if tree.kind == TREE_PROJECT else tree.name or ""
                found.append(RemovedFrom(tree, name, removed.parent_uid, not plan.fell_back, len(plan.restored)))
        return sorted(found, key=lambda t: (t.tree.kind != TREE_PROJECT, t.tree.uid))

    # --- Hilfen --------------------------------------------------------------------------------------------------

    def _branch_node(self, tx: Transaction, ref: str, project_uid: str | None) -> Node:
        """Der Knoten, dessen Ast bewegt wird: nicht die Wurzel einer Map, nicht im Papierkorb."""
        if self._repository.get_tree(tx, ref) is not None:
            raise MindmapViolation("mindmap_root_fixed", "Die Wurzel einer Map lässt sich nicht bewegen", tree=ref)
        node = self._mindmap.resolve(tx, ref, project_uid)
        self._mindmap.require_alive(node)
        return node

    def _is_alive(self, tx: Transaction, uid: str) -> bool:
        member = self._repository.get_node(tx, uid)
        return member is not None and member.deleted_at is None

    def _removed_tree(
        self, tx: Transaction, node: Node, removed: Sequence[RemovedPlacement], tree_uid: str | None
    ) -> Tree:
        """Der Baum, in den der Knoten zurück soll: er darf nicht im Papierkorb liegen. Ohne Angabe muss es genau einen
        geben. Steht der Knoten dort schon wieder, wird abgelehnt."""
        if tree_uid is None:
            if not removed:
                raise MindmapViolation(
                    "mindmap_nothing_to_restore", "Für diesen Knoten ist keine Platzierung gemerkt", node=node.label
                )
            if len(removed) > 1:
                raise InvalidInput(
                    "Der Knoten wurde aus mehreren Bäumen entfernt; tree angeben", details={"field": "tree"}
                )
            tree_uid = removed[0].tree_uid
        tree = self._mindmap.existing_tree(tx, node.project_uid, tree_uid)
        if all(r.tree_uid != tree.uid for r in removed):
            if any(p.tree_uid == tree.uid for p in self._repository.placements_of(tx, node.uid)):
                raise MindmapViolation(
                    "mindmap_node_in_tree", "Der Knoten steht in diesem Baum schon wieder", node=node.label
                )
            raise MindmapViolation(
                "mindmap_nothing_to_restore",
                "Für diesen Knoten ist in diesem Baum keine Platzierung gemerkt",
                node=node.label,
            )
        return tree

    def _nodes(self, tx: Transaction, uids: Sequence[str]) -> list[Node]:
        return [n for uid in uids if (n := self._repository.get_node(tx, uid)) is not None]

    def _tree_to_restore(self, tx: Transaction, node: Node, tree_uid: str | None) -> Tree:
        placements = self._repository.placements_of(tx, node.uid)
        trees = [t for p in placements if (t := self._repository.get_tree(tx, p.tree_uid)) and t.deleted_at is None]
        if tree_uid is not None:
            chosen = next((t for t in trees if t.uid == tree_uid), None)
            if chosen is None:
                raise MindmapViolation(
                    "mindmap_node_not_in_tree", "Der Knoten steht nicht in diesem Baum", node=node.label
                )
            return chosen
        if len(trees) != 1:
            raise InvalidInput(
                "Der Knoten steht in keinem oder mehreren Bäumen; tree angeben", details={"field": "tree"}
            )
        return trees[0]

    def _cut(self, tx: Transaction, node: Node, tree_uids: Sequence[str], version: int) -> CutResult:
        placements = {uid: self._repository.placements(tx, uid) for uid in dict.fromkeys(tree_uids)}
        members = {uid for p in placements.values() for uid in branch_rules.branch_uids(p, node.uid)}
        standing = self._repository.live_trees_of(tx, sorted(members))
        cut = branch_rules.plan_cuts(placements, node.uid, standing)
        self._registry.bump_revision(tx, node.uid, version)
        self._repository.upsert_placements(tx, cut.reparented)
        # Entfernte Platzierungen bleiben gemerkt (`TASK-066`): Baum, Parent und Stelle, in einer Gruppe mit dem Ast.
        self._repository.mark_removed(tx, cut.removed, node.uid)
        at = self._clock.now()
        trashed: list[Node] = []
        for uid in cut.homeless:
            member = self._repository.get_node(tx, uid)
            if member is not None and member.deleted_at is None:
                self._registry.mark_deleted(tx, uid, at)
                trashed.append(member)
        kept = [n for n in self._nodes(tx, sorted(members)) if n.uid not in cut.homeless and n.deleted_at is None]
        return CutResult(Removal(node, len(trashed), len(kept)), trashed, kept)

    def _announce(self, result: CutResult) -> None:
        self._mindmap.announce_nodes(result.trashed, "deleted")
        self._mindmap.announce_nodes(result.kept, "removed")

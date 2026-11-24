"""Anwendungsfälle der Zuordnung: Items und Memos an Knoten hängen, Zahlen und Zustand je Knoten.

Eine Zuordnung ist eine Verknüpfung `Knoten → Item/Memo` der Rolle `node` in `workspace_links`. Die Regel „ein Item
hängt an höchstens einem Knoten“ liegt in `domain/assignment.py`; wirksamer Knoten, Summen und Zustand werden bei
jeder Abfrage berechnet und nicht gespeichert. Wandert ein Knoten in den Papierkorb, rührt das die Verknüpfungen nicht
an: das Ergebnis ändert sich allein durch die Rechnung, und das Wiederherstellen stellt alles wieder her.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from viewer.core.application.ports import Database, EventBus, Transaction
from viewer.core.domain.errors import InvalidInput, NotFound
from viewer.core.domain.events import Event
from viewer.plugins.mindmap.application.ports import BacklogItem, BacklogItems, MindmapRepository
from viewer.plugins.mindmap.application.service import NODE_TOPIC, MindmapService
from viewer.plugins.mindmap.domain import assignment as rules
from viewer.plugins.mindmap.domain import tree as rules_tree
from viewer.plugins.mindmap.domain.assignment import ItemFact, LinkFact, NodeStats, Overview
from viewer.plugins.mindmap.domain.model import MindmapViolation, Node
from viewer.plugins.workspace import Element, ElementRegistry, Links

ROLE = "node"
#: Elementtypen, die an einen Knoten gehängt werden: Items des Backlogs und Memos.
ITEM_KINDS = ("epic", "story", "task")
MEMO_KIND = "memo"
#: Die Status des Backlogs (für die Prüfung des Statusfilters).
ITEM_STATUSES = ("Open", "In progress", "Awaiting confirmation", "Completed", "Rejected")


def _facts(items: list[BacklogItem]) -> list[ItemFact]:
    return [ItemFact(i.uid, i.parent_uid, i.status, i.deleted, i.dependencies) for i in items]


@dataclass(frozen=True)
class TreeStats:
    """Zahlen und Zustand je lebendem Knoten des Baums und die Items ohne Knoten."""

    stats: dict[str, NodeStats]
    unassigned: list[BacklogItem]
    #: Abhängigkeiten zwischen Knoten, zusammengefasst (Statusfilter wie bei den Zahlen).
    links: list[LinkFact]


@dataclass(frozen=True)
class NodeContent:
    """Das Detail eines Knotens: die Items, deren wirksamer Knoten er ist (nach dem Statusfilter), und seine Memos."""

    node: Node
    items: list[BacklogItem]
    memos: list[Element] = field(default_factory=list)
    #: `uid`s der Items aus `items`, die diesem Knoten eigens zugeordnet sind (die übrigen erben ihn).
    explicit: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ItemNode:
    """Wo ein Item hängt: `node` ist der wirksame Knoten (`None`: nicht zugeordnet); `explicit` sagt, ob das Item
    eigens an ihn gehängt ist oder ihn von seinem Parent erbt."""

    item: BacklogItem
    node: Node | None
    explicit: bool


def check_statuses(statuses: list[str]) -> list[str]:
    unknown = [s for s in statuses if s not in ITEM_STATUSES]
    if unknown:
        raise InvalidInput(
            f"Unbekannter Status '{unknown[0]}'", details={"field": "statuses", "allowed": list(ITEM_STATUSES)}
        )
    return statuses


class AssignmentService:
    def __init__(
        self,
        repository: MindmapRepository,
        backlog: BacklogItems,
        mindmap: MindmapService,
        links: Links,
        registry: ElementRegistry,
        database: Database,
        events: EventBus,
    ) -> None:
        self._repository = repository
        self._backlog = backlog
        self._mindmap = mindmap
        self._links = links
        self._registry = registry
        self._database = database
        self._events = events

    # --- Schreiben ------------------------------------------------------------------------------------------------

    def assign_item(self, item_ref: str, node_ref: str, project_uid: str | None, replace: bool) -> Node:
        """Hängt das Item an den Knoten. Hängt es schon an einem anderen, wird das abgewiesen; mit `replace` ersetzt
        der neue Knoten den alten ausdrücklich."""
        with self._database.transaction() as tx:
            node = self._mindmap.resolve(tx, node_ref, project_uid)
            self._mindmap.require_alive(node)
            item = self._element(tx, item_ref, node.project_uid, ITEM_KINDS)
            current = self._nodes_of(tx, item.uid)
            drop = rules.check_assign([n for n, _ in current], node.uid, replace)
            removed = [link for n, link in current if n in drop]
            for link in removed:
                self._links.remove(tx, link)
            added = None
            if node.uid not in {n for n, _ in current}:
                added = self._links.add(tx, node.uid, item.uid, ROLE)
        self._announce(node, removed_nodes=drop, added=added is not None)
        return node

    def unassign_item(self, item_ref: str, project_uid: str | None) -> None:
        """Löst die eigene Zuordnung des Items; es erbt danach wieder von seinem Parent."""
        with self._database.transaction() as tx:
            item = self._element(tx, item_ref, project_uid, ITEM_KINDS)
            current = self._nodes_of(tx, item.uid)
            if not current:
                raise NotFound(f"{item.label} ist keinem Knoten eigens zugeordnet", details={"item": item.label})
            for _, link in current:
                self._links.remove(tx, link)
            nodes = [n for n, _ in current]
        self._announce_nodes(nodes)

    def link_memo(self, memo_ref: str, node_ref: str, project_uid: str | None) -> Node:
        """Verlinkt das Memo mit dem Knoten; ein Memo darf an mehrere Knoten hängen. Doppelt verlinken tut nichts."""
        with self._database.transaction() as tx:
            node = self._mindmap.resolve(tx, node_ref, project_uid)
            self._mindmap.require_alive(node)
            memo = self._element(tx, memo_ref, node.project_uid, (MEMO_KIND,))
            existing = {n for n, _ in self._nodes_of(tx, memo.uid)}
            if node.uid not in existing:
                self._links.add(tx, node.uid, memo.uid, ROLE)
        self._announce_nodes([node.uid], change="linked")
        return node

    def unlink_memo(self, memo_ref: str, node_ref: str, project_uid: str | None) -> None:
        with self._database.transaction() as tx:
            node = self._mindmap.resolve(tx, node_ref, project_uid)
            memo = self._element(tx, memo_ref, node.project_uid, (MEMO_KIND,))
            found = [link for n, link in self._nodes_of(tx, memo.uid) if n == node.uid]
            if not found:
                raise NotFound(f"{memo.label} ist nicht mit {node.label} verlinkt", details={"memo": memo.label})
            for link in found:
                self._links.remove(tx, link)
        self._announce_nodes([node.uid], change="unlinked")

    # --- Lesen ----------------------------------------------------------------------------------------------------

    def stats(self, project_uid: str, statuses: list[str], tree_uid: str | None = None) -> TreeStats:
        """Anzahl, Fortschritt und Zustand je Knoten des Projektbaums oder einer freien Map und die Items ohne
        Knoten. „Nicht zugeordnet“ gibt es nur im Projektbaum; in einer freien Map ist die Liste leer."""
        check_statuses(statuses)
        with self._database.transaction() as tx:
            overview, items, _, _ = self._overview(tx, project_uid, statuses, tree_uid)
        loose = set(overview.unassigned) if tree_uid is None else set()
        links = rules.dependency_links(_facts(items), overview.effective, statuses)
        # Die Items ohne Knoten in der Reihenfolge des Backlogs
        return TreeStats(overview.stats, [i for i in items if i.uid in loose], links)

    def node_content(
        self,
        node_ref: str,
        project_uid: str | None,
        statuses: list[str],
        tree_uid: str | None = None,
        include_subnodes: bool = False,
    ) -> NodeContent:
        """Die Items des Knotens; mit `include_subnodes` auch die seiner Unterknoten (dann stimmt die Liste mit der
        Zahl am Knoten überein). Die Memos sind immer nur die des Knotens."""
        check_statuses(statuses)
        with self._database.transaction() as tx:
            node = self._mindmap.resolve(tx, node_ref, project_uid)
            overview, items, live, parent_of = self._overview(tx, node.project_uid, statuses, tree_uid)
            wanted = rules.subtree_nodes(node.uid, live, parent_of) if include_subnodes else {node.uid}
            shown = [
                i
                for i in items
                if not i.deleted and overview.effective.get(i.uid) in wanted and (not statuses or i.status in statuses)
            ]
            memos = self._memos_of(tx, node.uid)
            explicit = frozenset(i.uid for i in shown if any(n in wanted for n, _ in self._nodes_of(tx, i.uid)))
        return NodeContent(node, shown, memos, explicit)

    def item_node(self, item_ref: str, project_uid: str | None) -> ItemNode:
        with self._database.transaction() as tx:
            element = self._element(tx, item_ref, project_uid, ITEM_KINDS, allow_deleted=True)
            overview, items, _, _ = self._overview(tx, element.project_uid, [])
            item = next(i for i in items if i.uid == element.uid)
            node_uid = overview.effective.get(item.uid)
            node = self._repository.get_node(tx, node_uid) if node_uid else None
            explicit = any(n == node_uid for n, _ in self._nodes_of(tx, item.uid))
        return ItemNode(item, node, explicit and node is not None)

    def memo_nodes(self, memo_ref: str, project_uid: str | None) -> list[Node]:
        """Die Knoten, mit denen das Memo verlinkt ist; Knoten im Papierkorb fehlen (der Link ruht)."""
        with self._database.transaction() as tx:
            memo = self._element(tx, memo_ref, project_uid, (MEMO_KIND,), allow_deleted=True)
            nodes = [self._repository.get_node(tx, n) for n, _ in self._nodes_of(tx, memo.uid)]
        return [n for n in nodes if n is not None and n.deleted_at is None]

    # --- Hilfen ---------------------------------------------------------------------------------------------------

    def _overview(
        self, tx: Transaction, project_uid: str, statuses: list[str], tree_uid: str | None = None
    ) -> tuple[Overview, list[BacklogItem], set[str], dict[str, str | None]]:
        items = self._backlog.list_items(tx, project_uid)
        tree = (
            self._repository.get_tree(tx, tree_uid) if tree_uid else self._repository.tree_of_project(tx, project_uid)
        )
        if tree is not None:
            rules_tree.check_project(tree.project_uid, project_uid)
            if tree.deleted_at is not None:
                raise MindmapViolation("mindmap_tree_deleted", "Die Map liegt im Papierkorb", tree=tree.uid)
        live: set[str] = set()
        parent_of: dict[str, str | None] = {}
        assigned: dict[str, str] = {}
        if tree is not None:
            nodes = self._repository.nodes_in_tree(tx, tree.uid, include_deleted=True)
            live = {n.uid for n in nodes if n.deleted_at is None}
            parent_of = {p.node_uid: p.parent_uid for p in self._repository.placements(tx, tree.uid)}
            wanted = {i.uid for i in items}
            for node in nodes:
                for view in self._links.outgoing(tx, node.uid):
                    if view.link.role == ROLE and view.element.uid in wanted:
                        assigned.setdefault(view.element.uid, node.uid)
        return rules.overview(_facts(items), assigned, live, parent_of, statuses), items, live, parent_of

    def _element(
        self, tx: Transaction, ref: str, project_uid: str | None, kinds: tuple[str, ...], *, allow_deleted: bool = False
    ) -> Element:
        element = self._registry.get(tx, ref)
        if element is None and project_uid is not None:
            element = self._registry.find_by_label(tx, project_uid, ref.strip())
        if element is None:
            if project_uid is None:
                raise InvalidInput(
                    f"'{ref}' ist keine uid; für ein Label braucht es das Projekt", details={"field": "project"}
                )
            raise NotFound(f"{ref} gibt es nicht", details={"ref": ref})
        if element.kind not in kinds:
            raise InvalidInput(
                f"{element.label} ist kein {'Memo' if kinds == (MEMO_KIND,) else 'Item'}", details={"ref": ref}
            )
        if project_uid is not None and element.project_uid != project_uid:
            raise MindmapViolation("mindmap_other_project", f"{element.label} gehört zu einem anderen Projekt")
        if element.deleted_at is not None and not allow_deleted:
            raise MindmapViolation("mindmap_item_deleted", f"{element.label} liegt im Papierkorb", ref=element.label)
        return element

    def _nodes_of(self, tx: Transaction, element_uid: str) -> list[tuple[str, str]]:
        """(Knoten-uid, Verknüpfungs-uid) der Zuordnungen des Elements."""
        return sorted(
            ((v.element.uid, v.link.uid) for v in self._links.incoming(tx, element_uid) if v.link.role == ROLE),
        )

    def _memos_of(self, tx: Transaction, node_uid: str) -> list[Element]:
        views = [v for v in self._links.outgoing(tx, node_uid) if v.link.role == ROLE and v.element.kind == MEMO_KIND]
        return [v.element for v in views if v.element.deleted_at is None]

    def _announce(self, node: Node, removed_nodes: list[str], added: bool) -> None:
        self._announce_nodes([node.uid, *removed_nodes], change="assigned" if added else "unchanged")

    def _announce_nodes(self, uids: list[str], change: str = "unassigned") -> None:
        if change == "unchanged":
            return
        with self._database.transaction() as tx:
            nodes = [n for uid in dict.fromkeys(uids) if (n := self._repository.get_node(tx, uid)) is not None]
        for node in nodes:
            payload: dict[str, object] = {"uid": node.uid, "project_uid": node.project_uid, "change": change}
            self._events.publish(Event(NODE_TOPIC, payload, public=True))

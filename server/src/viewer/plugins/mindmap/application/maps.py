"""Maps eines Projekts: der Projektbaum und die freien Maps (`TASK-062`).

Eine freie Map gehört zu einem Projekt, hat einen Namen und wandert beim Löschen in den Papierkorb von `workspace`
(als Eintrag, den das Plugin selbst hält: `MapTrash`). Knoten, die nur in dieser Map stehen, gehen mit und kommen mit
ihr zurück; sie tragen denselben Löschzeitpunkt wie die Map. Knoten, die auch in einem anderen Baum stehen, bleiben
dort unverändert (Platzierungen sind gleichberechtigt). Der Projektbaum ist einmalig und nicht löschbar.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime

from viewer.core.application.ports import Clock, Database, EventBus, Transaction
from viewer.core.domain.errors import NotFound
from viewer.core.domain.events import Event
from viewer.plugins.mindmap.application.ports import MindmapRepository
from viewer.plugins.mindmap.application.service import NODE_TOPIC
from viewer.plugins.mindmap.domain import tree as rules
from viewer.plugins.mindmap.domain.model import TREE_FREE, MindmapViolation, Node, Tree
from viewer.plugins.workspace import ElementRegistry, Project, Projects, TrashEntry

MAP_TOPIC = "mindmap.map.changed"
#: Art des Eintrags im Papierkorb.
MAP_ENTRY = "mindmap_map"
MAP_LABEL = "MAP"


@dataclass(frozen=True)
class MapView:
    """Eine Map der Liste. `tree` ist `None` beim Projektbaum, solange noch kein Knoten angelegt wurde."""

    project_uid: str
    kind: str
    #: Bei freien Maps der Name, beim Projektbaum der Name des Projekts.
    name: str
    tree: Tree | None
    node_count: int = 0
    #: Davon Knoten, die auch in einem anderen Baum stehen (bleiben dort erhalten, wenn die Map gelöscht wird).
    shared_count: int = 0


@dataclass(frozen=True)
class MapDeleted:
    tree_uid: str
    #: Die Knoten, die mit der Map in den Papierkorb gingen.
    nodes_deleted: int
    #: Die Knoten, die auch in einem anderen Baum stehen und dort erhalten bleiben.
    kept_elsewhere: int


def trash_map(
    repository: MindmapRepository,
    registry: ElementRegistry,
    tx: Transaction,
    tree: Tree,
    at: datetime,
    expected: int | None,
) -> tuple[list[Node], int]:
    """Legt die freie Map mit den lebenden Knoten, die in keinem anderen Baum stehen, in den Papierkorb (mit `expected`
    wird ihre Version geprüft). Gibt diese Knoten und die Zahl der Knoten zurück, die auch anderswo stehen und dort
    bleiben. Gemeinsam für die API und den Sync."""
    rules.check_deletable(tree)
    shared = repository.shared_count(tx, tree.uid)
    own = [
        n
        for n in repository.nodes_in_tree(tx, tree.uid)
        if all(p.tree_uid == tree.uid for p in repository.placements_of(tx, n.uid))
    ]
    repository.set_tree_deleted(tx, tree.uid, at, expected)
    for node in own:
        registry.mark_deleted(tx, node.uid, at)
    return own, shared


class MapService:
    def __init__(
        self,
        repository: MindmapRepository,
        registry: ElementRegistry,
        projects: Projects,
        database: Database,
        events: EventBus,
        clock: Clock,
        new_uid: Callable[[], str],
    ) -> None:
        self._repository = repository
        self._registry = registry
        self._projects = projects
        self._database = database
        self._events = events
        self._clock = clock
        self._new_uid = new_uid

    def list_maps(self, project_uid: str) -> list[MapView]:
        """Der Projektbaum zuerst, dann die freien Maps in der Reihenfolge des Anlegens."""
        with self._database.transaction() as tx:
            project = self._require_project(tx, project_uid)
            project_tree = self._repository.tree_of_project(tx, project_uid)
            views = [self._view(tx, project.name, project_tree, project_uid, "project")]
            for tree in self._repository.free_maps(tx, project_uid):
                views.append(self._view(tx, tree.name or "", tree, project_uid, TREE_FREE))
        return views

    def get_map(self, tree_uid: str) -> MapView:
        with self._database.transaction() as tx:
            tree = self._require_tree(tx, tree_uid)
            project = self._require_project(tx, tree.project_uid)
            return self._view(tx, tree.name or project.name, tree, tree.project_uid, tree.kind)

    def create_map(self, project_uid: str, name: object) -> str:
        clean = rules.clean_map_name(name)
        with self._database.transaction() as tx:
            self._require_project(tx, project_uid)
            rules.check_map_name_free(clean, self._free_names(tx, project_uid))
            tree = Tree(self._new_uid(), project_uid, TREE_FREE, clean)
            self._repository.insert_tree(tx, tree)
        self._map_changed(tree, "created")
        return tree.uid

    def rename_map(self, tree_uid: str, version: int, name: object) -> str:
        clean = rules.clean_map_name(name)
        with self._database.transaction() as tx:
            tree = self._require_tree(tx, tree_uid)
            rules.check_renamable(tree)
            self._require_alive(tree)
            rules.check_map_name_free(clean, self._free_names(tx, tree.project_uid, except_uid=tree.uid))
            self._repository.rename_tree(tx, tree.uid, clean, version)
        self._map_changed(tree, "renamed")
        return tree.uid

    def delete_map(self, tree_uid: str, version: int) -> MapDeleted:
        """Legt die freie Map mit den Knoten, die nur in ihr stehen, in den Papierkorb."""
        with self._database.transaction() as tx:
            tree = self._require_tree(tx, tree_uid)
            rules.check_deletable(tree)
            self._require_alive(tree)
            own, shared = trash_map(self._repository, self._registry, tx, tree, self._clock.now(), version)
        self._map_changed(tree, "deleted")
        self._nodes_changed(own, "deleted")
        return MapDeleted(tree.uid, len(own), shared)

    def announce_entries(self, uids: Sequence[str], change: str) -> None:
        """Meldet Maps, die der Papierkorb von `workspace` zurückgeholt hat, samt ihren Knoten."""
        if change != "restored":
            return
        for uid in uids:
            with self._database.transaction() as tx:
                tree = self._repository.get_tree(tx, uid)
                nodes = self._repository.nodes_in_tree(tx, uid) if tree else []
            if tree is not None:
                self._map_changed(tree, "restored")
                self._nodes_changed(nodes, "restored")

    # --- Hilfen ---------------------------------------------------------------------------------------------------

    def _view(self, tx: Transaction, name: str, tree: Tree | None, project_uid: str, kind: str) -> MapView:
        if tree is None:
            return MapView(project_uid, kind, name, None)
        return MapView(
            project_uid,
            kind,
            name,
            tree,
            self._repository.node_count(tx, tree.uid),
            self._repository.shared_count(tx, tree.uid),
        )

    def _free_names(self, tx: Transaction, project_uid: str, except_uid: str | None = None) -> list[str]:
        return [t.name or "" for t in self._repository.free_maps(tx, project_uid) if t.uid != except_uid]

    def _require_project(self, tx: Transaction, project_uid: str) -> Project:
        project = self._projects.get(tx, project_uid)
        if project is None or project.deleted_at is not None:
            raise NotFound(f"Projekt {project_uid} gibt es nicht", details={"project": project_uid})
        return project

    def _require_tree(self, tx: Transaction, tree_uid: str) -> Tree:
        tree = self._repository.get_tree(tx, tree_uid)
        if tree is None:
            raise NotFound(f"Map {tree_uid} gibt es nicht", details={"tree": tree_uid})
        return tree

    @staticmethod
    def _require_alive(tree: Tree) -> None:
        if tree.deleted_at is not None:
            raise MindmapViolation("mindmap_tree_deleted", "Die Map liegt im Papierkorb", tree=tree.uid)

    def _map_changed(self, tree: Tree, change: str) -> None:
        payload: dict[str, object] = {"tree_uid": tree.uid, "project_uid": tree.project_uid, "change": change}
        self._events.publish(Event(MAP_TOPIC, payload, public=True))

    def _nodes_changed(self, nodes: Sequence[Node], change: str) -> None:
        for node in nodes:
            payload: dict[str, object] = {"uid": node.uid, "project_uid": node.project_uid, "change": change}
            self._events.publish(Event(NODE_TOPIC, payload, public=True))


class MapTrash:
    """Die gelöschten freien Maps als Einträge des Papierkorbs (`TrashSource` von `workspace`)."""

    def __init__(self, repository: MindmapRepository, registry: ElementRegistry, projects: Projects) -> None:
        self._repository = repository
        self._registry = registry
        self._projects = projects

    def list_deleted(self, tx: Transaction, project_uids: Sequence[str] | None, query: str) -> list[TrashEntry]:
        needle = query.strip().casefold()
        entries = [_entry(tree) for tree in self._repository.deleted_maps(tx, project_uids)]
        return [e for e in entries if not needle or needle in e.title.casefold() or needle in e.label.casefold()]

    def get(self, tx: Transaction, uid: str) -> TrashEntry | None:
        tree = self._repository.get_tree(tx, uid)
        return _entry(tree) if tree is not None and tree.deleted_at is not None else None

    def restore(self, tx: Transaction, uid: str) -> None:
        tree = self._repository.get_tree(tx, uid)
        assert tree is not None and tree.deleted_at is not None
        project = self._projects.get(tx, tree.project_uid)
        if project is None or project.deleted_at is not None:
            raise MindmapViolation("mindmap_project_in_trash", "Das Projekt der Map liegt im Papierkorb", tree=tree.uid)
        taken = [t.name or "" for t in self._repository.free_maps(tx, tree.project_uid)]
        rules.check_map_name_free(tree.name or "", taken)
        for node in self._repository.nodes_in_tree(tx, tree.uid, include_deleted=True):
            if node.deleted_at is not None and node.deleted_at == tree.deleted_at:
                self._registry.restore(tx, node.uid)  # nur, was mit der Map ging
        self._repository.set_tree_deleted(tx, tree.uid, None)

    def purge(self, tx: Transaction, uid: str) -> None:
        tree = self._repository.get_tree(tx, uid)
        assert tree is not None
        own = [
            n
            for n in self._repository.nodes_in_tree(tx, uid, include_deleted=True)
            if n.deleted_at is not None
            and n.deleted_at == tree.deleted_at
            and all(p.tree_uid == uid for p in self._repository.placements_of(tx, n.uid))
        ]
        self._repository.delete_tree(tx, uid)  # zuerst die Platzierungen, dann die Knoten
        for node in own:
            self._repository.delete_node(tx, node.uid)
            self._registry.purge(tx, node.uid)


def _entry(tree: Tree) -> TrashEntry:
    return TrashEntry(tree.uid, tree.project_uid, MAP_ENTRY, MAP_LABEL, tree.name or "", tree.deleted_at)

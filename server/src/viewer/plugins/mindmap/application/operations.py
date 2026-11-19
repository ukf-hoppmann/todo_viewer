"""Ein- und Ausgaben und Operationen des Plugins `mindmap` (HTTP + MCP).

Knoten in den Papierkorb legen und wiederherstellen gehen über `workspace` (`workspace_delete_element` mit `cascade`,
`workspace_restore_elements`): ein Ast mit seinen Kindern wandert zusammen in den Papierkorb und kommt zusammen zurück.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from viewer.core.domain.operations import HttpBinding, Operation
from viewer.plugins.mindmap.application.assignments import AssignmentService, ItemNode, NodeContent, TreeStats
from viewer.plugins.mindmap.application.branches import BranchService, NodeTree, Removal
from viewer.plugins.mindmap.application.documents import DocumentService
from viewer.plugins.mindmap.application.maps import MapDeleted, MapService, MapView
from viewer.plugins.mindmap.application.ports import BacklogItem, Document
from viewer.plugins.mindmap.application.service import MindmapService, NodeView, TreeView


class MindmapServices:
    def __init__(
        self,
        mindmap: MindmapService,
        documents: DocumentService,
        assignments: AssignmentService,
        maps: MapService,
        branches: BranchService,
    ) -> None:
        self.mindmap = mindmap
        self.documents = documents
        self.assignments = assignments
        self.maps = maps
        self.branches = branches


@dataclass(frozen=True)
class NodeOut:
    uid: str
    project_uid: str
    label: str
    title: str
    #: Der Text des Knotens; leer, wenn er keinen hat.
    text: str | None
    tree_uid: str
    #: `uid` des Parent-Knotens in diesem Baum; leer unter der Wurzel (dem Projekt).
    parent_uid: str | None
    #: Stelle unter den Geschwistern (ab 0).
    position: int
    #: Versionstoken für schreibende Operationen.
    version: int
    #: Die Namen der Dokumente des Knotens, die Notiz zuerst; leer, wenn er keine hat.
    documents: list[str]
    #: Die Markierung des Knotens (`discarded` oder `later`); leer, wenn er keine trägt. Sie gilt nur für ihn selbst
    #: und ändert weder Summen noch Zustand.
    mark: str | None = None


@dataclass(frozen=True)
class TreeNodeOut(NodeOut):
    """Ein Knoten im Baum mit den Zahlen über sich und seine Unterknoten (jedes Item zählt genau einmal)."""

    #: Anzahl der zählenden Items: nicht im Papierkorb und vom Statusfilter durchgelassen.
    total: int = 0
    #: Davon erledigt (`Completed`): der Fortschritt ist `done` von `total`.
    done: int = 0
    #: `idea`, `planned`, `in_progress` oder `done`; unabhängig vom Statusfilter, `Rejected` zählt nicht.
    state: str = "idea"
    #: In wie vielen Bäumen (ohne Papierkorb) der Knoten steht; mehr als 1: ein übertragener Ast.
    tree_count: int = 1


@dataclass(frozen=True)
class ItemRefOut:
    uid: str
    label: str
    type: str
    title: str
    status: str


@dataclass(frozen=True)
class LinkOut:
    from_node: str
    to_node: str
    count: int


@dataclass(frozen=True)
class TreeOut:
    project_uid: str
    #: Leer, solange im Projekt noch kein Knoten angelegt ist.
    tree_uid: str | None
    #: Die Knoten, Eltern vor Kindern und je Parent nach Stelle; Knoten im Papierkorb fehlen.
    nodes: list[TreeNodeOut]
    #: Die Items ohne Knoten, die der Statusfilter durchlässt (die Seitenansicht „Nicht zugeordnet“).
    unassigned: list[ItemRefOut]
    #: Abhängigkeiten zwischen Knoten: `count` Abhängigkeiten von Items in `to_node` auf Items in `from_node`
    #: (Linie vom benötigten zum abhängigen Thema); nur innerhalb des Projekts, sortiert.
    links: list[LinkOut]


@dataclass(frozen=True)
class MapOut:
    """Eine Map eines Projekts: der Projektbaum (zuerst) oder eine freie Map."""

    project_uid: str
    #: `project` oder `free`.
    kind: str
    #: Bei freien Maps der Name, beim Projektbaum der Name des Projekts.
    name: str
    #: Leer beim Projektbaum, solange im Projekt noch kein Knoten angelegt ist.
    tree_uid: str | None
    #: Die Knoten der Map außerhalb des Papierkorbs.
    node_count: int
    #: Davon Knoten, die auch in einem anderen Baum stehen und beim Löschen der Map dort erhalten bleiben.
    shared_count: int
    #: Versionstoken für Umbenennen und Löschen; beim noch leeren Projektbaum 0.
    version: int


@dataclass(frozen=True)
class MapDeletedOut:
    tree_uid: str
    #: Die Knoten, die mit der Map in den Papierkorb gingen (nur in ihr stehende).
    nodes_deleted: int
    #: Die Knoten, die auch in einem anderen Baum stehen und dort erhalten bleiben.
    kept_elsewhere: int = 0


@dataclass(frozen=True)
class ListMaps:
    #: `uid` des Projekts.
    project: str


@dataclass(frozen=True)
class CreateMap:
    project: str
    name: str


@dataclass(frozen=True)
class RenameMap:
    #: `uid` der freien Map.
    tree: str
    version: int
    name: str


@dataclass(frozen=True)
class DeleteMap:
    #: `uid` der freien Map; sie geht in den Papierkorb und lässt sich dort wiederherstellen.
    tree: str
    version: int


def map_out(view: MapView) -> MapOut:
    return MapOut(
        view.project_uid,
        view.kind,
        view.name,
        view.tree.uid if view.tree else None,
        view.node_count,
        view.shared_count,
        view.tree.revision if view.tree else 0,
    )


@dataclass(frozen=True)
class GetTree:
    #: `uid` des Projekts.
    project: str
    #: Eine freie Map des Projekts; ohne Angabe der Projektbaum.
    tree: str | None = None
    #: Statusfilter des Backlogs, kommagetrennt (`Open,In progress`); ohne Angabe zählen alle Items.
    statuses: str | None = None


@dataclass(frozen=True)
class GetNode:
    ref: str
    project: str | None = None
    tree: str | None = None


@dataclass(frozen=True)
class CreateNode:
    project: str
    title: str
    text: str | None = None
    #: Parent-Knoten (uid oder Label); ohne Angabe steht der Knoten unter der Wurzel.
    parent: str | None = None
    #: Stelle unter den Geschwistern; ohne Angabe ans Ende.
    position: int | None = None
    #: Die freie Map, in der der Knoten angelegt wird; ohne Angabe der Projektbaum.
    tree: str | None = None


@dataclass(frozen=True)
class UpdateNode:
    ref: str
    version: int
    #: Neuer Titel; ohne Angabe bleibt er.
    title: str | None = None
    #: Neuer Text; ohne Angabe bleibt er, ein leerer Text löscht ihn.
    text: str | None = None
    #: Neue Markierung (`discarded` oder `later`); ohne Angabe bleibt sie, eine leere löscht sie.
    mark: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class MoveNode:
    ref: str
    version: int
    #: Neuer Parent (uid oder Label); ohne Angabe unter die Wurzel.
    parent: str | None = None
    #: Stelle unter den neuen Geschwistern; ohne Angabe ans Ende. Mit demselben Parent ordnet das um.
    position: int | None = None
    #: Der Baum, in dem der Knoten umgehängt wird; nur nötig, wenn er in mehreren steht.
    tree: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class MoveNodeToMap:
    """Hängt den Ast unter die Wurzel der Ziel-Map um (aus seinem Baum weg)."""

    ref: str
    version: int
    #: `uid` der Ziel-Map (auch der Projektbaum, dessen `tree_uid` `list_maps` nennt).
    target: str
    #: Der Baum, aus dem der Ast kommt; nur nötig, wenn der Knoten in mehreren steht.
    tree: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class TransferNodeToMap:
    """Überträgt den Ast: er steht danach auch unter der Wurzel der Ziel-Map."""

    ref: str
    version: int
    target: str
    tree: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class RemoveNodeFromMap:
    """„Hier entfernen“: nimmt den Ast nur aus einem Baum."""

    ref: str
    version: int
    tree: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class DeleteNode:
    """„Knoten löschen“: der Ast verlässt alle Bäume."""

    ref: str
    version: int
    project: str | None = None


@dataclass(frozen=True)
class RestoreAndMoveNode:
    ref: str
    #: Die Version des Knotens im Papierkorb.
    version: int
    #: Neuer Parent in `tree` (uid oder Label); ohne Angabe unter die Wurzel.
    parent: str | None = None
    position: int | None = None
    #: Der Baum, in dem der Knoten an die neue Stelle kommt; nur nötig, wenn er in mehreren steht.
    tree: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class ListNodeTrees:
    ref: str
    project: str | None = None


@dataclass(frozen=True)
class RemovalOut:
    node_uid: str
    #: Die Knoten, die in den Papierkorb gingen (steht der Knoten nirgends mehr, er selbst und seine heimatlosen
    #: Unterknoten).
    nodes_deleted: int
    #: Die Knoten des Asts, die in einem anderen Baum stehen und dort erhalten bleiben.
    kept_elsewhere: int


@dataclass(frozen=True)
class NodeTreeOut:
    tree_uid: str
    #: `project` oder `free`.
    kind: str
    #: Bei freien Maps der Name, beim Projektbaum der Name des Projekts.
    name: str
    #: `uid` des Parent-Knotens in diesem Baum; leer unter der Wurzel.
    parent_uid: str | None


def _removal_out(result: Removal) -> RemovalOut:
    return RemovalOut(result.node.uid, result.nodes_deleted, result.kept_elsewhere)


def _node_tree_out(found: NodeTree) -> NodeTreeOut:
    return NodeTreeOut(found.tree.uid, found.tree.kind, found.name, found.parent_uid)


@dataclass(frozen=True)
class DocumentInfo:
    name: str
    kind: str
    version: int
    updated_at: datetime


@dataclass(frozen=True)
class DocumentOut:
    name: str
    kind: str
    content: str
    version: int
    updated_at: datetime


@dataclass(frozen=True)
class ListNodeDocuments:
    ref: str
    project: str | None = None


@dataclass(frozen=True)
class GetNodeDocument:
    ref: str
    name: str
    project: str | None = None


@dataclass(frozen=True)
class PutNodeDocument:
    ref: str
    name: str
    content: str
    #: Die Version, die ersetzt wird; ohne Angabe wird ein neues Dokument angelegt.
    version: int | None = None
    project: str | None = None


@dataclass(frozen=True)
class AppendNodeEntry:
    ref: str
    topic: str
    discussed: list[str] = field(default_factory=list)
    decided: list[str] = field(default_factory=list)
    open: list[str] = field(default_factory=list)
    project: str | None = None


def _document_info(document: Document) -> DocumentInfo:
    return DocumentInfo(document.name, document.kind, document.revision, document.updated_at)


def _document_out(document: Document) -> DocumentOut:
    return DocumentOut(document.name, document.kind, document.content, document.revision, document.updated_at)


def node_out(view: NodeView) -> NodeOut:
    n, p = view.node, view.placement
    return NodeOut(
        n.uid,
        n.project_uid,
        n.label,
        n.title,
        n.text,
        p.tree_uid,
        p.parent_uid,
        p.position,
        n.revision,
        list(view.documents),
        n.mark,
    )


def _item_ref(item: BacklogItem) -> ItemRefOut:
    return ItemRefOut(item.uid, item.label, item.type, item.title, item.status)


def tree_out(view: TreeView, stats: TreeStats) -> TreeOut:
    nodes: list[TreeNodeOut] = []
    for node, placement in view.nodes:
        base = node_out(NodeView(node, placement, tuple(view.documents.get(node.uid, ()))))
        counted = stats.stats.get(node.uid)
        nodes.append(
            TreeNodeOut(
                **vars(base),
                total=counted.total if counted else 0,
                done=counted.done if counted else 0,
                state=counted.state if counted else "idea",
                tree_count=view.tree_counts.get(node.uid, 1),
            )
        )
    return TreeOut(
        view.project_uid,
        view.tree.uid if view.tree else None,
        nodes,
        [_item_ref(i) for i in stats.unassigned],
        [LinkOut(link.from_node, link.to_node, link.count) for link in stats.links],
    )


def _statuses(value: str | None) -> list[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip()]


@dataclass(frozen=True)
class MemoRefOut:
    uid: str
    label: str
    title: str


@dataclass(frozen=True)
class NodeItemOut(ItemRefOut):
    #: Dem Knoten eigens zugeordnet (nur dann lässt sich die Zuordnung lösen); sonst erbt das Item ihn.
    explicit: bool = False


@dataclass(frozen=True)
class NodeContentOut:
    """Das Detail eines Knotens: die Items, deren wirksamer Knoten er ist (nach Statusfilter, ohne Unterknoten),
    und seine Memos. Memos zählen nicht in der Zahl."""

    node_uid: str
    items: list[NodeItemOut]
    memos: list[MemoRefOut]


@dataclass(frozen=True)
class ItemNodeOut:
    item_uid: str
    #: Der wirksame Knoten; leer, wenn das Item nirgends zugeordnet ist („Nicht zugeordnet“).
    node_uid: str | None
    #: Wahr, wenn das Item eigens an den Knoten gehängt ist; falsch, wenn es ihn von seinem Parent erbt.
    explicit: bool


@dataclass(frozen=True)
class AssignItem:
    #: Knoten (uid oder Label).
    node: str
    #: Item (uid oder Label).
    item: str
    #: Hängt das Item schon an einem anderen Knoten, wird abgewiesen; mit `replace` ersetzt dieser Knoten den alten.
    replace: bool = False
    project: str | None = None


@dataclass(frozen=True)
class UnassignItem:
    item: str
    project: str | None = None


@dataclass(frozen=True)
class LinkMemo:
    node: str
    memo: str
    project: str | None = None


@dataclass(frozen=True)
class UnlinkMemo:
    node: str
    memo: str
    project: str | None = None


@dataclass(frozen=True)
class GetNodeContent:
    ref: str
    statuses: str | None = None
    project: str | None = None
    #: Die Map, in der der Knoten gelesen wird (bestimmt den wirksamen Knoten der Items); ohne Angabe der Projektbaum.
    tree: str | None = None


@dataclass(frozen=True)
class GetItemNode:
    item: str
    project: str | None = None


@dataclass(frozen=True)
class ListMemoNodes:
    memo: str
    project: str | None = None


@dataclass(frozen=True)
class Done:
    ok: bool = True


def _content_out(content: NodeContent) -> NodeContentOut:
    return NodeContentOut(
        content.node.uid,
        [NodeItemOut(**vars(_item_ref(i)), explicit=i.uid in content.explicit) for i in content.items],
        [MemoRefOut(m.uid, m.label, m.title) for m in content.memos],
    )


def _item_node_out(found: ItemNode) -> ItemNodeOut:
    return ItemNodeOut(found.item.uid, found.node.uid if found.node else None, found.explicit)


def _deleted_out(result: MapDeleted) -> MapDeletedOut:
    return MapDeletedOut(result.tree_uid, result.nodes_deleted, result.kept_elsewhere)


def _detail(services: MindmapServices, uid: str, tree: str | None = None) -> NodeOut:
    return node_out(services.mindmap.get_node(uid, None, tree))


OPERATIONS: tuple[Operation, ...] = (
    Operation(
        "list_maps",
        "Die Maps eines Projekts: zuerst der Projektbaum, dann die freien Maps in der Reihenfolge des Anlegens, je "
        "mit Name, Knotenzahl und Versionstoken. Maps im Papierkorb fehlen",
        "read",
        ListMaps,
        list[MapOut],
        lambda s, d: [map_out(view) for view in s.maps.list_maps(d.project)],
        HttpBinding("GET", "/maps/{project}"),
    ),
    Operation(
        "create_map",
        "Legt eine freie Map zum Brainstormen im Projekt an (Übergreifendes gehört ins Projekt „Allgemein“). Der Name "
        "ist je Projekt eindeutig. Knoten legt `create_node` mit `tree` an",
        "write",
        CreateMap,
        MapOut,
        lambda s, d: map_out(s.maps.get_map(s.maps.create_map(d.project, d.name))),
        HttpBinding("POST", "/maps"),
    ),
    Operation(
        "rename_map",
        "Benennt eine freie Map um, mit Versionsprüfung. Der Projektbaum heißt wie das Projekt und lässt sich nicht "
        "umbenennen",
        "write",
        RenameMap,
        MapOut,
        lambda s, d: map_out(s.maps.get_map(s.maps.rename_map(d.tree, d.version, d.name))),
        HttpBinding("PUT", "/maps/{tree}"),
    ),
    Operation(
        "delete_map",
        "Legt eine freie Map in den Papierkorb (Wiederherstellen: `workspace_restore_elements` mit der `tree`-uid). "
        "Knoten, die nur in ihr stehen, gehen mit; Knoten, die auch in einem anderen Baum stehen, bleiben dort. "
        "Items an gelöschten Knoten fallen an den Parent-Knoten zurück, sonst nach „Nicht zugeordnet“. Der "
        "Projektbaum lässt sich nicht löschen. Mit Versionsprüfung",
        "write",
        DeleteMap,
        MapDeletedOut,
        lambda s, d: _deleted_out(s.maps.delete_map(d.tree, d.version)),
        HttpBinding("DELETE", "/maps/{tree}"),
    ),
    Operation(
        "get_tree",
        "Der Themenbaum eines Projekts (das Projekt ist die Wurzel) oder, mit `tree`, einer freien Map: alle Knoten "
        "mit Parent und Stelle, Eltern vor Kindern, je Knoten Anzahl, Fortschritt und Zustand über ihn und seine "
        "Unterknoten, dazu im Projektbaum die Items ohne Knoten (in freien Maps gibt es „Nicht zugeordnet“ nicht). "
        "Knoten im Papierkorb fehlen. `statuses` ist der Statusfilter des Backlogs für die Zahlen",
        "read",
        GetTree,
        TreeOut,
        lambda s, d: tree_out(
            s.mindmap.get_tree(d.project, d.tree), s.assignments.stats(d.project, _statuses(d.statuses), d.tree)
        ),
        HttpBinding("GET", "/trees/{project}"),
    ),
    Operation(
        "get_node",
        "Ein Knoten mit seiner Lage; `ref` ist die uid oder ein Label (mit `project`)",
        "read",
        GetNode,
        NodeOut,
        lambda s, d: node_out(s.mindmap.get_node(d.ref, d.project, d.tree)),
        HttpBinding("GET", "/nodes/{ref}"),
    ),
    Operation(
        "create_node",
        "Legt einen Knoten (Titel, optionaler Text) im Themenbaum des Projekts oder, mit `tree`, in einer freien Map "
        "an, unter `parent` oder unter der Wurzel, an der Stelle `position` (sonst am Ende). Leere Knoten sind erlaubt",
        "write",
        CreateNode,
        NodeOut,
        lambda s, d: _detail(
            s, s.mindmap.create_node(d.project, d.title, d.text, d.parent, d.position, d.tree), d.tree
        ),
        HttpBinding("POST", "/nodes"),
    ),
    Operation(
        "update_node",
        "Ändert Titel, Text oder Markierung eines Knotens mit Versionsprüfung; ein leerer `text` löscht den Text, "
        "`mark` ist `discarded` oder `later`, ein leerer Wert nimmt sie weg",
        "write",
        UpdateNode,
        NodeOut,
        lambda s, d: _detail(s, s.mindmap.update_node(d.ref, d.project, d.version, d.title, d.text, d.mark)),
        HttpBinding("PUT", "/nodes/{ref}"),
    ),
    Operation(
        "move_node",
        "Hängt einen Knoten samt Ast unter einen anderen Parent (ohne `parent`: unter die Wurzel) oder ordnet ihn "
        "unter demselben Parent um. Nicht unter sich selbst oder seine Nachkommen. Mit Versionsprüfung",
        "write",
        MoveNode,
        NodeOut,
        lambda s, d: node_out(
            s.mindmap.get_node(
                s.mindmap.move_node(d.ref, d.project, d.version, d.parent, d.position, d.tree), None, d.tree
            )
        ),
        HttpBinding("POST", "/nodes/{ref}/move"),
    ),
    Operation(
        "move_node_to_map",
        "Hängt einen Ast (Knoten mit Unterknoten) aus seinem Baum in die Ziel-Map um: er steht danach nur dort, unter "
        "der Wurzel am Ende. Nur innerhalb eines Projekts. Abgelehnt mit Liste der Knoten (`mindmap_target_conflict`), "
        "wenn der Ast oder ein Unterknoten im Ziel schon steht; ebenso Knoten im Papierkorb und Maps im Papierkorb. "
        "Mit Versionsprüfung",
        "write",
        MoveNodeToMap,
        NodeOut,
        lambda s, d: node_out(
            s.mindmap.get_node(
                s.branches.move_to_map(d.ref, d.project, d.version, d.tree, d.target).node.uid, None, d.target
            )
        ),
        HttpBinding("POST", "/nodes/{ref}/move-to-map"),
    ),
    Operation(
        "transfer_node_to_map",
        "Überträgt einen Ast in die Ziel-Map: derselbe Ast steht danach in beiden Bäumen (nichts wird kopiert; Titel, "
        "Text, Notizen und Items sind gemeinsam, die Struktur darunter gehört je Baum). Nur zwischen verschiedenen "
        "Bäumen desselben Projekts; Ablehnungen wie bei `move_node_to_map`. Mit Versionsprüfung",
        "write",
        TransferNodeToMap,
        NodeOut,
        lambda s, d: node_out(
            s.mindmap.get_node(
                s.branches.transfer_to_map(d.ref, d.project, d.version, d.tree, d.target).node.uid, None, d.target
            )
        ),
        HttpBinding("POST", "/nodes/{ref}/transfer"),
    ),
    Operation(
        "remove_node_from_map",
        "„Hier entfernen“: nimmt den Ast nur aus einem Baum. Verliert ein Knoten damit seine letzte Platzierung, geht "
        "er mit den heimatlos gewordenen Unterknoten in den Papierkorb; Unterknoten, die in einem anderen Baum stehen, "
        "bleiben dort. Mit Versionsprüfung",
        "write",
        RemoveNodeFromMap,
        RemovalOut,
        lambda s, d: _removal_out(s.branches.remove_from_map(d.ref, d.project, d.version, d.tree)),
        HttpBinding("POST", "/nodes/{ref}/remove"),
    ),
    Operation(
        "delete_node",
        "„Knoten löschen“: nimmt den Ast aus allen Bäumen und legt ihn mit den heimatlos gewordenen Unterknoten in den "
        "Papierkorb (Wiederherstellen: `workspace_restore_elements` oder `restore_and_move_node`). Unterknoten, die in "
        "einem anderen Baum stehen, bleiben dort. Mit Versionsprüfung",
        "write",
        DeleteNode,
        RemovalOut,
        lambda s, d: _removal_out(s.branches.delete_node(d.ref, d.project, d.version)),
        HttpBinding("DELETE", "/nodes/{ref}"),
    ),
    Operation(
        "restore_and_move_node",
        "Holt einen Knoten aus dem Papierkorb und stellt ihn in einem Schritt unter `parent` (sonst unter die Wurzel) "
        "des Baums `tree`. Die neue Stelle ersetzt seine alte Platzierung in diesem Baum; Platzierungen in anderen "
        "Bäumen kommen wie vorher zurück. Mit Versionsprüfung",
        "write",
        RestoreAndMoveNode,
        NodeOut,
        lambda s, d: node_out(
            s.mindmap.get_node(
                s.branches.restore_and_move(d.ref, d.project, d.version, d.tree, d.parent, d.position).uid, None, d.tree
            )
        ),
        HttpBinding("POST", "/nodes/{ref}/restore-move"),
    ),
    Operation(
        "list_node_trees",
        "Die Bäume (ohne Papierkorb), in denen ein Knoten steht: der Projektbaum zuerst, dann die freien Maps",
        "read",
        ListNodeTrees,
        list[NodeTreeOut],
        lambda s, d: [_node_tree_out(t) for t in s.branches.node_trees(d.ref, d.project)],
        HttpBinding("GET", "/nodes/{ref}/trees"),
    ),
    Operation(
        "list_node_documents",
        "Die Dokumente eines Knotens (Name, Art, Version)",
        "read",
        ListNodeDocuments,
        list[DocumentInfo],
        lambda s, d: [_document_info(doc) for doc in s.documents.list_documents(d.ref, d.project)],
        HttpBinding("GET", "/nodes/{ref}/documents"),
    ),
    Operation(
        "get_node_document",
        "Ein Dokument eines Knotens mit Inhalt und Version",
        "read",
        GetNodeDocument,
        DocumentOut,
        lambda s, d: _document_out(s.documents.get_document(d.ref, d.project, d.name)),
        HttpBinding("GET", "/nodes/{ref}/documents/{name}"),
    ),
    Operation(
        "put_node_document",
        "Ersetzt ein Dokument eines Knotens in `version` oder legt ein neues an (<LABEL>_notes.md, "
        "<LABEL>_spec[_<thema>].md)",
        "write",
        PutNodeDocument,
        DocumentOut,
        lambda s, d: _document_out(s.documents.put_document(d.ref, d.project, d.name, d.content, d.version)),
        HttpBinding("PUT", "/nodes/{ref}/documents/{name}"),
    ),
    Operation(
        "append_node_entry",
        "Hängt einen datierten Eintrag (Thema, Discussed, Decided, Open) an die Notizen eines Knotens",
        "write",
        AppendNodeEntry,
        DocumentOut,
        lambda s, d: _document_out(s.documents.append_note(d.ref, d.project, d.topic, d.discussed, d.decided, d.open)),
        HttpBinding("POST", "/nodes/{ref}/entries"),
    ),
    Operation(
        "assign_item",
        "Hängt ein Item (Epic, Story oder Task) an einen Knoten. Seine Kinder erben den Knoten, wenn sie nicht eigens "
        "angehängt sind. Ein Item hängt an höchstens einem Knoten: ein zweiter wird mit mindmap_item_assigned "
        "abgewiesen, außer `replace` ist gesetzt",
        "write",
        AssignItem,
        NodeOut,
        lambda s, d: _detail(s, s.assignments.assign_item(d.item, d.node, d.project, d.replace).uid),
        HttpBinding("POST", "/nodes/{node}/items"),
    ),
    Operation(
        "unassign_item",
        "Löst die eigene Zuordnung eines Items; es erbt danach den Knoten seines Parents oder ist nicht zugeordnet",
        "write",
        UnassignItem,
        Done,
        lambda s, d: (s.assignments.unassign_item(d.item, d.project), Done())[1],
        HttpBinding("DELETE", "/items/{item}/node"),
    ),
    Operation(
        "link_memo",
        "Verlinkt ein Memo mit einem Knoten; ein Memo darf an mehrere Knoten hängen und zählt nicht in der Zahl",
        "write",
        LinkMemo,
        NodeOut,
        lambda s, d: _detail(s, s.assignments.link_memo(d.memo, d.node, d.project).uid),
        HttpBinding("POST", "/nodes/{node}/memos"),
    ),
    Operation(
        "unlink_memo",
        "Löst den Link zwischen einem Memo und einem Knoten",
        "write",
        UnlinkMemo,
        Done,
        lambda s, d: (s.assignments.unlink_memo(d.memo, d.node, d.project), Done())[1],
        HttpBinding("DELETE", "/nodes/{node}/memos/{memo}"),
    ),
    Operation(
        "get_node_content",
        "Das Detail eines Knotens: seine Items (wirksamer Knoten, nach `statuses`) und seine verlinkten Memos",
        "read",
        GetNodeContent,
        NodeContentOut,
        lambda s, d: _content_out(s.assignments.node_content(d.ref, d.project, _statuses(d.statuses), d.tree)),
        HttpBinding("GET", "/nodes/{ref}/content"),
    ),
    Operation(
        "get_item_node",
        "Der wirksame Knoten eines Items und ob es eigens angehängt ist oder erbt",
        "read",
        GetItemNode,
        ItemNodeOut,
        lambda s, d: _item_node_out(s.assignments.item_node(d.item, d.project)),
        HttpBinding("GET", "/items/{item}/node"),
    ),
    Operation(
        "list_memo_nodes",
        "Die Knoten, mit denen ein Memo verlinkt ist (Knoten im Papierkorb fehlen)",
        "read",
        ListMemoNodes,
        list[NodeOut],
        lambda s, d: [_detail(s, n.uid) for n in s.assignments.memo_nodes(d.memo, d.project)],
        HttpBinding("GET", "/memos/{memo}/nodes"),
    ),
)

"""Ein- und Ausgaben und Operationen des Plugins `mindmap` (HTTP + MCP).

Knoten in den Papierkorb legen und wiederherstellen gehen über `workspace` (`workspace_delete_element` mit `cascade`,
`workspace_restore_elements`): ein Ast mit seinen Kindern wandert zusammen in den Papierkorb und kommt zusammen zurück.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from viewer.core.domain.operations import HttpBinding, Operation
from viewer.plugins.mindmap.application.assignments import AssignmentService, ItemNode, NodeContent, TreeStats
from viewer.plugins.mindmap.application.documents import DocumentService
from viewer.plugins.mindmap.application.ports import BacklogItem, Document
from viewer.plugins.mindmap.application.service import MindmapService, NodeView, TreeView


class MindmapServices:
    def __init__(self, mindmap: MindmapService, documents: DocumentService, assignments: AssignmentService) -> None:
        self.mindmap = mindmap
        self.documents = documents
        self.assignments = assignments


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


@dataclass(frozen=True)
class TreeNodeOut(NodeOut):
    """Ein Knoten im Baum mit den Zahlen über sich und seine Unterknoten (jedes Item zählt genau einmal)."""

    #: Anzahl der zählenden Items: nicht im Papierkorb und vom Statusfilter durchgelassen.
    total: int = 0
    #: Davon erledigt (`Completed`): der Fortschritt ist `done` von `total`.
    done: int = 0
    #: `idea`, `planned`, `in_progress` oder `done`; unabhängig vom Statusfilter, `Rejected` zählt nicht.
    state: str = "idea"


@dataclass(frozen=True)
class ItemRefOut:
    uid: str
    label: str
    type: str
    title: str
    status: str


@dataclass(frozen=True)
class TreeOut:
    project_uid: str
    #: Leer, solange im Projekt noch kein Knoten angelegt ist.
    tree_uid: str | None
    #: Die Knoten, Eltern vor Kindern und je Parent nach Stelle; Knoten im Papierkorb fehlen.
    nodes: list[TreeNodeOut]
    #: Die Items ohne Knoten, die der Statusfilter durchlässt (die Seitenansicht „Nicht zugeordnet“).
    unassigned: list[ItemRefOut]


@dataclass(frozen=True)
class GetTree:
    #: `uid` des Projekts.
    project: str
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


@dataclass(frozen=True)
class UpdateNode:
    ref: str
    version: int
    #: Neuer Titel; ohne Angabe bleibt er.
    title: str | None = None
    #: Neuer Text; ohne Angabe bleibt er, ein leerer Text löscht ihn.
    text: str | None = None
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
            )
        )
    return TreeOut(
        view.project_uid, view.tree.uid if view.tree else None, nodes, [_item_ref(i) for i in stats.unassigned]
    )


def _statuses(value: str | None) -> list[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip()]


@dataclass(frozen=True)
class MemoRefOut:
    uid: str
    label: str
    title: str


@dataclass(frozen=True)
class NodeContentOut:
    """Das Detail eines Knotens: die Items, deren wirksamer Knoten er ist (nach Statusfilter, ohne Unterknoten),
    und seine Memos. Memos zählen nicht in der Zahl."""

    node_uid: str
    items: list[ItemRefOut]
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
        [_item_ref(i) for i in content.items],
        [MemoRefOut(m.uid, m.label, m.title) for m in content.memos],
    )


def _item_node_out(found: ItemNode) -> ItemNodeOut:
    return ItemNodeOut(found.item.uid, found.node.uid if found.node else None, found.explicit)


def _detail(services: MindmapServices, uid: str) -> NodeOut:
    return node_out(services.mindmap.get_node(uid, None))


OPERATIONS: tuple[Operation, ...] = (
    Operation(
        "get_tree",
        "Der Themenbaum eines Projekts (das Projekt ist die Wurzel): alle Knoten mit Parent und Stelle, Eltern vor "
        "Kindern, je Knoten Anzahl, Fortschritt und Zustand über ihn und seine Unterknoten, dazu die Items ohne "
        "Knoten. "
        "Knoten im Papierkorb fehlen. `statuses` ist der Statusfilter des Backlogs für die Zahlen",
        "read",
        GetTree,
        TreeOut,
        lambda s, d: tree_out(s.mindmap.get_tree(d.project), s.assignments.stats(d.project, _statuses(d.statuses))),
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
        "Legt einen Knoten (Titel, optionaler Text) im Themenbaum des Projekts an, unter `parent` oder unter der "
        "Wurzel, an der Stelle `position` (sonst am Ende). Leere Knoten sind erlaubt",
        "write",
        CreateNode,
        NodeOut,
        lambda s, d: _detail(s, s.mindmap.create_node(d.project, d.title, d.text, d.parent, d.position)),
        HttpBinding("POST", "/nodes"),
    ),
    Operation(
        "update_node",
        "Ändert Titel oder Text eines Knotens mit Versionsprüfung; ein leerer `text` löscht den Text",
        "write",
        UpdateNode,
        NodeOut,
        lambda s, d: _detail(s, s.mindmap.update_node(d.ref, d.project, d.version, d.title, d.text)),
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
        lambda s, d: _content_out(s.assignments.node_content(d.ref, d.project, _statuses(d.statuses))),
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

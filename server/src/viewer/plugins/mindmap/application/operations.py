"""Ein- und Ausgaben und Operationen des Plugins `mindmap` (HTTP + MCP).

Knoten in den Papierkorb legen und wiederherstellen gehen über `workspace` (`workspace_delete_element` mit `cascade`,
`workspace_restore_elements`): ein Ast mit seinen Kindern wandert zusammen in den Papierkorb und kommt zusammen zurück.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from viewer.core.application.sync import SyncParticipant
from viewer.core.domain.operations import HttpBinding, Operation
from viewer.plugins.mindmap.application.assignments import AssignmentService, ItemNode, NodeContent, TreeStats
from viewer.plugins.mindmap.application.branches import (
    BranchMoved,
    BranchService,
    NodeTree,
    PlacementRestored,
    Removal,
    RemovedFrom,
    TrashedBranch,
)
from viewer.plugins.mindmap.application.creation import Created, NodeCreationService
from viewer.plugins.mindmap.application.documents import DocumentService
from viewer.plugins.mindmap.application.maps import MapDeleted, MapService, MapView
from viewer.plugins.mindmap.application.ports import BacklogItem, Document
from viewer.plugins.mindmap.application.service import MindmapService, NodeView, TreeView
from viewer.plugins.mindmap.application.transfer import BranchTransferService, Preview, TransferResult
from viewer.plugins.mindmap.domain.transfer import Problem, TransferEntry


class MindmapServices:
    def __init__(
        self,
        mindmap: MindmapService,
        documents: DocumentService,
        assignments: AssignmentService,
        maps: MapService,
        branches: BranchService,
        creation: NodeCreationService,
        transfer: BranchTransferService,
        participant: SyncParticipant,
    ) -> None:
        self.mindmap = mindmap
        self.documents = documents
        self.assignments = assignments
        self.maps = maps
        self.branches = branches
        self.creation = creation
        self.transfer = transfer
        self.participant = participant


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
class RestoreNodePlacement:
    """Setzt einen mit „Hier entfernen“ entfernten Ast wieder in den Baum, in dem er stand."""

    ref: str
    version: int
    #: Der Baum, in den der Ast zurück soll; nur nötig, wenn er aus mehreren entfernt wurde.
    tree: str | None = None
    project: str | None = None


@dataclass(frozen=True)
class ListRemovedPlacements:
    ref: str
    project: str | None = None


@dataclass(frozen=True)
class PlacementRestoredOut:
    node_uid: str
    tree_uid: str
    #: Die Knoten, die wieder im Baum stehen (der Knoten und seine Unterknoten aus derselben Entfernung).
    nodes_restored: int
    #: Mitglieder der Entfernung, die im Papierkorb liegen und entfernt gemerkt bleiben.
    nodes_skipped: int
    #: Der Parent, unter dem der Knoten jetzt steht; leer unter der Wurzel.
    parent_uid: str | None
    #: Der alte Parent fehlte (nicht mehr im Baum, im Papierkorb oder selbst noch entfernt): der Ast steht unter der
    #: Wurzel der Map.
    fell_back_to_root: bool


@dataclass(frozen=True)
class RemovedFromOut:
    tree_uid: str
    #: `project` oder `free`.
    kind: str
    #: Bei freien Maps der Name, beim Projektbaum der Name des Projekts.
    name: str
    #: Der Parent von damals; leer unter der Wurzel.
    parent_uid: str | None
    #: Ob der Parent von damals noch im Baum steht; sonst käme der Ast unter die Wurzel.
    parent_available: bool
    #: Die Knoten, die mit ihm zurückkämen.
    nodes: int


@dataclass(frozen=True)
class ListTrashedNodes:
    #: `uid` des Projekts.
    project: str
    #: Die Map, deren Papierkorb gezeigt wird; ohne Angabe der Projektbaum.
    tree: str | None = None


@dataclass(frozen=True)
class TrashedNodeOut:
    uid: str
    label: str
    title: str
    #: Versionstoken des Knotens im Papierkorb, für `restore_and_move_node`.
    version: int
    #: Der Parent, unter dem der Knoten im Baum stand; leer unter der Wurzel.
    parent_uid: str | None
    #: Die Knoten des Asts im Papierkorb (der Knoten und seine gelöschten Unterknoten in diesem Baum).
    nodes: int


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


def _moved(services: MindmapServices, moved: BranchMoved) -> NodeOut:
    return node_out(services.mindmap.get_node(moved.node.uid, None, moved.target.uid))


def _removal_out(result: Removal) -> RemovalOut:
    return RemovalOut(result.node.uid, result.nodes_deleted, result.kept_elsewhere)


def _restored_out(result: PlacementRestored) -> PlacementRestoredOut:
    return PlacementRestoredOut(
        result.node.uid, result.tree.uid, result.nodes, result.skipped, result.parent_uid, result.fell_back
    )


def _trashed_out(found: TrashedBranch) -> TrashedNodeOut:
    node = found.node
    return TrashedNodeOut(node.uid, node.label, node.title, node.revision, found.parent_uid, found.nodes)


def _removed_from_out(found: RemovedFrom) -> RemovedFromOut:
    return RemovedFromOut(
        found.tree.uid, found.tree.kind, found.name, found.parent_uid, found.parent_available, found.nodes
    )


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
    """Das Detail eines Knotens: die Items, deren wirksamer Knoten er ist (nach Statusfilter; Unterknoten nur mit
    `include_subnodes`),
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
    #: Auch die Items der Unterknoten liefern (wie die Zahl am Knoten); ohne: nur die des Knotens selbst.
    include_subnodes: bool = False


@dataclass(frozen=True)
class GetItemNode:
    item: str
    project: str | None = None


@dataclass(frozen=True)
class ListMemoNodes:
    memo: str
    project: str | None = None


@dataclass(frozen=True)
class CreateItemAtNode:
    #: Knoten (uid oder Label).
    node: str
    #: `Epic`, `Story` oder `Task`; die Ebene des Knotens bestimmt ihn nicht.
    type: str
    #: Wie bei `backlog_create_item`: `completion_criteria` sind Pflicht; fehlt `title`, gilt der Titel des Knotens,
    #: fehlt `goal`, sein Text. Dazu `priority`, `required_for_parent`, `summary`, `parent` (uid), `dependencies`.
    fields: dict[str, Any]
    #: Nur nötig, wenn `node` ein Label ist; mit Angabe muss der Knoten zu diesem Projekt gehören.
    project: str | None = None
    #: Die Map, in der der zurückgegebene Knoten gelesen wird; ohne Angabe der Projektbaum.
    tree: str | None = None


@dataclass(frozen=True)
class CreateMemoAtNode:
    node: str
    #: Wie bei `memos_create_memo`; fehlt `summary`, gilt der Titel des Knotens, fehlt `body`, sein Text.
    fields: dict[str, Any]
    project: str | None = None
    tree: str | None = None


@dataclass(frozen=True)
class CreatedElementOut:
    uid: str
    label: str
    #: Bei Items der Titel, bei Memos die Zusammenfassung.
    title: str
    #: Nur bei Items: `Epic`, `Story` oder `Task`.
    type: str | None = None


@dataclass(frozen=True)
class CreatedItemAtNodeOut:
    item: CreatedElementOut
    #: Der Knoten danach, mit Zahlen und Zustand (`idea` → `planned`).
    node: TreeNodeOut


@dataclass(frozen=True)
class CreatedMemoAtNodeOut:
    memo: CreatedElementOut
    #: Der Knoten danach; ein Memo ändert seinen Zustand nicht.
    node: TreeNodeOut


@dataclass(frozen=True)
class TransferEntryIn:
    """Was aus einem Knoten des Astes wird. Ohne Eintrag (oder mit `skip`) wird aus dem Knoten nichts."""

    #: Knoten des Astes (uid oder Label); höchstens einmal im Plan.
    node: str
    #: `item`, `memo` oder `skip`.
    kind: str = "skip"
    #: Bei `item`: `Epic`, `Story` oder `Task`. Er wird nie aus Ebene oder Tiefe abgeleitet.
    type: str | None = None
    #: Bei `item`; fehlt `title`, gilt der Titel des Knotens, fehlt `goal`, sein Text; `completion_criteria` sind
    #: Pflicht.
    title: str | None = None
    goal: str | None = None
    completion_criteria: str | None = None
    summary: str | None = None
    priority: str | None = None
    #: Bei `item` mit Parent: Standard `true`.
    required_for_parent: bool | None = None
    #: Bei `memo`: `summary` und `body` (wie bei `memos_create_memo`; Standard Titel und Text des Knotens).
    memo: dict[str, Any] | None = None
    #: Ein anderer Knoten des Plans (das neue Item wird sein Kind) oder ein vorhandenes Item (uid oder Label).
    parent: str | None = None
    #: Knoten des Plans oder vorhandene Items, von denen das neue Item abhängt.
    depends_on: list[str] | None = None


@dataclass(frozen=True)
class PreviewBranchTransfer:
    #: Der oberste Knoten des Astes (uid oder Label).
    root: str
    entries: list[TransferEntryIn]
    #: Nur nötig, wenn `root` ein Label ist.
    project: str | None = None
    #: Die Map, in der der Ast steht; nötig, wenn der Knoten in mehreren Bäumen steht.
    tree: str | None = None


@dataclass(frozen=True)
class TransferBranch(PreviewBranchTransfer):
    pass


@dataclass(frozen=True)
class ProblemOut:
    code: str
    message: str
    details: dict[str, Any]


@dataclass(frozen=True)
class EntryPreviewOut:
    node: str
    ok: bool
    problems: list[ProblemOut]


@dataclass(frozen=True)
class BranchPreviewOut:
    root: str
    ok: bool
    entries: list[EntryPreviewOut]
    #: Probleme des ganzen Plans (z. B. Kreise).
    problems: list[ProblemOut]
    #: Die Knoten in der Reihenfolge, in der angelegt würde.
    order: list[str]


@dataclass(frozen=True)
class TransferEntryOut:
    node: str
    #: `created`, `failed`, `skipped` oder `not_attempted`.
    status: str
    created: CreatedElementOut | None = None
    #: Bei `failed`: `code`, `message`, `details`.
    error: dict[str, Any] | None = None


@dataclass(frozen=True)
class BranchTransferOut:
    root: str
    #: Alle Knoten des Astes, die Wurzel zuerst.
    entries: list[TransferEntryOut]


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


def _tree_node(services: MindmapServices, uid: str, tree: str | None) -> TreeNodeOut:
    """Der Knoten wie in `get_tree` mit Zahlen und Zustand."""
    view = services.mindmap.get_node(uid, None, tree)
    stats = services.assignments.stats(view.node.project_uid, [], tree).stats.get(uid)
    return TreeNodeOut(
        **vars(node_out(view)),
        total=stats.total if stats else 0,
        done=stats.done if stats else 0,
        state=stats.state if stats else "idea",
    )


def _created_item(services: MindmapServices, created: Created, tree: str | None) -> CreatedItemAtNodeOut:
    e = created.element
    return CreatedItemAtNodeOut(
        CreatedElementOut(e.uid, e.label, e.title, e.type), _tree_node(services, created.node.uid, tree)
    )


def _created_memo(services: MindmapServices, created: Created, tree: str | None) -> CreatedMemoAtNodeOut:
    e = created.element
    return CreatedMemoAtNodeOut(
        CreatedElementOut(e.uid, e.label, e.title), _tree_node(services, created.node.uid, tree)
    )


def _problem_out(problem: Problem) -> ProblemOut:
    return ProblemOut(problem.code, problem.message, problem.details)


def _transfer_entry(entry: TransferEntryIn) -> TransferEntry:
    fields = {
        name: value
        for name in ("title", "goal", "completion_criteria", "summary", "priority", "required_for_parent")
        if (value := getattr(entry, name)) is not None
    }
    return TransferEntry(
        entry.node, entry.kind, entry.type, fields, entry.memo or {}, entry.parent, tuple(entry.depends_on or ())
    )


def _preview_out(preview: Preview) -> BranchPreviewOut:
    return BranchPreviewOut(
        preview.root_uid,
        preview.ok,
        [EntryPreviewOut(e.node, e.ok, [_problem_out(p) for p in e.problems]) for e in preview.entries],
        [_problem_out(p) for p in preview.problems],
        preview.order,
    )


def _transfer_out(result: TransferResult) -> BranchTransferOut:
    return BranchTransferOut(
        result.root_uid,
        [
            TransferEntryOut(
                e.node,
                e.status,
                CreatedElementOut(e.element.uid, e.element.label, e.element.title, e.element.type)
                if e.element
                else None,
                e.error,
            )
            for e in result.entries
        ],
    )


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
        lambda s, d: _moved(s, s.branches.move_to_map(d.ref, d.project, d.version, d.tree, d.target)),
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
        lambda s, d: _moved(s, s.branches.transfer_to_map(d.ref, d.project, d.version, d.tree, d.target)),
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
        "restore_node_placement",
        "Setzt einen mit `remove_node_from_map` („Hier entfernen“) entfernten Ast wieder in den Baum, in dem er stand: "
        "an den alten Parent und die alte Stelle, mit den Unterknoten, die mit ihm entfernt wurden. Fehlt der alte "
        "Parent (nicht mehr im Baum, im Papierkorb oder selbst noch entfernt), steht der Ast unter der Wurzel der Map "
        "(`fell_back_to_root`). Abgelehnt: der Knoten steht im Baum schon wieder (`mindmap_node_in_tree`), es ist "
        "keine "
        "Platzierung gemerkt (`mindmap_nothing_to_restore`), Knoten oder Map im Papierkorb. Mit Versionsprüfung",
        "write",
        RestoreNodePlacement,
        PlacementRestoredOut,
        lambda s, d: _restored_out(s.branches.restore_placement(d.ref, d.project, d.version, d.tree)),
        HttpBinding("POST", "/nodes/{ref}/restore-placement"),
    ),
    Operation(
        "list_trashed_nodes",
        "Die gelöschten Äste einer Map (Seitenansicht „Papierkorb“): je der oberste gelöschte Knoten, der im Baum "
        "stand, mit Titel, Version für `restore_and_move_node`, altem Parent und der Zahl der Knoten im Papierkorb, "
        "die mit ihm zurückkämen. Ohne `tree` der Projektbaum; eine Map im Papierkorb wird abgelehnt",
        "read",
        ListTrashedNodes,
        list[TrashedNodeOut],
        lambda s, d: [_trashed_out(b) for b in s.branches.trashed_branches(d.project, d.tree)],
        HttpBinding("GET", "/trash/{project}"),
    ),
    Operation(
        "list_removed_placements",
        "Die Bäume (ohne Papierkorb), aus denen ein Knoten entfernt wurde und in die er zurück kann („Früher in …“): "
        "der Projektbaum zuerst, dann die freien Maps; mit dem alten Parent, ob er noch im Baum steht, und der "
        "Zahl der "
        "Knoten, die zurückkämen",
        "read",
        ListRemovedPlacements,
        list[RemovedFromOut],
        lambda s, d: [_removed_from_out(t) for t in s.branches.removed_from(d.ref, d.project)],
        HttpBinding("GET", "/nodes/{ref}/removed"),
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
        "create_item_at_node",
        "Legt aus einem Knoten ein Item (Epic, Story oder Task) an und hängt es an den Knoten. Typ und Felder bestimmt "
        "der Aufrufer; fehlt `title`, gilt der Titel des Knotens, fehlt `goal`, sein Text; `completion_criteria` sind "
        "Pflicht. Der Knoten bleibt stehen und wechselt von Idee zu geplant. Scheitert das Anhängen, nennt "
        "mindmap_assign_failed das angelegte Item (`details.created`)",
        "write",
        CreateItemAtNode,
        CreatedItemAtNodeOut,
        lambda s, d: _created_item(s, s.creation.create_item(d.node, d.type, d.fields, d.project), d.tree),
        HttpBinding("POST", "/nodes/{node}/create-item"),
    ),
    Operation(
        "create_memo_at_node",
        "Legt aus einem Knoten ein Memo an und verlinkt es mit dem Knoten; fehlt `summary`, gilt der Titel des "
        "Knotens, fehlt `body`, sein Text. Der Zustand des Knotens ändert sich nicht",
        "write",
        CreateMemoAtNode,
        CreatedMemoAtNodeOut,
        lambda s, d: _created_memo(s, s.creation.create_memo(d.node, d.fields, d.project), d.tree),
        HttpBinding("POST", "/nodes/{node}/create-memo"),
    ),
    Operation(
        "preview_branch_transfer",
        "Prüft den Plan, einen Ast ins Backlog zu überführen, ohne etwas zu schreiben. Je Knoten des Astes legt der "
        "Aufrufer fest: `item` (mit Typ), `memo` oder `skip`; nichts wird aus Ebene oder Tiefe abgeleitet. "
        "`parent` und `depends_on` nennen andere Knoten des Plans oder vorhandene Items. Die Antwort nennt je Eintrag und "
        "für den ganzen Plan die Probleme (`code`, `message`; u. a. node_not_in_branch, node_duplicate, invalid_type, "
        "goal_missing, criteria_missing, parent_type_not_allowed, parent_is_memo, parent_not_found, parent_closed, "
        "dependency_cycle, depends_on_not_found) und die Reihenfolge des Anlegens",
        "read",
        PreviewBranchTransfer,
        BranchPreviewOut,
        lambda s, d: _preview_out(
            s.transfer.preview(d.root, d.project, d.tree, [_transfer_entry(e) for e in d.entries])
        ),
        HttpBinding("POST", "/nodes/{root}/preview-branch-transfer"),
    ),
    Operation(
        "transfer_branch",
        "Überführt einen Ast ins Backlog: prüft den Plan wie `preview_branch_transfer` und legt ihn nur an, wenn die "
        "Vorschau ohne Probleme ist (sonst transfer_blocked, Probleme in `details`). Items und Memos entstehen in der "
        "Reihenfolge ihrer Beziehungen, jedes am Knoten. Je Knoten des Astes meldet die Antwort created, failed, "
        "skipped oder not_attempted (alles, was von einem gescheiterten Eintrag abhängt); Angelegtes bleibt bestehen",
        "write",
        TransferBranch,
        BranchTransferOut,
        lambda s, d: _transfer_out(
            s.transfer.transfer(d.root, d.project, d.tree, [_transfer_entry(e) for e in d.entries])
        ),
        HttpBinding("POST", "/nodes/{root}/transfer-branch"),
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
        "Das Detail eines Knotens: seine Items (wirksamer Knoten, nach `statuses`; mit `include_subnodes` auch die der "
        "Unterknoten) und seine verlinkten Memos",
        "read",
        GetNodeContent,
        NodeContentOut,
        lambda s, d: _content_out(
            s.assignments.node_content(d.ref, d.project, _statuses(d.statuses), d.tree, d.include_subnodes)
        ),
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

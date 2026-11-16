"""Ein- und Ausgaben und Operationen des Plugins `mindmap` (HTTP + MCP).

Knoten in den Papierkorb legen und wiederherstellen gehen über `workspace` (`workspace_delete_element` mit `cascade`,
`workspace_restore_elements`): ein Ast mit seinen Kindern wandert zusammen in den Papierkorb und kommt zusammen zurück.
"""

from __future__ import annotations

from dataclasses import dataclass

from viewer.core.domain.operations import HttpBinding, Operation
from viewer.plugins.mindmap.application.service import MindmapService, NodeView, TreeView


class MindmapServices:
    def __init__(self, mindmap: MindmapService) -> None:
        self.mindmap = mindmap


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


@dataclass(frozen=True)
class TreeOut:
    project_uid: str
    #: Leer, solange im Projekt noch kein Knoten angelegt ist.
    tree_uid: str | None
    #: Die Knoten, Eltern vor Kindern und je Parent nach Stelle; Knoten im Papierkorb fehlen.
    nodes: list[NodeOut]


@dataclass(frozen=True)
class GetTree:
    #: `uid` des Projekts.
    project: str


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


def node_out(view: NodeView) -> NodeOut:
    n, p = view.node, view.placement
    return NodeOut(n.uid, n.project_uid, n.label, n.title, n.text, p.tree_uid, p.parent_uid, p.position, n.revision)


def tree_out(view: TreeView) -> TreeOut:
    nodes = [node_out(NodeView(node, placement)) for node, placement in view.nodes]
    return TreeOut(view.project_uid, view.tree.uid if view.tree else None, nodes)


def _detail(services: MindmapServices, uid: str) -> NodeOut:
    return node_out(services.mindmap.get_node(uid, None))


OPERATIONS: tuple[Operation, ...] = (
    Operation(
        "get_tree",
        "Der Themenbaum eines Projekts (das Projekt ist die Wurzel): alle Knoten mit Parent und Stelle, Eltern vor "
        "Kindern. Knoten im Papierkorb fehlen",
        "read",
        GetTree,
        TreeOut,
        lambda s, d: tree_out(s.mindmap.get_tree(d.project)),
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
)

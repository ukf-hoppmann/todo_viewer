"""Anwendungsfall: aus einem Knoten ein Item oder ein Memo anlegen, das gleich am Knoten hängt (`TASK-073`).

Der Typ des Items und seine Felder bestimmt der Aufrufer; der Knoten liefert nur Standardwerte. Anlegen und Anhängen
sind zwei Transaktionen: scheitert das Anhängen, bleibt das Anlegen bestehen (kein Rückbau) und der Fehler nennt das
angelegte Element, das dann unter „Nicht zugeordnet“ steht (Item) bzw. ohne Link bleibt (Memo).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from viewer.core.domain.errors import DomainError
from viewer.plugins.mindmap.application.ports import (
    BacklogWriter,
    CreatedElement,
    MemoWriter,
    NodeAssigner,
    NodeSource,
)
from viewer.plugins.mindmap.domain.creation import item_fields, memo_fields
from viewer.plugins.mindmap.domain.model import MindmapViolation, Node


@dataclass(frozen=True)
class Created:
    """Das angelegte Element und der Knoten, an dem es jetzt hängt."""

    element: CreatedElement
    node: Node


class NodeCreationService:
    def __init__(self, nodes: NodeSource, assigner: NodeAssigner, items: BacklogWriter, memos: MemoWriter) -> None:
        self._nodes = nodes
        self._assigner = assigner
        self._items = items
        self._memos = memos

    def create_item(self, node_ref: str, type_: str, fields: Mapping[str, Any], project_uid: str | None) -> Created:
        node = self._nodes.node_for_creation(node_ref, project_uid)
        prepared = item_fields(node, fields)
        element = self._items.create_item(node.project_uid, type_, prepared)
        attached = self._attach(
            element, lambda: self._assigner.assign_item(element.uid, node.uid, node.project_uid, False)
        )
        return Created(element, attached)

    def create_memo(self, node_ref: str, fields: Mapping[str, Any], project_uid: str | None) -> Created:
        node = self._nodes.node_for_creation(node_ref, project_uid)
        element = self._memos.create_memo(node.project_uid, memo_fields(node, fields))
        attached = self._attach(element, lambda: self._assigner.link_memo(element.uid, node.uid, node.project_uid))
        return Created(element, attached)

    @staticmethod
    def _attach(element: CreatedElement, attach: Any) -> Node:
        try:
            node: Node = attach()
        except DomainError as failure:
            raise MindmapViolation(
                "mindmap_assign_failed",
                f"{element.label} wurde angelegt, hängt aber an keinem Knoten: {failure}",
                created={"uid": element.uid, "label": element.label},
                cause=failure.code,
            ) from failure
        return node

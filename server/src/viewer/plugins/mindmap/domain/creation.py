"""Felder für ein Item oder Memo, das aus einem Knoten entsteht: Titel und Text des Knotens sind die Standardwerte."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from viewer.core.domain.errors import InvalidInput
from viewer.plugins.mindmap.domain.model import Node


def _given(fields: Mapping[str, Any], name: str) -> bool:
    value = fields.get(name)
    return value is not None and not (isinstance(value, str) and not value.strip())


def item_fields(node: Node, fields: Mapping[str, Any]) -> dict[str, Any]:
    """Die Felder des neuen Items: fehlt `title`, gilt der Titel des Knotens, fehlt `goal`, sein Text (falls er einen
    hat). Die Abschlusskriterien kommen immer vom Aufrufer, der Knoten hat keine; alles Weitere prüft das Backlog."""
    result = {k: v for k, v in fields.items() if k not in ("title", "goal") or _given(fields, k)}
    if not _given(fields, "completion_criteria"):
        raise InvalidInput(
            "completion_criteria fehlt: der Knoten hat keine Abschlusskriterien",
            details={"field": "completion_criteria"},
        )
    result.setdefault("title", node.title)
    if "goal" not in result and node.text:
        result["goal"] = node.text
    return result


def memo_fields(node: Node, fields: Mapping[str, Any]) -> dict[str, Any]:
    """Die Felder des neuen Memos: fehlt `summary`, gilt der Titel des Knotens, fehlt `body`, sein Text."""
    result = {k: v for k, v in fields.items() if k not in ("summary", "body") or _given(fields, k)}
    result.setdefault("summary", node.title)
    if "body" not in result and node.text:
        result["body"] = node.text
    return result

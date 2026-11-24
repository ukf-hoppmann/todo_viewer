"""Die Beschreibungen der MCP-Tools nennen der KI die Regel zum Zuordnen und Vorschlagen (`TASK-077`)."""

from __future__ import annotations

import pytest
from viewer.core.domain.operations import Operation
from viewer.plugins.backlog.application.operations import OPERATIONS as BACKLOG_OPERATIONS
from viewer.plugins.mindmap.application.guidance import ASSIGNMENT_RULE
from viewer.plugins.mindmap.application.operations import OPERATIONS as MINDMAP_OPERATIONS

RULE_OPERATIONS = ("get_tree", "create_node", "assign_item", "create_item_at_node")


def _operation(operations: tuple[Operation, ...], name: str) -> Operation:
    return next(op for op in operations if op.name == name)


def test_rule_states_the_key_points() -> None:
    # Baum lesen, Knoten wählen oder vorschlagen, nur nach Zustimmung anlegen, sonst „Nicht zugeordnet“.
    for phrase in (
        "mindmap_get_tree",
        "mindmap_create_item_at_node",
        "mindmap_assign_item",
        "schlage",
        "Zustimmung",
        "mindmap_create_node",
        "Nicht zugeordnet",
        "backlog_create_item",
    ):
        assert phrase in ASSIGNMENT_RULE


@pytest.mark.parametrize("name", RULE_OPERATIONS)
def test_mindmap_tools_carry_the_same_rule(name: str) -> None:
    assert ASSIGNMENT_RULE in _operation(MINDMAP_OPERATIONS, name).summary


def test_backlog_create_item_points_to_the_tree_without_naming_the_plugin_code() -> None:
    summary = _operation(BACKLOG_OPERATIONS, "create_item").summary
    assert "Themenbaum" in summary
    assert "mindmap_create_item_at_node" in summary
    assert "Pflicht: title, goal, completion_criteria" in summary

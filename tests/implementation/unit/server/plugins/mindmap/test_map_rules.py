"""Regeln für Maps: Name einer freien Map und Art des Baums (`TASK-062`)."""

from __future__ import annotations

import pytest

from viewer.plugins.mindmap.domain import tree as rules
from viewer.plugins.mindmap.domain.model import TREE_FREE, TREE_KINDS, TREE_PROJECT, MindmapViolation, Tree


def test_there_are_project_and_free_trees() -> None:
    assert TREE_KINDS == (TREE_PROJECT, TREE_FREE)


def test_a_new_tree_has_no_name_and_is_alive() -> None:
    tree = Tree("t", "p")
    assert (tree.kind, tree.name, tree.revision, tree.deleted_at) == (TREE_PROJECT, None, 1, None)


def test_the_name_is_one_trimmed_line() -> None:
    assert rules.clean_map_name("  Ideen   für \n Q3 ") == "Ideen für Q3"


@pytest.mark.parametrize("value", [None, "", "   ", 5])
def test_the_name_is_required(value: object) -> None:
    with pytest.raises(MindmapViolation) as error:
        rules.clean_map_name(value)
    assert error.value.code == "mindmap_map_name_missing"


def test_the_name_has_a_length_limit() -> None:
    with pytest.raises(MindmapViolation) as error:
        rules.clean_map_name("x" * 101)
    assert error.value.code == "mindmap_map_name_too_long"


def test_a_name_is_taken_regardless_of_case() -> None:
    with pytest.raises(MindmapViolation) as error:
        rules.check_map_name_free("ideen", ["Ideen", "Roadmap"])
    assert error.value.code == "mindmap_map_name_taken"
    rules.check_map_name_free("Neu", ["Ideen"])


def test_only_free_maps_can_be_deleted() -> None:
    rules.check_deletable(Tree("t", "p", TREE_FREE, "Ideen"))
    with pytest.raises(MindmapViolation) as error:
        rules.check_deletable(Tree("t", "p", TREE_PROJECT))
    assert error.value.code == "mindmap_project_tree_fixed"
    with pytest.raises(MindmapViolation) as error:
        rules.check_renamable(Tree("t", "p", TREE_PROJECT))
    assert error.value.code == "mindmap_project_tree_fixed"

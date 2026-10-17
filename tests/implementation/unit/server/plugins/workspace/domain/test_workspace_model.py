import pytest
from viewer.core.domain.errors import InvalidInput
from viewer.plugins.workspace.domain.model import (
    format_label,
    parse_label,
    reorder,
    validate_mirror,
    validate_project_name,
    validate_sync_direction,
)


def test_labels_have_three_digits_at_least_and_parse_back() -> None:
    assert format_label("STORY", 12) == "STORY-012"
    assert format_label("TASK", 1234) == "TASK-1234"
    assert parse_label("STORY-012") == ("STORY", 12)
    assert parse_label(" NOTE-003 ") == ("NOTE", 3)
    assert parse_label("story-1") is None and parse_label("NEW-x") is None and parse_label("Misc:NOTE-003") is None


@pytest.mark.parametrize("name", ["", "   ", "x" * 101, "mit\nUmbruch"])
def test_invalid_project_names(name: str) -> None:
    with pytest.raises(InvalidInput):
        validate_project_name(name)


def test_project_name_is_trimmed() -> None:
    assert validate_project_name("  Mein Projekt ") == "Mein Projekt"


def test_mirror_folder_must_be_absolute_and_required_when_enabled() -> None:
    assert validate_mirror("/home/x/todo", True) == "/home/x/todo"
    assert validate_mirror("C:\\Projekte\\todo", False) == "C:\\Projekte\\todo"
    assert validate_mirror(None, False) is None
    assert validate_mirror("  ", False) is None
    for bad in (("relativ/pfad", False), (None, True), ("", True)):
        with pytest.raises(InvalidInput):
            validate_mirror(*bad)


def test_sync_direction_is_one_of_three() -> None:
    assert validate_sync_direction("to_files") == "to_files"
    with pytest.raises(InvalidInput):
        validate_sync_direction("sideways")


@pytest.mark.parametrize(
    ("position", "expected"),
    [
        (0, ["c", "a", "b", "d"]),
        (1, ["a", "c", "b", "d"]),
        (3, ["a", "b", "d", "c"]),
        (99, ["a", "b", "d", "c"]),
        (-5, ["c", "a", "b", "d"]),
    ],
)
def test_reorder_moves_an_entry_to_a_position(position: int, expected: list[str]) -> None:
    assert reorder(["a", "b", "c", "d"], "c", position) == expected

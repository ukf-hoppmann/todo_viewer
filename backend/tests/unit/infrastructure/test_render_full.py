"""The full renderer writes every field of an item so that reading it back gives the same item."""
from __future__ import annotations

from pathlib import Path

from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.markdown import build_markdown_repository
from todo_viewer.infrastructure.markdown.editors import EntryRenderer
from todo_viewer.infrastructure.markdown.field_mapper import BacklogFieldMapper, PriorityNormalizer
from todo_viewer.infrastructure.markdown.parsers import BacklogParser

FIXTURE = Path(__file__).parents[2] / "fixtures" / "backlog"


def _render(items: list[Item]) -> list[str]:
    lines = ["# Backlog", "", "## Work items", ""]
    for item in items:
        lines += [*EntryRenderer().render_full(item), ""]
    return lines


def _parse(lines: list[str], location: Location = Location.ACTIVE) -> list[Item]:
    return BacklogParser(BacklogFieldMapper(PriorityNormalizer())).parse(lines, "P", location)


def _fixture_items() -> list[Item]:
    return build_markdown_repository(Path("/")).load(Source(project="P", path=str(FIXTURE))).items


def test_fixture_items_survive_rendering_and_reading():
    for location in Location:
        items = [i for i in _fixture_items() if i.location is location]
        assert items

        back = _parse(_render(items), location)

        assert [(i.id, i.version) for i in back] == [(i.id, i.version) for i in items]


def test_rendering_twice_gives_identical_text():
    items = _fixture_items()

    once = _render(items)
    twice = _render(_parse(once))

    assert twice == once


def test_every_field_is_written():
    item = Item(
        id="STORY-007", title="Everything", project="P", item_type="Story", status="Completed", parent="EPIC-001",
        required_for_parent=False, dependencies=["TASK-001", "TASK-002"], created="2026-05-01", area="Core",
        priority="Urgent", goal="Goal text.", completion_criteria="Criteria", summary="Sum",
        resolution="Done by owner.",
        notes=["STORY-007_notes.md"], spec=["STORY-007_spec.md", "STORY-007_spec_ui.md"],
        extra_fields={"Verification": "Unit tests", "Empty": ""}, deleted="2026-06-01")

    [back] = _parse(_render([item]))

    assert back == item


def test_optional_fields_stay_unset():
    item = Item(id="EPIC-001", title="Bare", project="P", item_type="Epic")

    [back] = _parse(_render([item]))

    assert back == item
    assert not any("Parent" in line for line in EntryRenderer().render_full(item))


def test_render_full_does_not_change_the_existing_renderer():
    item = Item(id="TASK-001", title="t", project="P", resolution="r", notes=["TASK-001_notes.md"])

    assert not any("Resolution" in line or "Notes" in line for line in EntryRenderer().render(item))

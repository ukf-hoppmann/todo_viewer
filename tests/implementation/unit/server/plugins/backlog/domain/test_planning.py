"""Neue Items vor dem Anlegen prüfen, ohne zu schreiben (`TASK-074`): dieselben Regeln wie beim Anlegen."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Any

from backlog_fixtures import item

from viewer.plugins.backlog.domain.planning import PlannedItem, PlanProblem, check_planned

TODAY = date(2026, 11, 24)
FIELDS = {"title": "Titel", "goal": "Ziel", "completion_criteria": "1. Fertig"}


def planned(
    key: str, type_: str = "Task", parent_key: str | None = None, depends: tuple[str, ...] = (), **fields: Any
) -> PlannedItem:
    return PlannedItem(key, type_, {**FIELDS, "title": key, **fields}, parent_key, depends)


def codes(problems: list[PlanProblem], key: str | None) -> list[str]:
    return [p.code for p in problems if p.key == key]


def test_a_valid_plan_has_no_problems() -> None:
    plan = [
        planned("e", "Epic"),
        planned("s", "Story", "e", required_for_parent=True),
        planned("t", "Task", "s", ("e",), required_for_parent=True),
    ]
    assert check_planned([], "p", plan, TODAY) == []


def test_missing_fields_and_unknown_types_are_named_per_entry() -> None:
    plan = [
        PlannedItem("a", "Task", {"title": "A", "completion_criteria": "1. x"}),
        PlannedItem("b", "Task", {"title": "B", "goal": "Z"}),
        PlannedItem("c", "Thema", dict(FIELDS)),
    ]
    problems = check_planned([], "p", plan, TODAY)
    assert codes(problems, "a") == ["value_required"] and problems[0].details["field"] == "goal"
    assert codes(problems, "b") == ["value_required"] and problems[1].details["field"] == "completion_criteria"
    assert codes(problems, "c") == ["invalid_input"] and problems[2].details["field"] == "type"


def test_an_epic_below_a_task_and_a_parent_without_required_flag_are_reported() -> None:
    plan = [planned("t", "Task"), planned("e", "Epic", "t"), planned("s", "Story", "t")]
    problems = check_planned([], "p", plan, TODAY)
    assert "epic_with_parent" in codes(problems, "e")
    assert "required_for_parent_missing" in codes(problems, "s")
    assert codes(problems, "t") == []


def test_every_problem_of_every_entry_is_reported_not_only_the_first() -> None:
    plan = [planned("a", "Epic", "x"), planned("b", "Epic", "x"), planned("x")]
    problems = check_planned([], "p", plan, TODAY)
    assert "epic_with_parent" in codes(problems, "a") and "epic_with_parent" in codes(problems, "b")


def test_cycles_name_all_entries_involved() -> None:
    plan = [planned("a", depends=("b",)), planned("b", depends=("a",)), planned("c")]
    problems = check_planned([], "p", plan, TODAY)
    assert "dependency_cycle" in codes(problems, "a") and "dependency_cycle" in codes(problems, "b")
    assert codes(problems, "c") == []
    assert any(p.key is None and p.code == "dependency_cycle" for p in problems)


def test_a_closed_existing_parent_is_reported_at_the_child() -> None:
    parent = replace(item("old", status="Completed"), type="Story")
    plan = [PlannedItem("t", "Task", {**FIELDS, "parent": "old", "required_for_parent": True})]
    problems = check_planned([parent], "p", plan, TODAY)
    assert "parent_closed" in codes(problems, "t")


def test_an_entry_that_cannot_be_built_does_not_cause_follow_up_problems_at_its_children() -> None:
    plan = [PlannedItem("a", "Epic", {"title": "A"}), planned("b", "Story", "a", required_for_parent=True)]
    problems = check_planned([], "p", plan, TODAY)
    assert codes(problems, "a") == ["value_required"]
    assert codes(problems, "b") == []

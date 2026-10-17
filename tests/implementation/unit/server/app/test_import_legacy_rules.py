from __future__ import annotations

import re
from pathlib import Path

import pytest
from viewer.app.import_legacy import legacy_schema
from viewer.app.import_legacy.mapping import (
    counters,
    document_kind,
    extra_fields_lines,
    map_priority,
    split_label,
    stable_uid,
)
from viewer.app.import_legacy.report import Report

OLD_SCHEMA = Path(__file__).resolve().parents[5] / "src_old/backend/todo_viewer/infrastructure/database/schema.py"


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("Urgent", "Urgent"),
        ("Important", "Important"),
        ("Normal", "Normal"),
        ("Prospective", "Prospective"),
        ("High", "Urgent"),
        ("Medium", "Important"),
        ("Low", "Normal"),
        ("dringend", "Urgent"),
        ("Wichtig", "Important"),
        ("PERSPEKTIVISCH", "Prospective"),
        (None, "Normal"),
        ("  ", "Normal"),
    ],
)
def test_priorities_are_mapped(old: str | None, new: str) -> None:
    assert map_priority(old) == new


def test_any_other_priority_is_unknown() -> None:
    assert map_priority("Kritisch") is None


def test_labels_split_into_prefix_and_number_and_counters_take_the_highest() -> None:
    assert split_label("STORY-012") == ("STORY", 12)
    assert split_label("story-1") is None and split_label("STORY") is None
    assert counters(["STORY-001", "STORY-012", "TASK-003", "kaputt"]) == {"STORY": 12, "TASK": 3}


def test_generated_uids_are_stable_and_distinct() -> None:
    assert stable_uid("alarm", 1) == stable_uid("alarm", 1)
    assert stable_uid("alarm", 1) != stable_uid("alarm", 2) != stable_uid("link", 2)


def test_extra_fields_are_one_line_each() -> None:
    assert extra_fields_lines([("Context", "Kontext"), ("Implementation", "Eins\nZwei"), ("Leer", "")]) == [
        "Context: Kontext",
        "Implementation: Eins\n  Zwei",
        "Leer:",
    ]


def test_document_kind_follows_the_list_and_otherwise_the_name() -> None:
    assert document_kind("TASK-001", "x.md", "spec") == "spec"
    assert document_kind("TASK-001", "TASK-001_notes.md", None) == "notes"
    assert document_kind("TASK-001", "TASK-001_spec_ui.md", None) == "spec"


def test_the_report_lists_counts_sorted_and_deviations() -> None:
    report = Report()
    report.count("Notes", 2)
    report.count("Items")
    report.deviation("etwas fehlt")

    text = report.render(dry_run=True)

    assert text.splitlines() == [
        "Übernahme aus dem alten Viewer (Probelauf, nichts geschrieben)",
        "",
        "  Items  1",
        "  Notes  2",
        "",
        "Abweichungen: 1",
        "  - etwas fehlt",
    ]


def _columns(source: str) -> dict[str, set[str]]:
    """Tabelle → Spaltennamen, aus dem Quelltext einer Schema-Datei gelesen (nicht importiert)."""
    tables: dict[str, set[str]] = {}
    for match in re.finditer(r'sa\.Table\(\s*"(\w+)", metadata,(.*?)\n\)', source, re.S):
        tables[match.group(1)] = set(re.findall(r'sa\.Column\("(\w+)"', match.group(2)))
    return tables


def test_the_copy_of_the_legacy_schema_matches_the_old_viewer() -> None:
    old = _columns(OLD_SCHEMA.read_text(encoding="utf-8"))
    copy = {name: {c.name for c in table.columns} for name, table in legacy_schema.metadata.tables.items()}

    assert set(copy) <= set(old)
    for name, columns in copy.items():
        assert columns <= old[name], name

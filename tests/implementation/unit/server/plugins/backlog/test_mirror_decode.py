from __future__ import annotations

import json
from dataclasses import replace

import pytest
from mirror_files import BACKLOG_FIXTURES, FIXTURES, read_folder
from viewer.core.domain.sync import MirrorFormatError
from viewer.plugins.backlog.infrastructure.mirror.decode import decode

CODES = [
    "duplicate_label",
    "duplicate_uid",
    "format_version",
    "invalid_placeholder",
    "invalid_value",
    "missing_field",
    "rule_violation",
    "unknown_field",
]


def _decode(name: str):  # type: ignore[no-untyped-def]
    return decode(read_folder(BACKLOG_FIXTURES / name))


def test_the_valid_project_is_read_with_all_items_and_documents() -> None:
    entries = _decode("valid")

    items = {e.label or e.placeholder: e for e in entries if e.kind != "backlog.document"}
    assert list(items) == [
        "EPIC-001",
        "STORY-001",
        "TASK-001",
        "STORY-002",
        "TASK-002",
        "NEW-login-dialog",
        "STORY-003",
        "TASK-003",
    ]
    assert {k: e.kind for k, e in items.items()}["STORY-003"] == "story"


def test_fields_and_references_of_an_item() -> None:
    items = {e.label: e for e in _decode("valid") if e.label and e.kind != "backlog.document"}
    task = items["TASK-001"]

    assert task.uid == "0b6f2c1e-4d3a-4e8b-9c7d-1a2b3c4d5e03"
    assert task.refs == {"parent": ("STORY-001",), "dependencies": ("STORY-002",)}
    assert dict(task.fields) == {
        "title": "Task mit Abhängigkeit",
        "status": "Awaiting confirmation",
        "priority": "Normal",
        "created": "2026-10-03",
        "goal": "Ein Task, der von einer anderen Story abhängt.",
        "completion_criteria": "Die Abhängigkeit ist erfüllt.",
        "summary": None,
        "resolution": None,
        "required_for_parent": True,
        "deleted": None,
    }
    assert items["EPIC-001"].refs == {}
    assert items["STORY-002"].fields["required_for_parent"] is False
    assert items["STORY-003"].fields["resolution"] == "Vom Projektinhaber am 2026-10-01 bestätigt."
    assert items["TASK-003"].fields["deleted"] == "2026-10-10"


def test_a_wrapped_goal_is_read_as_one_text() -> None:
    items = {e.label: e for e in _decode("valid") if e.label and e.kind != "backlog.document"}

    assert items["EPIC-001"].fields["goal"] == (
        "Ein Epic mit einer Pflicht-Story, einer optionalen Story und einer abgeschlossenen Story im Archiv."
    )


def test_a_new_item_has_a_placeholder_and_no_uid_label_or_created() -> None:
    new = next(e for e in _decode("valid") if e.placeholder == "NEW-login-dialog")

    assert (new.uid, new.label, new.fields["created"]) == (None, None, None)
    assert new.refs == {"parent": ("STORY-001",), "dependencies": ("TASK-001",)}
    assert new.source == ("TODO.md", 72)


def test_an_existing_item_may_name_a_placeholder() -> None:
    items = {e.label: e for e in _decode("valid") if e.label and e.kind != "backlog.document"}

    assert items["TASK-002"].refs == {"dependencies": ("NEW-login-dialog",)}


def test_documents_are_entries_with_the_uid_of_the_item_and_the_name() -> None:
    docs = {e.label or e.placeholder: e for e in _decode("valid") if e.kind == "backlog.document"}
    assert docs["STORY-001_spec.md"].uid == "0b6f2c1e-4d3a-4e8b-9c7d-1a2b3c4d5e02/spec"

    assert set(docs) == {"STORY-001_notes.md", "STORY-001_spec.md", "NEW-login-dialog/notes"}
    notes = docs["STORY-001_notes.md"]
    assert notes.uid == "0b6f2c1e-4d3a-4e8b-9c7d-1a2b3c4d5e02/notes"
    assert notes.refs == {"item": ("STORY-001",)} and notes.fields["kind"] == "notes"
    # Die Titelzeile ist kein Inhalt: das Schreiben erzeugt sie aus Label und Titel.
    assert notes.fields["title"] == "Pflicht-Story mit Dokumenten"
    assert notes.fields["content"].startswith("\n## 2026-10-02 — Erster Eintrag\n")
    assert docs["STORY-001_spec.md"].fields["kind"] == "spec"
    new = docs["NEW-login-dialog/notes"]
    assert (new.uid, new.label, new.refs) == (None, None, {"item": ("NEW-login-dialog",)})


@pytest.mark.parametrize("code", CODES)
def test_every_error_names_code_file_and_line_of_the_golden_example(code: str) -> None:
    expected = json.loads((BACKLOG_FIXTURES / "invalid" / code / "expected.json").read_text(encoding="utf-8"))

    with pytest.raises(MirrorFormatError) as error:
        decode(read_folder(BACKLOG_FIXTURES / "invalid" / code))

    assert (error.value.code, error.value.details["file"], error.value.details["line"]) == (
        expected["code"],
        expected["file"],
        expected["line"],
    )


def test_a_missing_file_is_no_entry_and_an_empty_folder_gives_none() -> None:
    from viewer.core.domain.files import FileSet

    assert decode(FileSet({})) == []


def test_a_document_in_the_wrong_folder_is_a_file_label_mismatch() -> None:
    files = read_folder(BACKLOG_FIXTURES / "valid")
    moved = {
        ("items/STORY-001/STORY-009_notes.md" if p == "items/STORY-001/STORY-001_notes.md" else p): e
        for p, e in files.files.items()
    }

    with pytest.raises(MirrorFormatError) as error:
        decode(type(files)(moved))

    assert (error.value.code, error.value.details["file"], error.value.details["line"]) == (
        "file_label_mismatch",
        "items/STORY-001/STORY-009_notes.md",
        1,
    )


def test_a_document_of_an_item_that_is_not_in_the_files_is_left_alone() -> None:
    files = read_folder(BACKLOG_FIXTURES / "valid")
    extra = dict(files.files)
    extra["items/STORY-099/STORY-099_notes.md"] = files.files["items/STORY-001/STORY-001_notes.md"]

    entries = decode(type(files)(extra))

    assert not any(e.label == "STORY-099_notes.md" for e in entries)


def test_an_active_item_below_a_closed_parent_is_reported_at_its_parent_line() -> None:
    # Die Zeile steht im Golden-File; hier zusätzlich die Meldung.
    with pytest.raises(MirrorFormatError) as error:
        decode(read_folder(BACKLOG_FIXTURES / "invalid" / "rule_violation"))

    assert "STORY-003" in str(error.value)


def test_a_type_that_does_not_match_the_label_is_invalid() -> None:
    files = read_folder(BACKLOG_FIXTURES / "valid")
    changed = {
        p: (
            type(e)(
                e.path,
                e.text.replace(
                    "- Type: Task.\n  - Parent: `STORY-001`.\n  - Required for parent: Yes.\n  - Status: Awaiting",
                    "- Type: Story.\n  - Parent: `STORY-001`.\n  - Required for parent: Yes.\n  - Status: Awaiting",
                ),
                e.version,
            )
            if p == "TODO.md"
            else e
        )
        for p, e in files.files.items()
    }

    with pytest.raises(MirrorFormatError) as error:
        decode(type(files)(changed))

    assert error.value.code == "invalid_value" and "TASK-001" in str(error.value)


def test_notes_are_compared_in_the_layout_the_database_produces() -> None:
    """Zusätzliche Leerzeilen nach dem Stempel sind kein Unterschied: die Datenbank bringt Notes ins feste Layout."""
    from dataclasses import replace

    files = read_folder(BACKLOG_FIXTURES / "valid")
    path = "items/STORY-001/STORY-001_notes.md"
    text = (
        "# STORY-001 — Pflicht-Story mit Dokumenten\n\n## State\n\n- Goal/Status: a\n\n"
        "State confirmed after entry 2026-10-02 — Erster Eintrag (d48625b9122c)\n\n\n"
        "## 2026-10-02 — Erster Eintrag\ntext\n"
    )
    plain = replace(files.files[path], text=text.replace("\n\n\n##", "\n\n##"))
    extra = replace(files.files[path], text=text)

    def content_of(entry) -> str:  # type: ignore[no-untyped-def]
        folder = type(files)({**files.files, path: entry})
        return next(e for e in decode(folder) if e.label == "STORY-001_notes.md").fields["content"]

    assert content_of(extra) == content_of(plain)


def _with_text(files, path: str, old: str, new: str):  # type: ignore[no-untyped-def]
    changed = replace(files.files[path], text=files.files[path].text.replace(old, new))
    return type(files)({**files.files, path: changed})


def test_version_2_with_area_is_read_like_version_3_and_area_is_ignored() -> None:
    v2 = decode(read_folder(FIXTURES / "valid"))
    v3 = _decode("valid")

    assert [(e.kind, e.uid, e.label, e.placeholder, dict(e.fields), e.refs) for e in v2] == [
        (e.kind, e.uid, e.label, e.placeholder, dict(e.fields), e.refs) for e in v3
    ]
    assert all("area" not in e.fields for e in v2)


def test_a_version_3_file_may_still_carry_area_which_is_ignored() -> None:
    files = read_folder(BACKLOG_FIXTURES / "valid")
    with_area = _with_text(files, "TODO.md", "  - Status: In progress.\n", "  - Status: In progress.\n  - Area: Alt.\n")
    assert with_area.files["TODO.md"].text != files.files["TODO.md"].text

    assert [dict(e.fields) for e in decode(with_area)] == [dict(e.fields) for e in decode(files)]


def test_area_is_not_required_in_either_version() -> None:
    files = read_folder(BACKLOG_FIXTURES / "valid")
    v2 = _with_text(files, "TODO.md", "backlog format version 3", "backlog format version 2")

    assert decode(v2) and "Area" not in v2.files["TODO.md"].text


def test_version_4_and_a_missing_version_are_rejected_with_the_format_version_code() -> None:
    files = read_folder(BACKLOG_FIXTURES / "valid")
    for text, version in (("backlog format version 4", 4), ("backlog format", None)):
        broken = _with_text(files, "TODO.md", "backlog format version 3", text)
        with pytest.raises(MirrorFormatError) as error:
            decode(broken)
        assert error.value.code == "format_version", version
        assert error.value.details["file"] == "TODO.md"

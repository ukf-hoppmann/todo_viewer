from __future__ import annotations

import difflib
from dataclasses import replace
from typing import Any

from mirror_files import BACKLOG_FIXTURES, FIXTURES, read_folder
from viewer.core.domain.files import Change, DeleteFile, FileEntry, FileSet, RenameFile, WriteFile
from viewer.core.domain.sync import MirrorEntry
from viewer.plugins.backlog.infrastructure.mirror.decode import decode
from viewer.plugins.backlog.infrastructure.mirror.encode import encode
from viewer.plugins.backlog.infrastructure.mirror.syntax import field_lines

CURRENT = read_folder(BACKLOG_FIXTURES / "valid")
ENTRIES = decode(CURRENT)
BY_LABEL = {e.label: e for e in ENTRIES if e.label}


def changed(entry: MirrorEntry, **fields: Any) -> MirrorEntry:
    return replace(entry, fields={**entry.fields, **fields})


def texts(changes: list[Change]) -> dict[str, str]:
    return {c.path: c.text for c in changes if isinstance(c, WriteFile)}


def diff(path: str, text: str) -> list[str]:
    old = CURRENT.files[path].text.splitlines()
    return [
        line
        for line in difflib.unified_diff(old, text.splitlines(), lineterm="", n=0)
        if line[:1] in "+-" and line[:3] not in ("+++", "---")
    ]


def test_writing_what_was_read_changes_nothing() -> None:
    known = [e for e in ENTRIES if e.uid is not None]

    assert encode(known, [], CURRENT) == []


def test_a_changed_field_changes_only_its_line() -> None:
    entry = changed(BY_LABEL["TASK-001"], status="In progress")

    written = texts(encode([entry], [], CURRENT))

    assert list(written) == ["TODO.md"]
    assert diff("TODO.md", written["TODO.md"]) == ["-  - Status: Awaiting confirmation.", "+  - Status: In progress."]


def test_a_changed_title_goal_and_reference_are_replaced_in_place_with_wrapping() -> None:
    long_goal = "Ein ganz anderes Ziel, das lang genug ist, um umbrochen zu werden, weil es die Breite überschreitet."
    entry = changed(BY_LABEL["STORY-001"], title="Neuer Titel", goal=long_goal)
    entry = replace(entry, refs={"parent": ("EPIC-001",), "dependencies": ("TASK-001", "STORY-002")})

    out = texts(encode([entry], [], CURRENT))["TODO.md"]

    lines = out.splitlines()
    goal = field_lines("Goal", long_goal)
    assert len(goal) == 2
    assert "- `STORY-001` **Neuer Titel**" in lines
    start = lines.index(goal[0])
    assert lines[start : start + 2] == goal
    assert "  - Dependencies: `TASK-001`, `STORY-002`." in lines
    assert lines.index("  - Dependencies: `TASK-001`, `STORY-002`.") < start
    removed = [line for line in diff("TODO.md", out) if line.startswith("-")]
    assert removed == [
        "-- `STORY-001` **Pflicht-Story mit Dokumenten**",
        "-  - Dependencies: None.",
        "-  - Goal: Eine Story mit Notizen und Spec in `items/STORY-001/`.",
    ]


def test_a_field_that_is_missing_is_inserted_at_its_place_and_a_removed_one_is_dropped() -> None:
    entry = changed(BY_LABEL["TASK-001"], summary="Neue Kurzfassung")
    written = texts(encode([entry], [], CURRENT))["TODO.md"].splitlines()
    index = written.index("  - Summary: Neue Kurzfassung")
    assert written[index - 1].startswith("  - Completion criteria:") and written[index + 1] == ""

    without = changed(BY_LABEL["EPIC-001"], summary=None)
    assert "  - Summary: Beispiel für ein laufendes Epic." not in texts(encode([without], [], CURRENT))["TODO.md"]


def test_a_closed_item_moves_to_the_archive_and_leaves_no_gap_in_todo() -> None:
    entry = changed(BY_LABEL["TASK-001"], status="Completed", resolution="Bestätigt.")

    written = texts(encode([entry], [], CURRENT))

    assert "- `TASK-001`" not in written["TODO.md"] and "\n\n\n" not in written["TODO.md"]
    archive = written["archive.md"]
    assert archive.rstrip("\n").endswith("  - Resolution: Bestätigt.")
    assert "- `TASK-001` **Task mit Abhängigkeit**" in archive and "  - Status: Completed." in archive


def test_a_reopened_item_moves_back_and_a_trashed_one_goes_to_the_archive() -> None:
    reopened = changed(BY_LABEL["STORY-003"], status="In progress", resolution=None)
    trashed = changed(BY_LABEL["STORY-002"], deleted="2026-10-12")

    written = texts(encode([reopened, trashed], [], CURRENT))

    assert "- `STORY-003`" in written["TODO.md"] and "  - Resolution:" not in written["TODO.md"].split("`STORY-003`")[1]
    assert "- `STORY-003`" not in written["archive.md"]
    assert (
        "- `STORY-002` **Optionale Story**" in written["archive.md"]
        and "  - Deleted: 2026-10-12." in written["archive.md"]
    )
    assert "- `STORY-002`" not in written["TODO.md"]


def test_a_new_item_is_appended_with_all_fields_in_the_order_of_the_format() -> None:
    entry = MirrorEntry(
        "task",
        "TASK-009",
        {
            "title": "Neu",
            "status": "Open",
            "priority": "Urgent",
            "created": "2026-10-17",
            "goal": "Ziel",
            "completion_criteria": "Kriterien",
            "summary": None,
            "resolution": None,
            "required_for_parent": True,
            "deleted": None,
        },
        {"parent": ("STORY-001",), "dependencies": ("TASK-001",)},
        "11111111-1111-4111-8111-111111111111",
    )

    out = texts(encode([entry], [], CURRENT))["TODO.md"]

    assert out.rstrip("\n").endswith(
        "\n".join(
            [
                "- `TASK-009` **Neu**",
                "  - Uid: 11111111-1111-4111-8111-111111111111.",
                "  - Type: Task.",
                "  - Parent: `STORY-001`.",
                "  - Required for parent: Yes.",
                "  - Status: Open.",
                "  - Created: 2026-10-17.",
                "  - Priority: Urgent.",
                "  - Dependencies: `TASK-001`.",
                "  - Goal: Ziel",
                "  - Completion criteria: Kriterien",
            ]
        )
    )
    assert (
        decode(FileSet({"TODO.md": FileEntry("TODO.md", out, "v")}))[-1].uid == "11111111-1111-4111-8111-111111111111"
    )


def test_a_placeholder_entry_is_replaced_in_place_and_its_documents_are_renamed() -> None:
    fresh = replace(
        changed(next(e for e in ENTRIES if e.placeholder == "NEW-login-dialog"), created="2026-10-17"),
        label="TASK-004",
        uid="22222222-2222-4222-8222-222222222222",
    )
    doc = MirrorEntry(
        "backlog.document",
        "TASK-004_notes.md",
        next(e for e in ENTRIES if e.kind == "backlog.document" and e.placeholder).fields,
        {"item": ("TASK-004",)},
        "22222222-2222-4222-8222-222222222222/notes",
        placeholder="NEW-login-dialog/notes",
    )
    other = replace(BY_LABEL["TASK-002"], refs={"dependencies": ("TASK-004",)})

    changes = encode([fresh, doc, other], [], CURRENT)

    out = texts(changes)["TODO.md"]
    old = CURRENT.files["TODO.md"].text.splitlines()
    new = out.splitlines()
    assert "- `NEW-login-dialog`" not in out
    assert new.index("- `TASK-004` **Neuer Task aus der Cloud**") == old.index(
        "- `NEW-login-dialog` **Neuer Task aus der Cloud**"
    )
    block = new[new.index("- `TASK-004` **Neuer Task aus der Cloud**") :]
    assert block[1] == "  - Uid: 22222222-2222-4222-8222-222222222222." and block[2] == "  - Type: Task."
    assert "  - Created: 2026-10-17." in block
    assert "  - Dependencies: `TASK-004`." in new
    renames = [c for c in changes if isinstance(c, RenameFile)]
    assert renames == [
        RenameFile("items/NEW-login-dialog/NEW-login-dialog_notes.md", "items/TASK-004/TASK-004_notes.md")
    ]


def test_a_retyped_item_gets_a_new_header_and_its_documents_follow() -> None:
    story = BY_LABEL["STORY-001"]
    retyped = replace(story, kind="task", label="TASK-007")
    notes = BY_LABEL.get("x") or next(e for e in ENTRIES if e.label == "STORY-001_notes.md")
    renamed_notes = replace(notes, label="TASK-007_notes.md", refs={"item": ("TASK-007",)})
    spec = next(e for e in ENTRIES if e.label == "STORY-001_spec.md")
    renamed_spec = replace(spec, label="TASK-007_spec.md", refs={"item": ("TASK-007",)})

    changes = encode([retyped, renamed_notes, renamed_spec], [], CURRENT)

    out = texts(changes)["TODO.md"]
    assert "- `TASK-007` **Pflicht-Story mit Dokumenten**" in out and "  - Type: Task." in out
    assert sorted((c.path, c.new_path) for c in changes if isinstance(c, RenameFile)) == [
        ("items/STORY-001/STORY-001_notes.md", "items/TASK-007/TASK-007_notes.md"),
        ("items/STORY-001/STORY-001_spec.md", "items/TASK-007/TASK-007_spec.md"),
    ]


def test_a_document_with_new_content_is_written_and_a_new_document_is_created() -> None:
    notes = next(e for e in ENTRIES if e.label == "STORY-001_notes.md")
    changed_notes = replace(notes, fields={**notes.fields, "content": "\n## 2026-10-03 — Neu\n"})
    topic = MirrorEntry(
        "backlog.document",
        "STORY-001_spec_Teil.md",
        {"content": "# Teil\n", "kind": "spec"},
        {"item": ("STORY-001",)},
        "0b6f2c1e-4d3a-4e8b-9c7d-1a2b3c4d5e02/spec_Teil",
    )

    changes = encode([changed_notes, topic], [], CURRENT)

    assert texts(changes) == {
        "items/STORY-001/STORY-001_notes.md": "# STORY-001 — Pflicht-Story mit Dokumenten\n\n## 2026-10-03 — Neu\n",
        "items/STORY-001/STORY-001_spec_Teil.md": "# Teil\n",
    }


def test_removed_items_and_documents_disappear_from_the_files() -> None:
    gone = BY_LABEL["TASK-003"]
    notes = next(e for e in ENTRIES if e.label == "STORY-001_notes.md")

    changes = encode([], [gone, notes], CURRENT)

    assert "TASK-003" not in texts(changes)["archive.md"]
    assert DeleteFile("items/STORY-001/STORY-001_notes.md") in changes


def test_the_last_entry_removed_leaves_the_section_marked_empty() -> None:
    text = (
        "# Project Backlog Archive\n\nFormat: Claude_Harness backlog format version 3.\n\n## Work items\n\n"
        "- `TASK-001` **Eins**\n  - Uid: 33333333-3333-4333-8333-333333333333.\n  - Type: Task.\n"
    )
    current = FileSet({"archive.md": FileEntry("archive.md", text, "v")})
    entry = MirrorEntry(
        "task", "TASK-001", {"status": "Open", "deleted": None}, {}, "33333333-3333-4333-8333-333333333333"
    )

    out = texts(encode([], [entry], current))["archive.md"]

    assert out.rstrip("\n").endswith("## Work items\n\nNo entries.")


def test_without_any_file_a_new_item_creates_todo_md_from_the_template_and_no_archive() -> None:
    entry = replace(changed(BY_LABEL["EPIC-001"], status="Open"), refs={})

    changes = encode([entry], [], FileSet({}))

    assert list(texts(changes)) == ["TODO.md"]
    out = texts(changes)["TODO.md"]
    assert out.startswith("# Project Backlog\n") and "backlog format version 3" in out and "## Work items" in out
    assert decode(FileSet({"TODO.md": FileEntry("TODO.md", out, "v")}))[0].uid == entry.uid


def test_the_title_line_of_notes_follows_label_and_title_of_the_item() -> None:
    notes = next(e for e in ENTRIES if e.label == "STORY-001_notes.md")
    retyped = replace(
        notes, label="TASK-009_notes.md", refs={"item": ("TASK-009",)}, fields={**notes.fields, "title": "Neu"}
    )

    text = texts(encode([retyped], [], CURRENT))["items/TASK-009/TASK-009_notes.md"]

    assert text.startswith("# TASK-009 — Neu\n\n## 2026-10-02 — Erster Eintrag\n")


def test_list_items_get_their_own_lines_and_never_start_a_soft_wrap() -> None:
    value = "1. Fragen besprochen.\n2. Die Spec liegt vor und ist freigegeben."

    lines = field_lines("Completion criteria", value)

    assert lines[0] == "  - Completion criteria: 1. Fragen besprochen."
    assert lines[1] == "    2. Die Spec liegt vor und ist freigegeben."

    wrapped = field_lines(
        "Goal",
        "Ein langer Satz, der ziemlich lang ist und umbrochen werden muss, bis Version 1. 2. wird danach erwähnt",
    )
    assert not any(line.strip()[:2] == "2." for line in wrapped[1:])


def test_a_list_survives_writing_and_reading() -> None:
    from viewer.plugins.backlog.infrastructure.mirror.syntax import parse_blocks, same_text  # noqa: PLC0415

    value = "1. Erstens\n2. Zweitens, mit sehr viel Text " + "x " * 60 + "\n3. Drittens"
    text = "- `TASK-001`  **T**\n" + "\n".join(field_lines("Goal", value)) + "\n"

    read = parse_blocks(text.splitlines())[0].fields[0].value

    assert read.count("\n") == 2 and same_text(read, value)
    assert not same_text("Flach 1. Eins 2. Zwei", "Flach 1. Eins\n2. Zwei")


def test_a_new_item_gets_no_area_line_and_the_templates_carry_version_3() -> None:
    entry = replace(changed(BY_LABEL["EPIC-001"], status="Open"), refs={})

    out = texts(encode([entry], [], FileSet({})))["TODO.md"]

    assert "  - Area:" not in out and "backlog format version 3" in out and "version 2" not in out


V2 = read_folder(FIXTURES / "valid")


def test_unchanged_entries_of_a_version_2_file_are_not_rewritten_because_of_area() -> None:
    known = [e for e in decode(V2) if e.uid is not None]

    assert encode(known, [], V2) == []


def test_a_changed_entry_in_a_version_2_file_loses_area_and_the_file_becomes_version_3() -> None:
    entry = changed({e.label: e for e in decode(V2) if e.label}["TASK-001"], status="In progress")

    out = texts(encode([entry], [], V2))["TODO.md"]

    assert "backlog format version 3" in out and "backlog format version 2" not in out
    task = out.split("- `TASK-001`")[1].split("\n- `")[0]
    assert "  - Area:" not in task and "  - Status: In progress." in task
    other = out.split("- `STORY-001`")[1].split("\n- `")[0]
    assert "  - Area:" in other  # ein unveränderter Eintrag behält sie; gelesen wird sie ignoriert
    assert {e.label: dict(e.fields) for e in decode(FileSet({**V2.files, "TODO.md": FileEntry("TODO.md", out, "v")}))}[
        "TASK-001"
    ]["status"] == "In progress"

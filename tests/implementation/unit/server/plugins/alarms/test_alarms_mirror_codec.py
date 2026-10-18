from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest
from mirror_files import FIXTURES, read_folder
from viewer.core.domain.files import FileEntry, FileSet, WriteFile
from viewer.core.domain.sync import MirrorEntry, MirrorFormatError
from viewer.plugins.alarms.infrastructure.mirror.codec import AlarmsCodec
from viewer.plugins.alarms.infrastructure.mirror.decode import decode
from viewer.plugins.alarms.infrastructure.mirror.encode import encode

CURRENT = read_folder(FIXTURES / "valid")
ENTRIES = decode(CURRENT, "Beispiel")
BY_KEY = {str(e.label or e.placeholder): e for e in ENTRIES}

PREAMBLE = "# Alarms\n\nFormat: Claude_Harness backlog format version 2.\n\n## Alarms\n"
BLOCK = "\n- `ALARM-001` **Text**\n  - Uid: u1.\n  - At: 2026-10-20T07:00:00Z.\n  - Status: Pending.\n"


def alarms_file(text: str) -> FileSet:
    return FileSet({"alarms.md": FileEntry("alarms.md", text, "v")})


def failure(text: str) -> MirrorFormatError:
    with pytest.raises(MirrorFormatError) as error:
        decode(alarms_file(text), "Beispiel")
    return error.value


def written(entries: list[MirrorEntry], removed: list[MirrorEntry] | None = None, current: FileSet = CURRENT) -> str:
    changes = encode(entries, removed or [], current, "Beispiel")
    assert len(changes) == 1 and isinstance(changes[0], WriteFile)
    return changes[0].text


def changed(entry: MirrorEntry, **fields: Any) -> MirrorEntry:
    return replace(entry, fields={**entry.fields, **fields})


def test_the_example_has_three_alarms_with_their_fields_and_targets() -> None:
    assert [(e.label, e.placeholder, e.fields["status"]) for e in ENTRIES] == [
        ("ALARM-001", None, "Pending"),
        ("ALARM-002", None, "Snoozed"),
        (None, "NEW-standup", "Pending"),
    ]
    first, second, new = (BY_KEY[k] for k in ("ALARM-001", "ALARM-002", "NEW-standup"))
    assert first.fields["text"] == "An die Story erinnern" and first.fields["at"] == "2026-10-20T07:00:00Z"
    assert dict(first.refs) == {"target": ("STORY-001",)} and dict(first.extra) == {"created": "2026-10-16"}
    assert second.fields["snoozed_until"] == "2026-10-17T07:00:00Z" and dict(second.refs) == {}
    assert (new.uid, dict(new.refs), new.extra["created"]) == (None, {"target": ("Misc:NOTE-003",)}, None)
    assert first.source == ("alarms.md", 8) and first.source_lines["target"] == 11


def test_a_project_of_another_name_keeps_the_target_qualified() -> None:
    assert decode(CURRENT, "Anders")[0].refs["target"] == ("STORY-001",)  # ohne Qualifizierung bleibt es, wie es steht
    assert AlarmsCodec().for_project("Beispiel").decode(CURRENT)[0].refs["target"] == ("STORY-001",)
    qualified = alarms_file(PREAMBLE + BLOCK + "  - Target: `Beispiel:STORY-001`.\n")
    assert decode(qualified, "Beispiel")[0].refs["target"] == ("STORY-001",)
    assert decode(qualified, "Anders")[0].refs["target"] == ("Beispiel:STORY-001",)
    assert AlarmsCodec().decode(qualified)[0].refs["target"] == ("Beispiel:STORY-001",)
    assert AlarmsCodec.patterns == ("alarms.md",)


def test_the_file_is_written_exactly_as_it_was_read() -> None:
    assert encode(ENTRIES, [], CURRENT, "Beispiel") == []


def test_a_changed_field_rewrites_only_its_line() -> None:
    out = written([changed(BY_KEY["ALARM-001"], status="Due")]).splitlines()
    old = CURRENT.files["alarms.md"].text.splitlines()
    assert [(a, b) for a, b in zip(old, out, strict=True) if a != b] == [("  - Status: Pending.", "  - Status: Due.")]


def test_a_new_alarm_replaces_its_block_with_uid_label_and_keeps_the_text() -> None:
    new = replace(BY_KEY["NEW-standup"], label="ALARM-003", uid="u3", extra={"created": "2026-10-17"})
    out = written([new])
    assert "- `NEW-standup`" not in out
    assert out.endswith(
        "- `ALARM-003` **Neuer Wecker aus der Cloud, Ziel in anderem Projekt**\n  - Uid: u3.\n"
        "  - At: 2026-10-21T08:00:00Z.\n  - Target: `Misc:NOTE-003`.\n  - Status: Pending.\n  - Created: 2026-10-17.\n"
    )
    assert out.startswith(CURRENT.files["alarms.md"].text[: CURRENT.files["alarms.md"].text.index("- `ALARM-001`")])


def test_a_removed_alarm_disappears_and_an_empty_file_says_so() -> None:
    assert "ALARM-002" not in written([], [BY_KEY["ALARM-002"]])
    assert written([], ENTRIES).endswith("## Alarms\n\nNo entries.\n")


def test_a_new_file_gets_the_template_and_unset_fields_are_left_out() -> None:
    entry = MirrorEntry(
        "alarms.alarm",
        "ALARM-007",
        {"text": "Neu", "at": "2026-10-20T07:00:00Z", "status": "Done", "snoozed_until": None, "deleted": "2026-10-18"},
        {},
        "u7",
        extra={"created": None},
    )
    out = written([entry], current=FileSet())
    assert out.startswith("# Alarms\n\nFormat: Claude_Harness backlog format version 2.")
    assert out.endswith(
        "- `ALARM-007` **Neu**\n  - Uid: u7.\n  - At: 2026-10-20T07:00:00Z.\n  - Target: None.\n"
        "  - Status: Done.\n  - Deleted: 2026-10-18.\n"
    )
    assert decode(alarms_file(out), "P")[0].fields["deleted"] == "2026-10-18"


def test_a_missing_file_has_no_entries() -> None:
    assert decode(FileSet(), "P") == []


@pytest.mark.parametrize(
    "text,code,line",
    [
        ("# Alarms\n\n## Alarms\n" + BLOCK, "format_version", 1),
        ("# Alarms\n\nFormat: backlog format version 1.\n\n## Alarms\n" + BLOCK, "format_version", 3),
        (PREAMBLE + BLOCK + "  - Colour: red.\n", "unknown_field", 11),
        (PREAMBLE + BLOCK.replace("  - At: 2026-10-20T07:00:00Z.\n", ""), "missing_field", 7),
        (PREAMBLE + BLOCK.replace("  - Status: Pending.\n", ""), "missing_field", 7),
        (PREAMBLE + BLOCK.replace("  - Uid: u1.\n", ""), "missing_field", 7),
        (PREAMBLE + BLOCK.replace("Pending", "Waiting"), "invalid_value", 10),
        (PREAMBLE + BLOCK.replace("2026-10-20T07:00:00Z", "morgen"), "invalid_value", 9),
        (PREAMBLE + BLOCK.replace("Pending", "Snoozed"), "missing_field", 7),
        (PREAMBLE + BLOCK + "  - Snoozed until: 2026-10-21T07:00:00Z.\n", "invalid_value", 11),
        (PREAMBLE + BLOCK + "  - Created: gestern.\n", "invalid_value", 11),
        (PREAMBLE + BLOCK + BLOCK.replace("ALARM-001", "ALARM-002"), "duplicate_uid", 12),
        (PREAMBLE + BLOCK + BLOCK.replace("u1", "u2"), "duplicate_label", 12),
        (PREAMBLE + BLOCK.replace("`ALARM-001`", "`TASK-001`"), "invalid_value", 7),
        (
            PREAMBLE + BLOCK.replace("`ALARM-001`", "`NEW-Gross`").replace("  - Uid: u1.\n", ""),
            "invalid_placeholder",
            7,
        ),
        (PREAMBLE + BLOCK.replace("`ALARM-001`", "`NEW-ok`"), "invalid_value", 8),
    ],
)
def test_format_errors_name_code_and_line(text: str, code: str, line: int) -> None:
    error = failure(text)
    assert (error.code, error.details["file"], error.details["line"]) == (code, "alarms.md", line)


def test_several_targets_without_text_and_a_done_time_round_trip() -> None:
    text = (
        PREAMBLE + "\n- `ALARM-004`\n  - Uid: u4.\n  - At: 2026-10-20T07:00:00Z.\n"
        "  - Target: `NOTE-001`, `Beispiel:EPIC-005`, `Misc:STORY-022`, `NOTE-001`.\n  - Status: Done.\n"
        "  - Done at: 2026-10-18T10:00:00Z.\n"
    )
    [entry] = decode(alarms_file(text), "Beispiel")
    assert entry.refs["target"] == ("NOTE-001", "EPIC-005", "Misc:STORY-022")  # doppelt nur einmal
    assert (entry.fields["text"], entry.fields["done_at"]) == ("", "2026-10-18T10:00:00Z")
    out = written([entry], current=alarms_file(text))
    assert "- `ALARM-004`\n" in out and "  - Target: `NOTE-001`, `EPIC-005`, `Misc:STORY-022`.\n" in out
    assert decode(alarms_file(out), "Beispiel") == [
        replace(entry, source=entry.source, source_lines=entry.source_lines)
    ]


@pytest.mark.parametrize(
    "text,code,line",
    [
        (PREAMBLE + BLOCK.replace("**Text**", "").replace("u1.\n", "u1.\n  - Target: None.\n"), "missing_field", 7),
        (PREAMBLE + BLOCK + "  - Done at: 2026-10-18T10:00:00Z.\n", "invalid_value", 11),
        (PREAMBLE + BLOCK.replace("Pending", "Expired") + "  - Done at: gestern.\n", "invalid_value", 11),
    ],
)
def test_reminder_rules_name_code_and_line(text: str, code: str, line: int) -> None:
    error = failure(text)
    assert (error.code, error.details["line"]) == (code, line)

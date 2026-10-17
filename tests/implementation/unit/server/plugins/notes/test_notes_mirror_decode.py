from __future__ import annotations

import json

import pytest
from mirror_files import FIXTURES, read_folder
from viewer.core.domain.files import FileEntry, FileSet
from viewer.core.domain.sync import MirrorEntry, MirrorFormatError
from viewer.plugins.notes.infrastructure.mirror.codec import NotesCodec
from viewer.plugins.notes.infrastructure.mirror.decode import decode

VALID = read_folder(FIXTURES / "valid")
ENTRIES = decode(VALID, "Beispiel")
BY_KEY = {str(e.label or e.placeholder): e for e in ENTRIES}


def folder(**texts: str) -> FileSet:
    return FileSet({path: FileEntry(path, text, "v") for path, text in texts.items()})


def failure(files: FileSet) -> MirrorFormatError:
    with pytest.raises(MirrorFormatError) as error:
        decode(files, "Beispiel")
    return error.value


def with_note(text: str, name: str = "NOTE-001") -> FileSet:
    return folder(**{f"notes/{name}.md": text})


HEADER = "# NOTE-001\nUid: u1\nSummary: S\nStatus: waiting\n"


def test_the_example_project_has_topics_notes_and_documents() -> None:
    kinds = [(e.kind, e.label or e.placeholder) for e in ENTRIES]
    assert kinds == [
        ("notes.topic", "TOPIC-001"),
        ("notes.topic", "TOPIC-002"),
        ("notes.topic", "new:Ideen aus der Cloud"),
        ("notes.note", "NOTE-001"),
        ("notes.note", "NOTE-002"),
        ("notes.note", "new-idee-export"),
        ("notes.document", "NOTE-001_notes.md"),
    ]


def test_topics_carry_their_fields_parent_and_placeholder() -> None:
    root, child, new = BY_KEY["TOPIC-001"], BY_KEY["TOPIC-002"], BY_KEY["new:Ideen aus der Cloud"]
    assert dict(root.fields) == {
        "name": "Sync",
        "due_at": "2026-12-01T00:00:00Z",
        "archived_at": None,
        "deleted_at": None,
    }
    assert root.uid == "0b6f2c1e-4d3a-4e8b-9c7d-1a2b3c4d5e31" and root.extra["created"] == "2026-09-01T09:00:00Z"
    assert (child.fields["name"], child.fields["archived_at"], dict(child.refs)) == (
        "Format | Dateien",
        "2026-10-05T09:00:00Z",
        {"parent": ("TOPIC-001",)},
    )
    assert (new.uid, new.label, new.placeholder) == (None, None, "new:Ideen aus der Cloud")


def test_a_note_has_fields_triggers_references_and_extra() -> None:
    note = BY_KEY["NOTE-001"]
    assert (note.uid, note.fields["summary"], note.fields["status"], note.fields["mode"]) == (
        "0b6f2c1e-4d3a-4e8b-9c7d-1a2b3c4d5e21",
        "Note mit Auslösern, Links und Dokument",
        "waiting",
        "all",
    )
    assert note.fields["review_at"] == "2026-11-07T08:00:00Z" and note.fields["archived"] is False
    assert note.fields["body"] == "# Überschrift\n\nLangtext mit Umlauten: äöü ß."
    assert note.fields["triggers"] == [
        {"kind": "event", "status": "Completed", "fired_at": "2026-10-12T08:00:00Z", "already_met": True},
        {"kind": "event", "status": "Completed", "fired_at": None, "already_met": False},
        {"kind": "topic_date", "status": None, "fired_at": None, "already_met": False},
    ]
    assert dict(note.refs) == {
        "topic": ("TOPIC-001",),
        "reference": ("STORY-001", "TOPIC-002", "new-idee-export"),
        "origin": ("STORY-002",),
        "trigger_targets": ("STORY-003", "TASK-001"),
    }
    assert dict(note.extra) == {"created": "2026-10-01T09:30:00Z", "updated": "2026-10-12T08:00:00Z"}
    assert note.source == ("notes/NOTE-001.md", 1)
    assert note.source_lines["reference:STORY-001"] == 17


def test_a_note_in_the_trash_and_archive_has_no_body() -> None:
    note = BY_KEY["NOTE-002"]
    assert (note.fields["status"], note.fields["archived"], note.fields["deleted_at"], note.fields["body"]) == (
        "done",
        True,
        "2026-10-02T10:00:00Z",
        "",
    )
    assert note.fields["review_at"] is None and dict(note.refs) == {"topic": ("TOPIC-002",)}


def test_a_new_note_has_a_placeholder_and_references_other_placeholders() -> None:
    note = BY_KEY["new-idee-export"]
    assert (note.uid, note.label, note.placeholder) == (None, None, "new-idee-export")
    assert dict(note.refs) == {"topic": ("new:Ideen aus der Cloud",), "reference": ("NEW-login-dialog",)}
    assert note.fields["body"] == "Text."


def test_a_document_belongs_to_its_note_by_uid_and_suffix() -> None:
    document = BY_KEY["NOTE-001_notes.md"]
    assert document.uid == "0b6f2c1e-4d3a-4e8b-9c7d-1a2b3c4d5e21/notes"
    assert dict(document.refs) == {"note": ("NOTE-001",)} and document.fields["kind"] == "notes"


def test_a_document_of_a_new_note_has_a_placeholder() -> None:
    files = folder(
        **{
            "notes/new-a.md": "# NEW\nSummary: S\nStatus: waiting\n",
            "notes/new-a_spec_api.md": "Spec",
            "notes/NOTE-009_notes.md": "ohne Note",
        }
    )
    entries = decode(files, "P")
    document = next(e for e in entries if e.kind == "notes.document")
    assert (document.uid, document.placeholder, dict(document.refs)) == (None, "new-a/spec_api", {"note": ("new-a",)})
    assert len([e for e in entries if e.kind == "notes.document"]) == 1


def test_a_target_of_another_project_name_stays_qualified() -> None:
    files = with_note(HEADER + "Links:\n- reference Beispiel:STORY-001\n- reference Andere:NOTE-003\n")
    assert decode(files, "Beispiel")[0].refs["reference"] == ("Andere:NOTE-003", "STORY-001")
    assert decode(files, "Andere")[0].refs["reference"] == ("Beispiel:STORY-001", "NOTE-003")


def test_a_project_name_with_spaces_works_in_links_and_triggers() -> None:
    files = with_note(
        HEADER
        + "Triggers:\n- event Mein Projekt:STORY-003 In progress [fired 2026-10-12T08:00:00Z]\n"
        + "Links:\n- origin Mein Projekt:TASK-1\n"
    )
    note = decode(files, "Mein Projekt")[0]
    assert note.refs["trigger_targets"] == ("STORY-003",) and note.refs["origin"] == ("TASK-1",)
    assert note.fields["triggers"][0]["status"] == "In progress"


def test_the_codec_is_bound_to_the_name_of_the_project() -> None:
    codec = NotesCodec().for_project("Beispiel")
    assert codec.decode(VALID)[3].refs["origin"] == ("STORY-002",)
    assert NotesCodec().decode(VALID)[3].refs["origin"] == ("Beispiel:STORY-002",)
    assert NotesCodec.patterns == ("notes/*.md",)


def test_counters_and_unknown_files_are_ignored() -> None:
    files = folder(**{"notes/counters.md": "NOTE: 15\n", "notes/readme.md": "x", "notes/NOTE-001.md.bak": "x"})
    assert decode(files, "P") == []


def test_line_endings_and_other_files_do_not_matter_for_the_entries() -> None:
    assert [e for e in decode(folder(**{"TODO.md": "x"}), "P")] == []


@pytest.mark.parametrize("code", ["file_label_mismatch", "unknown_trigger"])
def test_the_invalid_examples_name_file_line_and_code(code: str) -> None:
    root = FIXTURES / "invalid" / code
    expected = json.loads((root / "expected.json").read_text())
    error = failure(read_folder(root))
    assert (error.code, error.details["file"], error.details["line"]) == (
        expected["code"],
        expected["file"],
        expected["line"],
    )


@pytest.mark.parametrize(
    "text,code,line",
    [
        ("# NOTE-002\nUid: u\nSummary: S\nStatus: waiting\n", "file_label_mismatch", 1),
        (HEADER + "Colour: red\n", "unknown_field", 5),
        (HEADER.replace("Summary: S\n", ""), "missing_field", 1),
        (HEADER.replace("Uid: u1\n", ""), "missing_field", 1),
        (HEADER.replace("waiting", "due"), "invalid_value", 4),
        (HEADER.replace("waiting", "weird"), "invalid_value", 4),
        (HEADER + "Mode: some\n", "invalid_value", 5),
        (HEADER + "Archived: yes\n", "invalid_value", 5),
        (HEADER + "Review: morgen\n", "invalid_value", 5),
        (HEADER + "Review: 2026-10-12\n", "invalid_value", 5),
        (HEADER + "Status: waiting\n", "invalid_value", 5),
        (HEADER + "- reference X:Y\n", "invalid_value", 5),
        (HEADER + "Links:\n- mention X:Y\n", "invalid_value", 6),
        (HEADER + "Triggers:\n- time 2026-10-12T08:00:00Z\n", "unknown_trigger", 6),
        (HEADER + "Triggers:\n- sometimes\n", "unknown_trigger", 6),
        (HEADER + "Triggers:\n- event Beispiel:STORY-001 Open\n", "invalid_value", 6),
        (HEADER + "Triggers:\n- event Beispiel:STORY-001 Completed [fired gestern]\n", "invalid_value", 6),
        (HEADER + "Triggers:\n- event Beispiel:STORY-001 Completed [odd]\n", "invalid_value", 6),
        (HEADER + "Links:\nTriggers: x\n", "invalid_value", 6),
        ("# NOTE-001\nSummary S\n", "invalid_value", 2),
    ],
)
def test_format_errors_name_code_and_line(text: str, code: str, line: int) -> None:
    error = failure(with_note(text))
    assert (error.code, error.details["line"]) == (code, line)
    assert error.details["file"] == "notes/NOTE-001.md"


def test_a_new_note_needs_a_valid_placeholder() -> None:
    error = failure(folder(**{"notes/new-Gross.md": "# NEW\nSummary: S\nStatus: waiting\n"}))
    assert error.code == "invalid_placeholder"


def test_a_new_note_has_no_uid() -> None:
    error = failure(folder(**{"notes/new-a.md": "# NEW\nUid: u\nSummary: S\nStatus: waiting\n"}))
    assert (error.code, error.details["line"]) == ("invalid_value", 2)


def test_two_notes_with_the_same_uid_are_refused() -> None:
    files = folder(**{"notes/NOTE-001.md": HEADER, "notes/NOTE-002.md": HEADER.replace("NOTE-001", "NOTE-002")})
    error = failure(files)
    assert (error.code, error.details["file"]) == ("duplicate_uid", "notes/NOTE-002.md")


def test_two_new_notes_cannot_share_a_placeholder_across_topics_and_notes() -> None:
    topics = "- NEW | A | due=\n- NEW | A | due=\n"
    error = failure(folder(**{"notes/topics.md": topics}))
    assert (error.code, error.details["file"], error.details["line"]) == ("invalid_placeholder", "notes/topics.md", 2)


@pytest.mark.parametrize(
    "text,code,line",
    [
        ("kein Eintrag\n", "invalid_value", 1),
        ("- TOPIC-001 | A\n", "missing_field", 1),
        ("- TOPIC-001 | A | uid=u | colour=red\n", "unknown_field", 1),
        ("- TOPIC-001 | A | uid=u | due=morgen\n", "invalid_value", 1),
        ("- TOPIC-001 | A | uid=u\n   - TOPIC-002 | B | uid=v\n", "invalid_value", 2),
        ("- TOPIC-001 | A | uid=u\n    - TOPIC-002 | B | uid=v\n", "invalid_value", 2),
        ("- TOPIC-001 |  | uid=u\n", "missing_field", 1),
        ("- TOPIC-001 | A | uid=u\n- TOPIC-001 | B | uid=v\n", "duplicate_label", 2),
        ("- TOPIC-001 | A | uid=u\n- TOPIC-002 | B | uid=u\n", "duplicate_uid", 2),
    ],
)
def test_topic_lines_name_code_and_line(text: str, code: str, line: int) -> None:
    error = failure(folder(**{"notes/topics.md": text}))
    assert (error.code, error.details["file"], error.details["line"]) == (code, "notes/topics.md", line)


def test_topic_names_unescape_pipes_backslashes_and_newlines() -> None:
    topics = decode(folder(**{"notes/topics.md": "- TOPIC-001 | a \\| b \\\\ c\\nd | uid=u\n"}), "P")
    assert topics[0].fields["name"] == "a | b \\ c\nd"


def test_entries_hash_by_content_not_by_where_they_came_from() -> None:
    again = decode(VALID, "Beispiel")
    assert [e.hash for e in again] == [e.hash for e in ENTRIES]
    one = BY_KEY["NOTE-001"]
    assert isinstance(one, MirrorEntry) and one.hash == again[3].hash

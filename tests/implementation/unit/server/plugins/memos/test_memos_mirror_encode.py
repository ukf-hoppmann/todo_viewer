from __future__ import annotations

from dataclasses import replace
from typing import Any

from mirror_files import FIXTURES, read_folder
from viewer.core.domain.files import Change, DeleteFile, FileEntry, FileSet, RenameFile, WriteFile
from viewer.core.domain.sync import MirrorEntry
from viewer.plugins.memos.infrastructure.mirror.decode import decode
from viewer.plugins.memos.infrastructure.mirror.encode import encode, render_memo

CURRENT = read_folder(FIXTURES / "valid")
ENTRIES = decode(CURRENT, "Beispiel")
BY_KEY = {str(e.label or e.placeholder): e for e in ENTRIES}


def written(changes: list[Change]) -> dict[str, str]:
    return {c.path: c.text for c in changes if isinstance(c, WriteFile)}


def changed(entry: MirrorEntry, **fields: Any) -> MirrorEntry:
    return replace(entry, fields={**entry.fields, **fields})


def test_every_memo_of_the_examples_is_written_exactly_as_it_was_read() -> None:
    for key in ("MEMO-001", "MEMO-002", "new-idee-export"):
        path = f"memos/{key}.md"
        assert render_memo(BY_KEY[key], "Beispiel") == CURRENT.files[path].text, path


def test_topics_are_written_exactly_as_they_were_read() -> None:
    topics = [e for e in ENTRIES if e.kind == "memos.topic"]
    assert written(encode(topics, [], CURRENT, "Beispiel"))["memos/topics.md"] == CURRENT.files["memos/topics.md"].text


def test_unchanged_documents_cause_no_change() -> None:
    assert encode([BY_KEY["MEMO-001_notes.md"]], [], CURRENT, "Beispiel") == []


def test_a_changed_field_rewrites_only_that_memo() -> None:
    out = written(encode([changed(BY_KEY["MEMO-001"], status="snoozed")], [], CURRENT, "Beispiel"))
    assert list(out) == ["memos/MEMO-001.md"]
    old, new = CURRENT.files["memos/MEMO-001.md"].text.splitlines(), out["memos/MEMO-001.md"].splitlines()
    assert [(a, b) for a, b in zip(old, new, strict=True) if a != b] == [("Status: waiting", "Status: snoozed")]


def test_references_and_triggers_are_written_as_the_file_names_them() -> None:
    entry = replace(
        changed(
            BY_KEY["MEMO-001"],
            triggers=[{"kind": "event", "status": "Rejected", "fired_at": None, "already_met": False}],
        ),
        refs={"reference": ("Andere:MEMO-003", "MEMO-005", "TOPIC-001", "STORY-001"), "trigger_targets": ("TASK-009",)},
    )
    text = written(encode([entry], [], CURRENT, "Beispiel"))["memos/MEMO-001.md"]
    assert "- event Beispiel:TASK-009 Rejected\n" in text
    assert (
        "Links:\n- reference Andere:MEMO-003\n- reference memo:MEMO-005\n- reference topic:TOPIC-001\n"
        "- reference Beispiel:STORY-001\n" in text
    )
    assert "Topic: \n" not in text and "Topic:\n" in text


def test_a_memo_without_body_or_links_has_a_short_file() -> None:
    entry = replace(changed(BY_KEY["MEMO-002"], deleted_at=None, archived=False, status="waiting"), refs={})
    text = render_memo(entry, "P")
    assert text.endswith("Archived: false\nDeleted:\n") and "Links:" not in text and "Triggers:" not in text


def test_the_body_stands_after_one_empty_line() -> None:
    text = render_memo(changed(BY_KEY["MEMO-002"], body="Zeile 1\nZeile 2"), "P")
    assert text.endswith("Deleted: 2026-10-02T10:00:00Z\n\nZeile 1\nZeile 2\n")


def test_a_new_memo_gets_label_and_uid_and_replaces_its_file_and_documents() -> None:
    files = FileSet(
        {
            **CURRENT.files,
            "memos/new-idee-export_notes.md": FileEntry("memos/new-idee-export_notes.md", "# Doku\n", "v"),
        }
    )
    memo = replace(BY_KEY["new-idee-export"], label="MEMO-003", uid="u-3", refs={"topic": ("TOPIC-003",)})
    document = MirrorEntry(
        "memos.document",
        "MEMO-003_notes.md",
        {"content": "# Doku\n", "kind": "notes"},
        {"memo": ("MEMO-003",)},
        "u-3/memos",
        "new-idee-export/notes",
    )

    changes = encode([memo, document], [], files, "Beispiel")

    assert DeleteFile("memos/new-idee-export.md") in changes
    assert RenameFile("memos/new-idee-export_notes.md", "memos/MEMO-003_notes.md") in changes
    text = written(changes)["memos/MEMO-003.md"]
    assert text.startswith("# MEMO-003\nUid: u-3\n") and "Topic: TOPIC-003\n" in text
    assert not [c for c in changes if isinstance(c, WriteFile) and c.path.endswith("_notes.md")]


def test_a_renamed_document_with_other_content_is_also_written() -> None:
    files = FileSet({"memos/new-a_spec.md": FileEntry("memos/new-a_spec.md", "alt", "v")})
    document = MirrorEntry(
        "memos.document",
        "MEMO-004_spec.md",
        {"content": "neu", "kind": "spec"},
        {"memo": ("MEMO-004",)},
        "u/spec",
        "new-a/spec",
    )

    changes = encode([document], [], files, "P")

    assert changes == [
        RenameFile("memos/new-a_spec.md", "memos/MEMO-004_spec.md"),
        WriteFile("memos/MEMO-004_spec.md", "neu"),
    ]


def test_a_new_topic_replaces_its_row_in_place_and_keeps_the_order() -> None:
    new = BY_KEY["new:Ideen aus der Cloud"]
    topic = replace(new, label="TOPIC-003", uid="u-t3", extra={"created": "2026-10-17T10:00:00Z"})

    out = written(encode([topic], [], CURRENT, "Beispiel"))["memos/topics.md"].splitlines()

    assert len(out) == 3 and out[2] == (
        "- TOPIC-003 | Ideen aus der Cloud | uid=u-t3 | due= | created=2026-10-17T10:00:00Z | archived= | deleted="
    )
    assert out[:2] == CURRENT.files["memos/topics.md"].text.splitlines()[:2]


def test_a_brand_new_topic_goes_below_its_parent_and_a_moved_one_follows() -> None:
    parent = BY_KEY["TOPIC-001"]
    added = MirrorEntry(
        "memos.topic",
        "TOPIC-004",
        {"name": "Neu", "due_at": None, "archived_at": None, "deleted_at": None},
        {"parent": ("TOPIC-001",)},
        "u4",
        extra={"created": None},
    )
    moved = replace(BY_KEY["TOPIC-002"], refs={})

    lines = written(encode([added, moved], [], CURRENT, "Beispiel"))["memos/topics.md"].splitlines()

    assert [line.split(" | ")[0] for line in lines] == ["- TOPIC-001", "  - TOPIC-004", "- TOPIC-002", "- NEW"]
    assert parent.label == "TOPIC-001"


def test_a_removed_topic_leaves_its_children_at_the_top() -> None:
    lines = written(encode([], [BY_KEY["TOPIC-001"]], CURRENT, "Beispiel"))["memos/topics.md"].splitlines()
    assert [line.split(" | ")[0] for line in lines] == ["- TOPIC-002", "- NEW"]


def test_removing_all_topics_deletes_the_file() -> None:
    topics = [e for e in ENTRIES if e.kind == "memos.topic"]
    assert encode([], topics, CURRENT, "Beispiel") == [DeleteFile("memos/topics.md")]


def test_removed_memos_and_documents_delete_their_files() -> None:
    changes = encode(
        [], [BY_KEY["MEMO-002"], BY_KEY["MEMO-001_notes.md"], BY_KEY["new-idee-export"]], CURRENT, "Beispiel"
    )
    assert sorted(c.path for c in changes if isinstance(c, DeleteFile)) == [
        "memos/MEMO-001_notes.md",
        "memos/MEMO-002.md",
        "memos/new-idee-export.md",
    ]


def test_a_leftover_counters_file_goes_with_the_next_write() -> None:
    files = FileSet({**CURRENT.files, "memos/counters.md": FileEntry("memos/counters.md", "MEMO: 5\n", "v")})
    changes = encode([changed(BY_KEY["MEMO-002"], summary="Anders")], [], files, "Beispiel")
    assert DeleteFile("memos/counters.md") in changes
    assert encode([], [], files, "Beispiel") == []


def test_names_with_special_characters_survive_a_round_trip() -> None:
    topic = MirrorEntry(
        "memos.topic",
        "TOPIC-009",
        {"name": "a | b \\ c\nd", "due_at": None, "archived_at": None, "deleted_at": None},
        {},
        "u9",
        extra={"created": None},
    )
    text = written(encode([topic], [], FileSet(), "P"))["memos/topics.md"]
    back = decode(FileSet({"memos/topics.md": FileEntry("memos/topics.md", text, "v")}), "P")
    assert back[0].fields["name"] == "a | b \\ c\nd"

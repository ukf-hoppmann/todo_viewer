from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

import pytest
from mindmap_mirror_files import FIXTURES, read_folder
from viewer.core.domain.files import Change, DeleteFile, FileEntry, FileSet, RenameFile, WriteFile
from viewer.core.domain.sync import MirrorEntry
from viewer.plugins.mindmap.infrastructure.mirror.codec import MindmapCodec
from viewer.plugins.mindmap.infrastructure.mirror.decode import decode

VALID = read_folder(FIXTURES / "valid")
ENTRIES = decode(VALID, "Beispiel")
CODEC = MindmapCodec("Beispiel")
EMPTY = FileSet({})
IDEEN = "9a2b0f4c-0d5e-4f60-8a71-2b3c4d5e6f71"


def written(changes: Sequence[Change]) -> dict[str, str]:
    return {c.path: c.text for c in changes if isinstance(c, WriteFile)}


def apply(current: FileSet, changes: Sequence[Change]) -> FileSet:
    files = dict(current.files)
    for change in changes:
        if isinstance(change, WriteFile):
            files[change.path] = FileEntry(change.path, change.text, "v")
        elif isinstance(change, DeleteFile):
            del files[change.path]
        elif isinstance(change, RenameFile):
            files[change.new_path] = replace(files.pop(change.path), path=change.new_path)
    return FileSet(files)


def entry(key: str) -> MirrorEntry:
    return next(e for e in ENTRIES if (e.label or e.placeholder or e.uid) == key)


def test_every_file_of_the_example_comes_back_byte_for_byte() -> None:
    changes = CODEC.for_project("Beispiel").encode(ENTRIES, [], EMPTY)
    assert written(changes) == {path: file.text for path, file in VALID.files.items()}
    assert not [c for c in changes if not isinstance(c, WriteFile)]


def test_encode_after_decode_changes_nothing_in_an_unchanged_folder() -> None:
    assert CODEC.encode(ENTRIES, [], VALID) == []


def test_a_changed_node_rewrites_only_its_file() -> None:
    node = entry("NODE-002")
    changed = replace(node, fields={**node.fields, "title": "Seite", "text": "Neu\nmit Zeile", "mark": "later"})
    (change,) = CODEC.encode([changed], [], VALID)
    assert change == WriteFile(
        "mindmap/NODE-002.md",
        "# NODE-002\nUid: 5d1c0c2e-7a53-4a0e-9f3b-0c9f8f6e1a02\nTitle: Seite\nMark: later\nDeleted:\n"
        "\nNeu\nmit Zeile\n",
    )


def test_assignments_are_written_sorted_with_the_project_name() -> None:
    node = entry("NODE-002")
    changed = replace(node, refs={"items": ("TASK-2", "Misc:TASK-1", "TASK-1"), "memos": ("MEMO-2",)})
    text = written(CODEC.encode([changed], [], VALID))["mindmap/NODE-002.md"]
    assert "Items:\n- Misc:TASK-1\n- Beispiel:TASK-1\n- Beispiel:TASK-2\nMemos:\n- Beispiel:MEMO-2\n" in text


def test_a_new_node_gets_label_and_uid_and_its_files_move() -> None:
    new = entry("new-cloud-ast")
    assigned = replace(new, label="NODE-008", uid="u8", placeholder="new-cloud-ast")
    document = MirrorEntry(
        "mindmap.document", "NODE-008_spec.md", {"content": "Spec\n", "kind": "spec"}, {"node": ("NODE-008",)},
        "u8/spec", "new-cloud-ast/spec",
    )  # fmt: skip
    current = apply(VALID, [WriteFile("mindmap/new-cloud-ast_spec.md", "Alt\n")])
    changes = CODEC.encode([assigned, document], [], current)
    after = apply(current, changes)
    assert "mindmap/new-cloud-ast.md" not in after.files and "mindmap/NODE-008.md" in after.files
    assert after.files["mindmap/NODE-008.md"].text.startswith("# NODE-008\nUid: u8\nTitle: Ast aus der Cloud\n")
    assert RenameFile("mindmap/new-cloud-ast_spec.md", "mindmap/NODE-008_spec.md") in changes
    assert after.files["mindmap/NODE-008_spec.md"].text == "Spec\n"


def test_a_new_map_gets_a_uid_and_a_file_named_after_its_name() -> None:
    new = entry("new-cloud-entwuerfe")
    assigned = replace(new, uid="t9")
    changes = CODEC.encode([assigned], [], VALID)
    after = apply(VALID, changes)
    assert "mindmap/maps/new-cloud-entwuerfe.md" not in after.files
    assert after.files["mindmap/maps/cloud-entwuerfe.md"].text.startswith(
        "# Cloud-Entwürfe\nFormat: mindmap format version 1\nUid: t9\n"
    )


def test_renaming_a_map_renames_its_file_and_a_name_clash_gets_a_number() -> None:
    ideen = entry(IDEEN)
    renamed = replace(ideen, fields={**ideen.fields, "name": "Neue Ideen"})
    after = apply(VALID, CODEC.encode([renamed], [], VALID))
    assert "mindmap/maps/ideen.md" not in after.files and "mindmap/maps/neue-ideen.md" in after.files
    clash = replace(ideen, fields={**ideen.fields, "name": "Alte-Ideen"})
    assert written(CODEC.encode([clash], [], VALID)).keys() == {"mindmap/maps/alte-ideen-2.md"}


def test_a_map_keeps_a_numbered_file_while_its_name_matches() -> None:
    current = apply(VALID, [RenameFile("mindmap/maps/ideen.md", "mindmap/maps/ideen-2.md")])
    assert CODEC.encode([entry(IDEEN)], [], current) == []


def test_moving_a_branch_changes_only_the_tree_file() -> None:
    ideen = entry(IDEEN)
    moved = replace(ideen, fields={**ideen.fields, "depths": [0, 0]})
    (change,) = CODEC.encode([moved], [], VALID)
    assert isinstance(change, WriteFile) and change.path == "mindmap/maps/ideen.md"
    assert "- NODE-005\n- NODE-007\n" in change.text


def test_an_empty_tree_is_only_its_head() -> None:
    project = entry("9a2b0f4c-0d5e-4f60-8a71-2b3c4d5e6f70")
    empty = replace(project, fields={**project.fields, "depths": [], "removed": []}, refs={})
    text = written(CODEC.encode([empty], [], EMPTY))["mindmap/project.md"]
    assert text == (
        "# Projekt\nFormat: mindmap format version 1\nUid: 9a2b0f4c-0d5e-4f60-8a71-2b3c4d5e6f70\nKind: project\n"
    )
    assert decode(FileSet({"mindmap/project.md": FileEntry("mindmap/project.md", text, "v")}), "Beispiel")[0].refs == {}


def test_removed_entries_delete_their_files() -> None:
    gone = [entry("NODE-006"), entry("9a2b0f4c-0d5e-4f60-8a71-2b3c4d5e6f72"), entry("NODE-001_notes.md")]
    changes = CODEC.encode([], gone, VALID)
    assert sorted(c.path for c in changes if isinstance(c, DeleteFile)) == [
        "mindmap/NODE-001_notes.md",
        "mindmap/NODE-006.md",
        "mindmap/maps/alte-ideen.md",
    ]


def test_a_removed_unknown_entry_deletes_nothing() -> None:
    assert CODEC.encode([], [entry("NODE-006")], EMPTY) == []


def test_the_codec_without_a_project_writes_bare_labels_with_an_empty_qualifier() -> None:
    node = entry("NODE-001")
    assert ":STORY-101" in written(MindmapCodec().encode([node], [], EMPTY))["mindmap/NODE-001.md"]


@pytest.mark.parametrize("key", ["NODE-001", "NODE-003", "NODE-006", "new-cloud-ast"])
def test_a_node_survives_decode_after_encode(key: str) -> None:
    node = entry(key)
    files = apply(EMPTY, CODEC.encode([node], [], EMPTY))
    (again,) = decode(files, "Beispiel")
    assert again == node


def test_text_with_blank_lines_at_the_edges_survives() -> None:
    node = entry("NODE-002")
    odd = replace(node, fields={**node.fields, "text": "\n\nMitte\n\n"})
    files = apply(EMPTY, CODEC.encode([odd], [], EMPTY))
    assert decode(files, "Beispiel")[0].fields["text"] == "\n\nMitte\n\n"

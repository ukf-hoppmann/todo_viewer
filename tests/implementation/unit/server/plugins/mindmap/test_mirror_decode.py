from __future__ import annotations

import json

import pytest
from mindmap_mirror_files import FIXTURES, read_folder
from viewer.core.domain.files import FileEntry, FileSet
from viewer.core.domain.sync import MirrorEntry, MirrorFormatError
from viewer.plugins.mindmap.infrastructure.mirror.codec import MindmapCodec
from viewer.plugins.mindmap.infrastructure.mirror.decode import decode

VALID = read_folder(FIXTURES / "valid")
ENTRIES = decode(VALID, "Beispiel")
BY_KEY = {e.kind + ":" + str(e.label or e.placeholder or e.uid): e for e in ENTRIES}
PROJECT_TREE = "9a2b0f4c-0d5e-4f60-8a71-2b3c4d5e6f70"
IDEEN = "9a2b0f4c-0d5e-4f60-8a71-2b3c4d5e6f71"


def folder(**texts: str) -> FileSet:
    return FileSet({path: FileEntry(path, text, "v") for path, text in texts.items()})


def failure(files: FileSet) -> MirrorFormatError:
    with pytest.raises(MirrorFormatError) as error:
        decode(files, "Beispiel")
    return error.value


def where(error: MirrorFormatError) -> tuple[str, str, int | None]:
    return error.code, error.details["file"], error.details["line"]


NODE = "# NODE-001\nUid: u1\nTitle: T\n"
TREE = "# Projekt\nFormat: mindmap format version 1\nUid: t1\nKind: project\n"


def test_the_example_has_trees_nodes_and_documents() -> None:
    kinds = [(e.kind, e.label or e.placeholder or e.uid) for e in ENTRIES]
    assert kinds == [
        ("mindmap.tree", "9a2b0f4c-0d5e-4f60-8a71-2b3c4d5e6f72"),
        ("mindmap.tree", "9a2b0f4c-0d5e-4f60-8a71-2b3c4d5e6f71"),
        ("mindmap.tree", "new-cloud-entwuerfe"),
        ("mindmap.tree", "9a2b0f4c-0d5e-4f60-8a71-2b3c4d5e6f70"),
        *[("mindmap.node", f"NODE-00{n}") for n in range(1, 8)],
        ("mindmap.node", "new-cloud-ast"),
        ("mindmap.document", "NODE-001_notes.md"),
        ("mindmap.document", "NODE-001_spec.md"),
        ("mindmap.document", "NODE-001_spec_format.md"),
    ]


def test_a_node_carries_its_fields_and_assignments() -> None:
    node = BY_KEY["mindmap.node:NODE-001"]
    assert node.uid == "5d1c0c2e-7a53-4a0e-9f3b-0c9f8f6e1a01"
    assert dict(node.fields) == {
        "title": "Mindmap-Ansichten",
        "text": "Freitext des Knotens mit Umlauten: äöü ß.\n\nZweiter Absatz.",
        "mark": "later",
        "deleted_at": None,
    }
    assert dict(node.refs) == {"items": ("STORY-101",), "memos": ("MEMO-004",)}
    assert node.source == ("mindmap/NODE-001.md", 1)


def test_items_of_other_projects_keep_their_project_and_targets_are_sorted() -> None:
    node = BY_KEY["mindmap.node:NODE-003"]
    assert node.refs["items"] == ("Misc:TASK-009", "TASK-001")
    assert node.refs["memos"] == ("MEMO-001", "MEMO-004")


def test_a_node_without_text_has_none_and_a_deleted_one_a_time() -> None:
    assert BY_KEY["mindmap.node:NODE-002"].fields["text"] is None
    assert BY_KEY["mindmap.node:NODE-002"].refs == {}
    assert BY_KEY["mindmap.node:NODE-006"].fields["deleted_at"] == "2026-11-10T08:00:00Z"
    assert BY_KEY["mindmap.node:NODE-004"].fields["mark"] == "discarded"


def test_a_new_node_has_a_placeholder_and_no_uid() -> None:
    node = BY_KEY["mindmap.node:new-cloud-ast"]
    assert (node.uid, node.label, node.placeholder) == (None, None, "new-cloud-ast")
    assert node.refs["memos"] == ("new-idee-export",)


def test_the_project_tree_lists_placements_in_depth_first_order() -> None:
    tree = BY_KEY[f"mindmap.tree:{PROJECT_TREE}"]
    assert dict(tree.fields) == {
        "tree_kind": "project",
        "name": None,
        "deleted_at": None,
        "depths": [0, 1, 1, 2, 0, 1, 0],
        "removed": [{"position": 1, "has_parent": True}],
    }
    assert dict(tree.refs) == {
        "nodes": ("NODE-001", "NODE-002", "NODE-003", "NODE-007", "NODE-004", "NODE-005", "new-cloud-ast"),
        "removed_nodes": ("NODE-006",),
        "removed_parents": ("NODE-004",),
        "removed_groups": ("NODE-006",),
    }


def test_a_free_map_has_a_name_and_a_node_may_stand_in_two_trees() -> None:
    ideen = BY_KEY[f"mindmap.tree:{IDEEN}"]
    assert (ideen.fields["tree_kind"], ideen.fields["name"]) == ("free", "Ideen")
    assert ideen.refs["nodes"] == ("NODE-005", "NODE-007")
    assert ideen.fields["removed"] == [{"position": 0, "has_parent": False}]
    assert "removed_parents" not in ideen.refs
    project = BY_KEY[f"mindmap.tree:{PROJECT_TREE}"]
    assert "NODE-005" in project.refs["nodes"] and "NODE-005" in ideen.refs["nodes"]


def test_trash_and_new_maps() -> None:
    old = BY_KEY["mindmap.tree:9a2b0f4c-0d5e-4f60-8a71-2b3c4d5e6f72"]
    assert old.fields["deleted_at"] == "2026-11-10T08:00:00Z"
    new = BY_KEY["mindmap.tree:new-cloud-entwuerfe"]
    assert (new.uid, new.fields["name"], new.refs["nodes"]) == (None, "Cloud-Entwürfe", ("new-cloud-ast",))


def test_documents_belong_to_their_node() -> None:
    doc = BY_KEY["mindmap.document:NODE-001_spec_format.md"]
    assert doc.uid == "5d1c0c2e-7a53-4a0e-9f3b-0c9f8f6e1a01/spec_format"
    assert dict(doc.refs) == {"node": ("NODE-001",)}
    assert doc.fields["kind"] == "spec" and doc.fields["content"].startswith("# Spec Format")
    assert BY_KEY["mindmap.document:NODE-001_notes.md"].fields["kind"] == "notes"


def test_the_codec_reads_the_same_and_knows_its_pattern() -> None:
    codec = MindmapCodec().for_project("Beispiel")
    assert codec.patterns == ("mindmap/**/*.md",)
    assert codec.decode(VALID) == ENTRIES


def test_other_files_are_ignored() -> None:
    files = folder(**{"mindmap/notizen.md": "irgendwas", "mindmap/maps/readme.txt": "x"})
    assert decode(files, "Beispiel") == []


@pytest.mark.parametrize("path", sorted(p.parent.name for p in (FIXTURES / "invalid").glob("*/expected.json")))
def test_every_invalid_example_is_rejected_where_expected(path: str) -> None:
    directory = FIXTURES / "invalid" / path
    expected = json.loads((directory / "expected.json").read_text(encoding="utf-8"))
    error = failure(read_folder(directory / "files"))
    assert where(error) == (expected["code"], expected["file"], expected["line"])


def test_every_error_code_of_the_format_has_an_example() -> None:
    codes = {p.name for p in (FIXTURES / "invalid").iterdir()}
    assert codes == {
        "format_version", "unknown_field", "missing_field", "invalid_value", "duplicate_uid", "duplicate_label",
        "file_label_mismatch", "invalid_placeholder", "merge_markers", "duplicate_node_in_tree", "tree_cycle",
        "rule_violation",
    }  # fmt: skip


def test_a_tree_without_the_format_line_is_rejected() -> None:
    error = failure(folder(**{"mindmap/project.md": "# Projekt\nUid: t1\nKind: project\n"}))
    assert where(error) == ("format_version", "mindmap/project.md", 1)


def test_a_project_file_must_be_a_project_tree_and_a_map_a_free_one() -> None:
    wrong = TREE.replace("project", "free", 1).replace("Kind: project", "Kind: free")
    assert failure(folder(**{"mindmap/project.md": wrong + "Name: X\n"})).code == "invalid_value"
    assert failure(folder(**{"mindmap/maps/x.md": TREE + "\n"})).code == "invalid_value"


def test_a_free_map_needs_a_name() -> None:
    text = TREE.replace("Kind: project", "Kind: free")
    assert failure(folder(**{"mindmap/maps/x.md": text})).code == "missing_field"


def test_indentation_must_be_even_and_may_not_skip_a_level() -> None:
    assert failure(folder(**{"mindmap/project.md": TREE + "\n- NODE-001\n - NODE-002\n"})).code == "invalid_value"
    skipped = TREE + "\n- NODE-001\n    - NODE-002\n"
    assert failure(folder(**{"mindmap/project.md": skipped})).code == "invalid_value"
    first = TREE + "\n  - NODE-001\n"
    assert failure(folder(**{"mindmap/project.md": first})).code == "invalid_value"


def test_a_node_twice_in_one_tree_is_found_with_its_line() -> None:
    text = TREE + "\n- NODE-001\n  - NODE-002\n- NODE-001\n"
    assert where(failure(folder(**{"mindmap/project.md": text}))) == ("duplicate_node_in_tree", "mindmap/project.md", 8)


def test_a_removed_node_may_not_stand_in_the_tree_too() -> None:
    text = TREE + "\n- NODE-001\n\nRemoved:\n- NODE-001 parent - position 0 group NODE-001\n"
    assert failure(folder(**{"mindmap/project.md": text})).code == "duplicate_node_in_tree"


def test_removed_parents_may_not_form_a_cycle() -> None:
    rows = (
        "- NODE-001 parent NODE-002 position 0 group NODE-001\n- NODE-002 parent NODE-001 position 0 group NODE-001\n"
    )
    assert where(failure(folder(**{"mindmap/project.md": TREE + "\nRemoved:\n" + rows}))) == (
        "tree_cycle",
        "mindmap/project.md",
        7,
    )
    own = "- NODE-001 parent NODE-001 position 0 group NODE-001\n"
    assert failure(folder(**{"mindmap/project.md": TREE + "\nRemoved:\n" + own})).code == "tree_cycle"


def test_two_nodes_may_not_hold_the_same_item_but_a_memo_may_be_shared() -> None:
    a = NODE + "Items:\n- Beispiel:TASK-1\nMemos:\n- Beispiel:MEMO-1\n"
    b = a.replace("NODE-001", "NODE-002").replace("u1", "u2")
    error = failure(folder(**{"mindmap/NODE-001.md": a, "mindmap/NODE-002.md": b}))
    assert where(error) == ("rule_violation", "mindmap/NODE-002.md", 5)
    assert "NODE-001" in str(error)
    shared = b.replace("Items:\n- Beispiel:TASK-1\n", "")
    assert len(decode(folder(**{"mindmap/NODE-001.md": a, "mindmap/NODE-002.md": shared}), "Beispiel")) == 2


def test_the_same_item_twice_in_one_node_is_one_assignment() -> None:
    text = NODE + "Items:\n- Beispiel:TASK-1\n- TASK-1\n"
    (entry,) = decode(folder(**{"mindmap/NODE-001.md": text}), "Beispiel")
    assert entry.refs["items"] == ("TASK-1",)


def test_map_names_are_unique_ignoring_case() -> None:
    def free(uid: str, name: str) -> str:
        return TREE.replace("Kind: project", f"Kind: free\nName: {name}").replace("Uid: t1", f"Uid: {uid}")

    files = folder(**{"mindmap/maps/a.md": free("t2", "Ideen"), "mindmap/maps/b.md": free("t3", "ideen")})
    assert where(failure(files)) == ("duplicate_label", "mindmap/maps/b.md", 5)


def test_a_document_without_a_node_is_rejected() -> None:
    error = failure(folder(**{"mindmap/NODE-009_notes.md": "x"}))
    assert where(error) == ("file_label_mismatch", "mindmap/NODE-009_notes.md", 1)


def test_header_errors() -> None:
    def bad(text: str) -> str:
        return failure(folder(**{"mindmap/NODE-001.md": text})).code

    assert bad("# NODE-002\nUid: u1\nTitle: T\n") == "file_label_mismatch"
    assert bad("# NODE-001\nTitle: T\n") == "missing_field"
    assert bad("# NODE-001\nUid: u1\n") == "missing_field"
    assert bad(NODE + "Color: red\n") == "unknown_field"
    assert bad(NODE + "Mark: wichtig\n") == "invalid_value"
    assert bad(NODE + "Deleted: gestern\n") == "invalid_value"
    assert bad(NODE + "Title: Zwei\n") == "invalid_value"
    assert bad(NODE + "Items:\n- \n") == "invalid_value"
    assert bad(NODE + "- Beispiel:X\n") == "invalid_value"
    assert bad("# NODE-001\nUid: u1\nTitle: T\nUid: u2\n") == "invalid_value"


def test_new_nodes_and_maps_have_no_uid_and_a_valid_placeholder() -> None:
    assert failure(folder(**{"mindmap/new-x.md": "# NEW\nUid: u1\nTitle: T\n"})).code == "invalid_value"
    assert failure(folder(**{"mindmap/new-Gross.md": "# NEW\nTitle: T\n"})).code == "invalid_placeholder"
    assert failure(folder(**{"mindmap/new-x.md": "# NODE-001\nTitle: T\n"})).code == "file_label_mismatch"


def test_the_tree_cannot_name_a_malformed_node_reference() -> None:
    assert failure(folder(**{"mindmap/project.md": TREE + "\n- Knoten\n"})).code == "invalid_value"


def test_merge_markers_are_reported_with_their_line() -> None:
    text = NODE + "\n<<<<<<< HEAD\nA\n=======\nB\n>>>>>>> x\n"
    assert where(failure(folder(**{"mindmap/NODE-001.md": text}))) == ("merge_markers", "mindmap/NODE-001.md", 5)


def test_two_files_with_the_same_uid_are_rejected() -> None:
    files = folder(
        **{"mindmap/NODE-001.md": NODE, "mindmap/NODE-002.md": "# NODE-002\nUid: u1\nTitle: T\n"},
    )
    assert where(failure(files)) == ("duplicate_uid", "mindmap/NODE-002.md", 2)


def test_entries_are_equal_when_content_is_equal() -> None:
    again = decode(VALID, "Beispiel")
    assert [e.hash for e in again] == [e.hash for e in ENTRIES]
    assert all(isinstance(e, MirrorEntry) for e in again)

from __future__ import annotations

from datetime import UTC, datetime

from viewer.core.domain.sync import Conflict, MirrorEntry, explain_conflict

SPEC = (
    "# Spec\n\nKopie von TASK-122 (Planung). Hier liegt sie, wo sie umgesetzt wird.\n\n"
    "Was NSFW-Markierung und Papierkorb angeht, siehe TASK-109.\n"
)
AT = datetime(2026, 10, 22, 13, 42, tzinfo=UTC)


def doc(uid: str, content: str, label: str = "STORY-086_spec_x.md", item: str = "STORY-086") -> MirrorEntry:
    return MirrorEntry("document", label, {"content": content, "kind": "spec"}, {"item": (item,)}, uid)


def deleted_in_files(db: MirrorEntry) -> Conflict:
    return Conflict("deleted_in_files", db.key, db.label, db, None)


def test_deleted_in_files_with_unchanged_database_recommends_taking_the_deletion() -> None:
    db = doc("i/spec_a", SPEC)
    hint = explain_conflict(deleted_in_files(db), {db.key: db.hash}, [], AT)
    assert (hint.database_changed, hint.files_changed) == (False, None)
    assert (hint.recommendation, hint.reason) == ("files", "deleted_other_unchanged")
    assert hint.synced_at == AT
    assert hint.renamed_to is None


def test_deleted_in_files_with_changed_database_recommends_keeping_the_entry() -> None:
    db = doc("i/spec_a", SPEC)
    hint = explain_conflict(deleted_in_files(db), {db.key: doc("i/spec_a", "alt").hash}, [], AT)
    assert hint.database_changed is True
    assert (hint.recommendation, hint.reason) == ("database", "deleted_other_changed")


def test_a_similar_entry_of_the_same_item_on_the_other_side_is_the_rename_partner() -> None:
    db = doc("i/spec_nsfw", SPEC, "STORY-086_spec_nsfw.md")
    renamed = doc("i/spec_sensibel", SPEC.replace("NSFW", "sensible"), "STORY-086_spec_sensibel.md")
    hint = explain_conflict(deleted_in_files(db), {db.key: db.hash}, [renamed], AT)
    assert hint.renamed_to is not None
    assert (hint.renamed_to.key, hint.renamed_to.label) == ("i/spec_sensibel", "STORY-086_spec_sensibel.md")
    assert 0.9 < hint.renamed_to.similarity < 1
    assert (hint.recommendation, hint.reason) == ("files", "renamed")


def test_a_renamed_entry_changed_in_the_database_is_still_kept() -> None:
    db = doc("i/spec_nsfw", SPEC)
    renamed = doc("i/spec_sensibel", SPEC)
    hint = explain_conflict(deleted_in_files(db), {db.key: doc("i/spec_nsfw", "alt").hash}, [renamed], AT)
    assert hint.renamed_to is not None
    assert (hint.recommendation, hint.reason) == ("database", "deleted_other_changed")


def test_unrelated_entries_are_no_rename_partner() -> None:
    db = doc("i/spec_a", SPEC)
    other_text = doc("i/spec_b", "Ganz anderer Text über das Datenmodell. " * 20)
    other_item = doc("j/spec_a", SPEC, item="STORY-087")
    other_kind = MirrorEntry("note", "N", {"content": SPEC}, {"item": ("STORY-086",)}, "n")
    hint = explain_conflict(deleted_in_files(db), {db.key: db.hash}, [other_text, other_item, other_kind], AT)
    assert hint.renamed_to is None


def test_deleted_in_database_mirrors_the_logic() -> None:
    fl = doc("i/spec_a", SPEC)
    conflict = Conflict("deleted_in_database", fl.key, fl.label, None, fl)
    unchanged = explain_conflict(conflict, {fl.key: fl.hash}, [], AT)
    assert (unchanged.database_changed, unchanged.files_changed) == (None, False)
    assert (unchanged.recommendation, unchanged.reason) == ("database", "deleted_other_unchanged")
    changed = explain_conflict(conflict, {fl.key: doc("i/spec_a", "alt").hash}, [], AT)
    assert (changed.recommendation, changed.reason) == ("files", "deleted_other_changed")


def test_both_changed_has_no_recommendation_but_names_the_changed_sides() -> None:
    old, db, fl = doc("i/spec_a", "alt"), doc("i/spec_a", "db"), doc("i/spec_a", "datei")
    hint = explain_conflict(Conflict("both_changed", db.key, db.label, db, fl), {db.key: old.hash}, [], AT)
    assert (hint.database_changed, hint.files_changed) == (True, True)
    assert (hint.recommendation, hint.reason) == ("none", "both_changed")


def test_both_created_has_no_base_and_no_recommendation() -> None:
    db, fl = doc("i/spec_a", "db"), doc("i/spec_a", "datei")
    hint = explain_conflict(Conflict("both_created", db.key, db.label, db, fl), {}, [], None)
    assert (hint.database_changed, hint.files_changed, hint.synced_at) == (None, None, None)
    assert (hint.recommendation, hint.reason) == ("none", "both_created")

from __future__ import annotations

from typing import Any

import pytest
from viewer.core.domain.sync import (
    Conflict,
    DeletionNotConfirmed,
    MirrorEntry,
    Plan,
    compute_plan,
    plan_token,
    resolve_conflicts,
    substitute_placeholders,
    sync_state,
)


def entry(uid: str | None, title: str = "t", label: str | None = "TASK-001", **refs: tuple[str, ...]) -> MirrorEntry:
    return MirrorEntry("task", label, {"title": title}, refs, uid, None if uid else "NEW-x")


def summary(plan: Plan) -> dict[str, Any]:
    return {
        "intents": sorted((i.target, i.action, i.entry.key) for i in plan.intents),
        "conflicts": sorted((c.kind, c.key) for c in plan.conflicts),
        "adopt": sorted(plan.adopt),
        "forget": list(plan.forget),
    }


A, B = entry("a", "alt"), entry("a", "neu")


@pytest.mark.parametrize(
    ("db", "files", "base", "expected"),
    [
        # beide Seiten gleich
        (A, A, A.hash, {}),
        (A, A, None, {"adopt": ["a"]}),  # beidseitig gleich, Basis fehlt: nur nachziehen
        (A, A, B.hash, {"adopt": ["a"]}),
        # eine Seite geändert
        (A, B, A.hash, {"intents": [("database", "update", "a")]}),
        (B, A, A.hash, {"intents": [("files", "update", "a")]}),
        # beide geändert / beide neu mit verschiedenem Inhalt
        (B, entry("a", "dritte"), A.hash, {"conflicts": [("both_changed", "a")]}),
        (A, B, None, {"conflicts": [("both_created", "a")]}),
        # neu auf einer Seite
        (A, None, None, {"intents": [("files", "create", "a")]}),
        (None, A, None, {"intents": [("database", "create", "a")]}),
        # auf einer Seite gelöscht: immer ein Konflikt, auch ohne Änderung der anderen Seite
        (A, None, A.hash, {"conflicts": [("deleted_in_files", "a")]}),
        (B, None, A.hash, {"conflicts": [("deleted_in_files", "a")]}),
        (None, A, A.hash, {"conflicts": [("deleted_in_database", "a")]}),
        (None, B, A.hash, {"conflicts": [("deleted_in_database", "a")]}),
        # auf beiden Seiten weg: Basis vergessen
        (None, None, A.hash, {"forget": ["a"]}),
    ],
)
def test_compute_plan_covers_every_case(
    db: MirrorEntry | None, files: MirrorEntry | None, base: str | None, expected: dict[str, Any]
) -> None:
    plan = compute_plan([db] if db else [], [files] if files else [], {"a": base} if base else {})
    result = summary(plan)
    for name in ("intents", "conflicts", "adopt", "forget"):
        assert result[name] == expected.get(name, []), name


def test_ephemeral_entries_deleted_in_the_database_are_deleted_in_unchanged_files() -> None:
    plan = compute_plan([], [A], {"a": A.hash}, ephemeral=frozenset({"task"}))
    assert summary(plan) == {"intents": [("files", "delete", "a")], "conflicts": [], "adopt": [], "forget": []}


def test_ephemeral_entries_changed_in_the_files_or_deleted_there_stay_conflicts() -> None:
    changed = compute_plan([], [B], {"a": A.hash}, ephemeral=frozenset({"task"}))
    assert summary(changed)["conflicts"] == [("deleted_in_database", "a")]
    gone_in_files = compute_plan([A], [], {"a": A.hash}, ephemeral=frozenset({"task"}))
    assert summary(gone_in_files)["conflicts"] == [("deleted_in_files", "a")]


def test_only_the_marked_kinds_are_ephemeral() -> None:
    plan = compute_plan([], [A], {"a": A.hash}, ephemeral=frozenset({"note"}))
    assert summary(plan)["conflicts"] == [("deleted_in_database", "a")]


def test_label_is_not_part_of_the_hash_but_kind_fields_and_refs_are() -> None:
    assert entry("a", label="TASK-001").hash == entry("a", label="TASK-099").hash
    assert entry("a").hash != MirrorEntry("story", "TASK-001", {"title": "t"}, {}, "a").hash
    assert entry("a").hash != entry("a", "anders").hash
    assert entry("a", parent=("EPIC-001",)).hash != entry("a", parent=("EPIC-002",)).hash
    assert entry("a", parent=("EPIC-001",)).hash == entry("a", parent=("EPIC-001",)).hash


def test_new_entries_without_uid_are_imported_only_with_direction_both() -> None:
    new = entry(None, "neu", label=None)
    both = compute_plan([], [new], {}, "both")
    assert [(i.target, i.action) for i in both.intents] == [("database", "create")]
    only_db = compute_plan([], [new], {}, "to_database")
    assert only_db.intents == () and only_db.not_imported == (new,)
    only_files = compute_plan([], [new], {}, "to_files")
    assert only_files.intents == () and only_files.not_imported == (new,)


def test_direction_restricts_transfers_and_reports_what_was_skipped() -> None:
    db_only, file_only = entry("a", "db"), entry("b", "datei")
    plan = compute_plan([db_only], [file_only], {}, "to_files")
    assert [(i.target, i.entry.key) for i in plan.intents] == [("files", "a")]
    assert [(i.target, i.entry.key) for i in plan.skipped] == [("database", "b")]
    plan = compute_plan([db_only], [file_only], {}, "to_database")
    assert [(i.target, i.entry.key) for i in plan.intents] == [("database", "b")]
    assert [(i.target, i.entry.key) for i in plan.skipped] == [("files", "a")]


def test_conflicts_are_reported_whatever_the_direction() -> None:
    plan = compute_plan([B], [entry("a", "dritte")], {"a": A.hash}, "to_files")
    assert [c.kind for c in plan.conflicts] == ["both_changed"]


def test_plan_without_differences_has_no_changes() -> None:
    assert not compute_plan([A], [A], {"a": A.hash}).changes
    assert compute_plan([A], [B], {"a": A.hash}).changes


# --- Auflösung der Konflikte -------------------------------------------------------------------------------------


def conflict_of(kind_db: MirrorEntry | None, kind_files: MirrorEntry | None, base: str | None) -> Conflict:
    plan = compute_plan([kind_db] if kind_db else [], [kind_files] if kind_files else [], {"a": base} if base else {})
    assert len(plan.conflicts) == 1
    return plan.conflicts[0]


def test_decision_database_overwrites_the_files_and_files_overwrites_the_database() -> None:
    conflict = conflict_of(B, entry("a", "dritte"), A.hash)
    to_files, _, _ = resolve_conflicts([conflict], {"a": "database"})
    to_db, _, _ = resolve_conflicts([conflict], {"a": "files"})
    assert [(i.target, i.action, i.entry.fields["title"]) for i in to_files] == [("files", "update", "neu")]
    assert [(i.target, i.action, i.entry.fields["title"]) for i in to_db] == [("database", "update", "dritte")]


def test_defer_and_missing_decisions_leave_the_conflict_open() -> None:
    conflict = conflict_of(B, entry("a", "dritte"), A.hash)
    for decisions in ({}, {"a": "defer"}, {"other": "files"}):
        intents, open_conflicts, skipped = resolve_conflicts([conflict], decisions)  # type: ignore[arg-type]
        assert (intents, open_conflicts, skipped) == ((), (conflict,), ())


def test_deletion_decisions_need_confirmation() -> None:
    gone_in_files = conflict_of(A, None, A.hash)
    gone_in_db = conflict_of(None, A, A.hash)
    with pytest.raises(DeletionNotConfirmed):
        resolve_conflicts([gone_in_files], {"a": "files"})
    with pytest.raises(DeletionNotConfirmed):
        resolve_conflicts([gone_in_db], {"a": "database"})
    deleted, _, _ = resolve_conflicts([gone_in_files], {"a": "files"}, delete_missing=True)
    assert [(i.target, i.action) for i in deleted] == [("database", "delete")]
    deleted, _, _ = resolve_conflicts([gone_in_db], {"a": "database"}, delete_missing=True)
    assert [(i.target, i.action) for i in deleted] == [("files", "delete")]


def test_keeping_the_surviving_entry_needs_no_confirmation() -> None:
    restored, _, _ = resolve_conflicts([conflict_of(A, None, A.hash)], {"a": "database"})
    assert [(i.target, i.action) for i in restored] == [("files", "create")]
    undeleted, _, _ = resolve_conflicts([conflict_of(None, A, A.hash)], {"a": "files"})
    assert [(i.target, i.action) for i in undeleted] == [("database", "create")]


def test_decisions_against_the_direction_are_skipped() -> None:
    conflict = conflict_of(B, entry("a", "dritte"), A.hash)
    intents, open_conflicts, skipped = resolve_conflicts([conflict], {"a": "files"}, direction="to_files")
    assert intents == () and open_conflicts == () and [i.target for i in skipped] == ["database"]


# --- Token, Zustand, Platzhalter -----------------------------------------------------------------------------------


def test_token_changes_with_anything_in_the_plan() -> None:
    base = compute_plan([A], [B], {"a": A.hash})
    same = compute_plan([A], [B], {"a": A.hash})
    other_content = compute_plan([A], [entry("a", "ganz anders")], {"a": A.hash})
    assert plan_token("p", "both", base) == plan_token("p", "both", same)
    assert plan_token("p", "both", base) != plan_token("p", "both", other_content)
    assert plan_token("p", "both", base) != plan_token("q", "both", base)
    assert plan_token("p", "both", base) != plan_token("p", "to_files", base)


def test_sync_state_names() -> None:
    assert sync_state(compute_plan([A], [A], {"a": A.hash})) == "in_sync"
    assert sync_state(compute_plan([B], [A], {"a": A.hash})) == "primary_changed"
    assert sync_state(compute_plan([A], [B], {"a": A.hash})) == "mirror_changed"
    assert sync_state(compute_plan([entry("x")], [entry("y")], {})) == "both_changed"
    assert sync_state(compute_plan([B], [A, entry(None, label=None)], {"a": A.hash})) == "both_changed"
    assert sync_state(compute_plan([B], [entry("a", "dritte")], {"a": A.hash})) == "conflicts"
    assert sync_state(compute_plan([], [entry(None, label=None)], {}, "to_files")) == "mirror_changed"


def test_placeholders_are_replaced_in_refs_of_all_entries_but_not_in_other_fields() -> None:
    child = entry("c", parent=("NEW-x",), deps=("TASK-001", "NEW-y"))
    untouched = entry("d", parent=("EPIC-001",))
    new_child, same = substitute_placeholders([child, untouched], {"NEW-x": "STORY-070", "NEW-y": "TASK-050"})
    assert new_child.refs == {"parent": ("STORY-070",), "deps": ("TASK-001", "TASK-050")}
    assert same is untouched


U1 = "00000000-0000-0000-0000-000000000001"


def test_a_label_that_differs_only_in_display_makes_the_file_follow_without_a_conflict() -> None:
    database = entry(U1, "t", "TASK-007")  # nach einem Typwechsel in der Datenbank
    files = entry(U1, "t", "STORY-001")  # in der Datei steht noch das alte Label; Inhalt und Hash gleich
    base = {U1: database.hash}

    plan = compute_plan([database], [files], base)

    assert plan.conflicts == () and [(i.target, i.action, i.entry.label) for i in plan.intents] == [
        ("files", "update", "TASK-007")
    ]


def test_the_label_drift_is_not_written_when_the_direction_only_goes_to_the_database() -> None:
    plan = compute_plan(
        [entry(U1, "t", "TASK-007")], [entry(U1, "t", "STORY-001")], {U1: entry(U1).hash}, "to_database"
    )

    assert plan.intents == () and len(plan.skipped) == 1

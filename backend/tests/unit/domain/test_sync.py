from __future__ import annotations

import dataclasses

import pytest

from todo_viewer.domain.documents import content_version
from todo_viewer.domain.errors import (
    BackupFailedError,
    ConflictError,
    SyncPathMissingError,
    SyncRequiredError,
    SyncSameBackendError,
    SyncStaleError,
)
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.source import Source, SyncBaseline
from todo_viewer.domain.sync import (
    Change,
    Choice,
    EntryKey,
    EntryState,
    Resolution,
    Side,
    SyncDirection,
    SyncEntry,
    SyncState,
    check_token,
    classify,
    classify_entry,
    decide,
    default_direction,
    fingerprint,
    merged_items,
    plan_sync,
    primary_and_mirror,
    sync_pair,
)


def item(label: str, title: str = "t", **fields: object) -> Item:
    return Item(id=label, title=title, project="P", **fields)  # type: ignore[arg-type]


def test_sync_pair_is_the_database_project_and_its_markdown_folder():
    source = Source(project="P", path="", backend="database", id="abc", sync_path="/data/md")

    for direction in SyncDirection:
        database, markdown = sync_pair(source, direction)

        assert database == source
        assert (markdown.backend, markdown.path, markdown.project, markdown.id) == ("markdown", "/data/md", "P", "abc")


def test_sync_pair_needs_a_sync_path():
    with pytest.raises(SyncPathMissingError) as error:
        sync_pair(Source(project="P", path="", backend="database", id="abc"), SyncDirection.TO_MD)
    assert error.value.code == "sync_path_missing"


def test_a_markdown_project_can_be_read_into_the_database_under_its_id():
    source = Source(project="P", path="docs", backend="markdown", id="abc", sync_path=None)

    database, markdown = sync_pair(source, SyncDirection.FROM_MD)

    assert markdown == source
    assert (database.backend, database.path, database.sync_path, database.id, database.project) == (
        "database", "", None, "abc", "P")


def test_a_markdown_project_without_a_database_mirror_cannot_be_written_anywhere():
    with pytest.raises(SyncSameBackendError) as error:
        sync_pair(Source(project="P", path="docs", backend="markdown", id="abc"), SyncDirection.TO_MD)
    assert error.value.code == "sync_same_backend"


def test_a_markdown_project_with_a_database_mirror_syncs_in_both_directions():
    source = Source(project="P", path="docs", backend="markdown", id="abc", mirror_database=True)

    for direction in SyncDirection:
        database, markdown = sync_pair(source, direction)

        assert markdown == source
        assert (database.backend, database.path, database.id, database.project) == ("database", "", "abc", "P")


def test_the_switch_needs_a_sync_first():
    error = SyncRequiredError()

    assert (error.code, isinstance(error, ConflictError)) == ("sync_required", True)


# --- one entry: which side changed it (TASK-032) ---

STORED = EntryState(database="v0", markdown="v0")


@pytest.mark.parametrize("database, markdown, stored, change", [
    ("v0", "v0", STORED, Change.UNCHANGED),
    ("v1", "v0", STORED, Change.DATABASE_CHANGED),
    ("v0", "v1", STORED, Change.MARKDOWN_CHANGED),
    ("v1", "v2", STORED, Change.BOTH_CHANGED),
    ("v1", "v1", STORED, Change.UNCHANGED),  # both moved to the same content: nothing left to sync
    (None, "v0", STORED, Change.DATABASE_DELETED),
    (None, "v1", STORED, Change.DATABASE_DELETED),  # deleted on one side, changed on the other: still a conflict
    ("v0", None, STORED, Change.MARKDOWN_DELETED),
    (None, None, STORED, Change.BOTH_DELETED),
    ("v1", None, None, Change.DATABASE_NEW),
    (None, "v1", None, Change.MARKDOWN_NEW),
    ("v1", "v1", None, Change.UNCHANGED),
    ("v1", "v2", None, Change.BOTH_NEW),
])
def test_an_entry_is_classified_by_its_two_versions_and_the_stored_state(database, markdown, stored, change):
    assert classify_entry(database, markdown, stored) is change


def test_sides_that_differ_while_the_stored_state_matches_neither_are_a_conflict():
    odd = EntryState(database="a", markdown="b")  # the state itself says the two were different

    assert classify_entry("a", "b", odd) is Change.BOTH_CHANGED


def test_only_these_changes_are_conflicts():
    assert {c for c in Change if c.is_conflict} == {Change.BOTH_CHANGED, Change.BOTH_NEW, Change.DATABASE_DELETED,
                                                    Change.MARKDOWN_DELETED}


def _plan(database, markdown, database_docs=None, markdown_docs=None, states=None):
    return plan_sync(database, markdown, database_docs or {}, markdown_docs or {}, states or {})


def _stored(*items: Item, docs: dict | None = None) -> dict:
    states = {EntryKey("item", i.id): EntryState(i.version, i.version) for i in items}
    for (label, name), content in (docs or {}).items():
        v = content_version(content)
        states[EntryKey("document", label, name)] = EntryState(v, v)
    return states


def test_a_change_on_one_side_only_is_carried_to_the_other_whichever_side_it_is():
    """Scenario 1 of STORY-057: the file changes STORY-A, the database changes STORY-B; both survive."""
    a, b = item("STORY-A", "a"), item("STORY-B", "b")
    states = _stored(a, b)
    database = [a, dataclasses.replace(b, title="b in database")]
    markdown = [dataclasses.replace(a, title="a in file"), b]

    plan = _plan(database, markdown, states=states)

    assert [(e.label, e.origin) for e in plan.preview.changed] == [("STORY-A", Side.MARKDOWN),
                                                                    ("STORY-B", Side.DATABASE)]
    assert plan.preview.conflicts == () and plan.preview.created == ()


def test_an_entry_new_on_one_side_goes_to_the_other():
    plan = _plan([item("TASK-001")], [item("TASK-002")])

    assert [(e.label, e.origin) for e in plan.preview.created] == [("TASK-001", Side.DATABASE),
                                                                    ("TASK-002", Side.MARKDOWN)]
    assert plan.preview.conflicts == ()


def test_the_same_new_id_on_both_sides_with_different_content_is_a_conflict_that_shows_both_versions():
    """Scenario 2 of STORY-057: nothing is overwritten, both versions are offered for the decision."""
    plan = _plan([item("STORY-009", "from the database", goal="g1")], [item("STORY-009", "from the file", goal="g2")])

    [conflict] = plan.preview.conflicts
    assert (conflict.entry.label, conflict.reason) == ("STORY-009", Change.BOTH_NEW)
    assert dict(conflict.database.fields)["title"] == "from the database"  # type: ignore[union-attr]
    assert dict(conflict.markdown.fields)["goal"] == "g2"  # type: ignore[union-attr]
    assert plan.preview.created == () and plan.preview.changed == ()


def test_a_deleted_entry_is_a_conflict_with_the_surviving_version():
    kept = item("TASK-005", "still in the file")
    plan = _plan([], [kept], states=_stored(kept))

    [conflict] = plan.preview.conflicts
    assert conflict.reason is Change.DATABASE_DELETED and conflict.database is None
    assert dict(conflict.markdown.fields)["title"] == "still in the file"  # type: ignore[union-attr]


def test_equal_entries_are_unchanged_without_a_stored_state():
    plan = _plan([item("TASK-001")], [item("TASK-001")])

    assert plan.preview.unchanged == 1 and plan.preview.created == plan.preview.changed == ()


def test_trashed_and_archived_state_counts_as_a_change():
    old = item("TASK-001")
    plan = _plan([dataclasses.replace(old, deleted="2026-01-01", location=Location.ARCHIVE)], [old],
                 states=_stored(old))

    assert [e.label for e in plan.preview.changed] == ["TASK-001"]


def test_documents_are_classified_by_content_like_items():
    both = [item("STORY-001", "s")]
    old = {("STORY-001", "STORY-001_spec.md"): "same", ("STORY-001", "STORY-001_notes.md"): "before"}
    states = _stored(*both, docs=old)
    database = {**old, ("STORY-001", "STORY-001_notes.md"): "after", ("STORY-001", "STORY-001_spec_ui.md"): "new"}

    plan = _plan(both, both, database, old, states)

    assert plan.preview.created_documents == (SyncEntry("document", "STORY-001", "s", "STORY-001_spec_ui.md",
                                                        Side.DATABASE),)
    assert plan.preview.changed_documents == (SyncEntry("document", "STORY-001", "s", "STORY-001_notes.md",
                                                        Side.DATABASE),)
    assert plan.preview.unchanged_documents == 1


def test_a_document_changed_on_both_sides_is_a_conflict_with_both_texts():
    both = [item("TASK-001", "t")]
    key = ("TASK-001", "TASK-001_notes.md")
    plan = _plan(both, both, {key: "database text"}, {key: "file text"}, _stored(*both, docs={key: "old"}))

    [conflict] = plan.preview.conflicts
    assert (conflict.entry.kind, conflict.entry.name, conflict.reason) == ("document", key[1], Change.BOTH_CHANGED)
    assert (conflict.database.text, conflict.markdown.text) == ("database text", "file text")  # type: ignore[union-attr]


def test_documents_of_a_new_item_travel_with_it_and_those_of_a_deleted_item_are_not_listed():
    new, gone = item("TASK-001", "new"), item("TASK-009", "gone")
    docs = {("TASK-001", "TASK-001_notes.md"): "x"}
    plan = _plan([new], [gone], docs, {("TASK-009", "TASK-009_notes.md"): "y"}, _stored(gone))

    assert plan.preview.created_documents == (SyncEntry("document", "TASK-001", "new", "TASK-001_notes.md",
                                                        Side.DATABASE),)
    assert [c.entry.kind for c in plan.preview.conflicts] == ["item"]


def test_skipped_entries_are_passed_through():
    skipped = (SyncEntry("document", "TASK-001", "t", "items/TASK-001/photo.png"),)

    assert plan_sync([], [], {}, {}, {}, skipped).preview.skipped == skipped


def test_the_token_changes_with_every_change_on_either_side_and_with_the_stored_state():
    a = item("TASK-001")
    base = _plan([a], [a], {("TASK-001", "a.md"): "x"}).preview.token

    assert _plan([a], [a], {("TASK-001", "a.md"): "x"}).preview.token == base
    assert _plan([a], [a], {("TASK-001", "a.md"): "y"}).preview.token != base
    assert _plan([a], [item("TASK-001", "other")], {("TASK-001", "a.md"): "x"}).preview.token != base
    assert _plan([a], [a], {("TASK-001", "a.md"): "x"}, {("TASK-001", "b.md"): "z"}).preview.token != base
    assert _plan([a], [a], {("TASK-001", "a.md"): "x"}, states=_stored(a)).preview.token != base


# --- what a run does (TASK-033) ---

def _decide(plan, *choices: tuple[str, Choice], direction=None):
    resolutions = [Resolution("item", label, None, choice) for label, choice in choices]
    return decide(plan, resolutions, direction)


def _moves(decisions):
    return sorted((t.key.label, t.to.value, "delete" if t.delete else "copy") for t in decisions.transfers)


def test_conflict_free_entries_are_carried_without_any_decision_and_conflicts_are_deferred():
    a, b = item("TASK-001", "a"), item("TASK-002", "b")
    plan = _plan([dataclasses.replace(a, title="a2"), b, item("TASK-003", "c1")], [a, b, item("TASK-003", "c2")],
                 states=_stored(a, b))

    decisions = _decide(plan)

    assert _moves(decisions) == [("TASK-001", "markdown", "copy")]
    assert [e.key.label for e in decisions.deferred] == ["TASK-003"]


@pytest.mark.parametrize("choice, moves", [
    (Choice.DATABASE, [("TASK-001", "markdown", "copy")]),
    (Choice.MARKDOWN, [("TASK-001", "database", "copy")]),
    (Choice.DEFER, []),
])
def test_a_conflict_takes_the_side_that_was_chosen(choice, moves):
    plan = _plan([item("TASK-001", "db")], [item("TASK-001", "md")])

    decisions = _decide(plan, ("TASK-001", choice))

    assert _moves(decisions) == moves
    assert [e.key.label for e in decisions.deferred] == ([] if moves else ["TASK-001"])


@pytest.mark.parametrize("missing_in, choice, moves", [
    ("database", Choice.DATABASE, [("TASK-005", "markdown", "delete")]),  # the database state holds: gone
    ("database", Choice.MARKDOWN, [("TASK-005", "database", "copy")]),  # the file state holds: restored
    ("markdown", Choice.DATABASE, [("TASK-005", "markdown", "copy")]),
    ("markdown", Choice.MARKDOWN, [("TASK-005", "database", "delete")]),
])
def test_a_deletion_is_decided_like_a_conflict_and_never_happens_without_a_decision(missing_in, choice, moves):
    entry = item("TASK-005")
    sides = ([], [entry]) if missing_in == "database" else ([entry], [])
    plan = _plan(*sides, states=_stored(entry))

    assert _moves(_decide(plan)) == []
    assert _moves(_decide(plan, ("TASK-005", choice))) == moves


def test_a_direction_only_restricts_which_sides_are_written():
    a, b = item("TASK-001", "a"), item("TASK-002", "b")
    plan = _plan([dataclasses.replace(a, title="a2"), b], [a, dataclasses.replace(b, title="b2")], states=_stored(a, b))

    assert _moves(_decide(plan, direction=SyncDirection.TO_MD)) == [("TASK-001", "markdown", "copy")]
    assert _moves(_decide(plan, direction=SyncDirection.FROM_MD)) == [("TASK-002", "database", "copy")]
    assert len(_decide(plan).transfers) == 2


def test_a_decision_that_writes_the_excluded_side_stays_deferred():
    plan = _plan([item("TASK-001", "db")], [item("TASK-001", "md")])

    decisions = _decide(plan, ("TASK-001", Choice.MARKDOWN), direction=SyncDirection.TO_MD)

    assert decisions.transfers == () and len(decisions.deferred) == 1


def test_a_decision_for_a_document_names_the_document():
    both = [item("TASK-001", "t")]
    key = ("TASK-001", "TASK-001_notes.md")
    plan = _plan(both, both, {key: "d"}, {key: "m"}, _stored(*both, docs={key: "o"}))

    wrong = decide(plan, [Resolution("item", "TASK-001", None, Choice.DATABASE)], None)
    right = decide(plan, [Resolution("document", key[0], key[1], Choice.MARKDOWN)], None)

    assert wrong.transfers == () and len(wrong.deferred) == 1
    assert [(t.key.name, t.to) for t in right.transfers] == [(key[1], Side.DATABASE)]


# --- the item lists after the transfers ---

def test_taken_items_replace_in_place_new_ones_follow_their_predecessor_and_dropped_ones_go():
    own = [item("A", "own a"), item("B", "own b"), item("C", "own c")]
    other = [item("A", "other a"), item("N", "new"), item("B", "other b"), item("C", "other c"), item("Z", "last")]

    merged = merged_items(own, other, take={"A", "N", "Z"}, drop={"C"})

    assert [(i.id, i.title) for i in merged] == [("A", "other a"), ("N", "new"), ("B", "own b"), ("Z", "last")]


def test_a_new_item_without_a_predecessor_on_the_other_side_goes_to_the_front():
    merged = merged_items([item("B")], [item("A"), item("B")], take={"A"}, drop=set())

    assert [i.id for i in merged] == ["A", "B"]


def test_check_token_refuses_a_state_that_changed_since_the_preview():
    check_token("abc", "abc")
    with pytest.raises(SyncStaleError) as error:
        check_token("abc", "abd")
    assert error.value.code == "sync_stale"
    with pytest.raises(SyncStaleError):
        check_token(None, "abc")


def test_directions_are_the_api_values():
    assert {d.value for d in SyncDirection} == {"to_md", "from_md"}


def test_the_default_direction_goes_from_the_primary_source_to_the_mirror():
    database = Source(project="P", path="", backend="database", id="abc", sync_path="/md")
    markdown = Source(project="P", path="docs", backend="markdown", id="abc", mirror_database=True)

    assert default_direction(database) is SyncDirection.TO_MD
    assert default_direction(markdown) is SyncDirection.FROM_MD
    assert default_direction(dataclasses.replace(markdown, mirror_database=False)) is SyncDirection.FROM_MD


def test_a_failed_backup_refuses_the_switch_and_names_the_reason():
    error = BackupFailedError("disk full")

    assert (error.code, isinstance(error, ConflictError), error.details) == ("backup_failed", True,
                                                                             {"reason": "disk full"})
    assert "disk full" in error.message and "Nothing was changed" in error.message


def test_a_side_is_fingerprinted_by_its_items_and_documents_regardless_of_order():
    a, b = item("TASK-001", "A"), item("TASK-002", "B")
    docs = {("TASK-001", "notes.md"): "one", ("TASK-002", "notes.md"): "two"}

    same = fingerprint([a, b], docs)

    assert fingerprint([b, a], dict(reversed(list(docs.items())))) == same
    assert fingerprint([a, item("TASK-002", "B changed")], docs) != same
    assert fingerprint([a, b], {**docs, ("TASK-001", "notes.md"): "one, edited"}) != same
    assert fingerprint([a, b], {**docs, ("TASK-001", "spec.md"): "new"}) != same
    assert fingerprint([a], docs) != same


BASE = SyncBaseline(at="2026-09-30T10:00:00+02:00", primary="p0", mirror="m0")


@pytest.mark.parametrize("primary, mirror, state", [
    ("p0", "m0", SyncState.IN_SYNC),
    ("p0", "m1", SyncState.MIRROR_CHANGED),
    ("p1", "m0", SyncState.PRIMARY_CHANGED),
    ("p1", "m1", SyncState.BOTH_CHANGED),
    ("x", "x", SyncState.IN_SYNC),  # both moved to the same content: nothing left to sync
])
def test_the_state_follows_which_side_moved_since_the_last_sync(primary, mirror, state):
    assert classify(primary, mirror, BASE) is state


def test_without_a_last_sync_equal_sides_are_in_sync_and_different_ones_unknown():
    assert classify("x", "x", None) is SyncState.IN_SYNC
    assert classify("x", "y", None) is SyncState.UNKNOWN


def test_what_stayed_different_on_purpose_does_not_count_as_a_change():
    assert classify("p0", "m0", BASE) is SyncState.IN_SYNC  # kept entries make the sides differ for good


def test_primary_and_mirror_are_the_two_sides_of_a_project_with_a_mirror():
    database = Source(project="P", path="", backend="database", id="a", sync_path="/md")
    markdown = Source(project="P", path="/docs", id="b", mirror_database=True)

    primary, mirror = primary_and_mirror(database)  # type: ignore[misc]
    assert (primary.backend, mirror.backend, mirror.path) == ("database", "markdown", "/md")
    primary, mirror = primary_and_mirror(markdown)  # type: ignore[misc]
    assert (primary.backend, primary.path, mirror.backend) == ("markdown", "/docs", "database")
    assert primary_and_mirror(Source(project="P", path="/docs")) is None
    assert primary_and_mirror(Source(project="P", path="", backend="database")) is None

"""SyncService gegen Fakes seiner Ports: Datenbank im Speicher, Dateien im Speicher, einfaches Zeilenformat."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import pytest
from fakes import FixedClock
from in_memory_files import InMemoryFileStore
from sync_fakes import (
    FILE,
    BackupRecorder,
    EventRecorder,
    LineCodec,
    MemoryParticipant,
    MemoryProjects,
    MemoryStateStore,
    ScheduleRecorder,
    SequentialIds,
    TransactionRecorder,
)
from viewer.core.application.sync import Decision, MirrorBinding, MirrorConfig, SyncService
from viewer.core.domain.errors import InvalidInput
from viewer.core.domain.sync import DeletionNotConfirmed, MirrorFormatError, SyncPreviewStale

FOLDER = Path("/mirror")
P = "project-1"
U1, U2, U3 = (f"00000000-0000-0000-0000-00000000000{i}" for i in (1, 2, 3))


@dataclass
class Rig:
    service: SyncService
    db: MemoryParticipant
    files: InMemoryFileStore
    state: MemoryStateStore
    backups: BackupRecorder
    events: EventRecorder
    scheduler: ScheduleRecorder
    projects: MemoryProjects
    clock: FixedClock
    transactions: TransactionRecorder

    def text(self) -> str:
        return self.files.folders[str(FOLDER)][FILE].decode()

    def write(self, text: str) -> None:
        self.files.put(FOLDER, FILE, text)

    def sync(self, direction: str = "both", **kwargs):  # type: ignore[no-untyped-def]
        token = self.service.preview(P, direction).token  # type: ignore[arg-type]
        return self.service.execute(P, token, direction, **kwargs)  # type: ignore[arg-type]


@pytest.fixture
def rig() -> Rig:
    db, files, state = MemoryParticipant(), InMemoryFileStore(), MemoryStateStore()
    backups, events, scheduler = BackupRecorder(), EventRecorder(), ScheduleRecorder()
    projects, clock, transactions = MemoryProjects({P: MirrorConfig(FOLDER)}), FixedClock(), TransactionRecorder()
    files.make_folder(FOLDER)
    service = SyncService(
        lambda: [MirrorBinding("test", LineCodec(), db)],
        projects=projects,
        files=files,
        state=state,
        database=transactions,
        backups=backups,
        events=events,
        scheduler=scheduler,
        clock=clock,
        ids=SequentialIds(),
        auto_interval_seconds=30,
    )
    return Rig(service, db, files, state, backups, events, scheduler, projects, clock, transactions)


def line(label: str, uid: str, kind: str, title: str, parent: str = "", deps: str = "") -> str:
    return f"- {label} | {uid} | {kind} | {title} | parent={parent} | deps={deps}\n"


# --- Zustand und Vorschau ------------------------------------------------------------------------------------------


def test_equal_sides_are_in_sync_and_a_run_remembers_them(rig: Rig) -> None:
    rig.db.add(U1, "task", "Eins")
    rig.write("# Items\n\n" + line("TASK-001", U1, "task", "Eins"))
    assert rig.service.status(P).state == "in_sync"
    assert rig.state.hashes == {}  # status ändert nichts
    rig.sync()
    assert set(rig.state.hashes[P]) == {U1}
    assert rig.backups.reasons == []  # nichts in die Datenbank geschrieben


def test_status_does_not_change_any_data(rig: Rig) -> None:
    rig.db.add(U1, "task", "Nur in der DB")
    before = (dict(rig.files.folders[str(FOLDER)]), rig.state.load(P), list(rig.db.rows))
    status = rig.service.status(P)
    assert (status.state, status.to_files, status.to_database) == ("primary_changed", 1, 0)
    assert before == (dict(rig.files.folders[str(FOLDER)]), rig.state.load(P), list(rig.db.rows))
    assert rig.events.events == [] and rig.backups.reasons == []


def test_status_names_the_direction_of_pending_changes(rig: Rig) -> None:
    rig.write("# Items\n\n" + line("TASK-009", U2, "task", "Nur in der Datei"))
    assert rig.service.status(P).state == "mirror_changed"
    rig.db.add(U1, "task", "Nur in der DB")
    assert rig.service.status(P).state == "both_changed"


def test_unconfigured_project_is_paused(rig: Rig) -> None:
    status = rig.service.status("nirgendwo")
    assert (status.state, status.reason) == ("paused", "not_configured")


# --- Übertragen ------------------------------------------------------------------------------------------------------


def test_new_database_entry_is_written_to_the_files(rig: Rig) -> None:
    rig.db.add(U1, "task", "Aus der DB", parent=("EPIC-001",))
    result = rig.sync()
    assert (result.to_files, result.to_database, result.state) == (1, 0, "in_sync")
    assert line("TASK-001", U1, "task", "Aus der DB", parent="EPIC-001").strip() in rig.text()
    assert rig.state.hashes[P].keys() == {U1}


def test_changes_are_carried_in_the_direction_they_happened(rig: Rig) -> None:
    rig.db.add(U1, "task", "A alt")
    rig.db.add(U2, "task", "B alt")
    rig.write("# Items\n\n" + line("TASK-001", U1, "task", "A alt") + line("TASK-002", U2, "task", "B alt"))
    rig.sync()
    rig.db.rows[U1] = rig.db.add(U1, "task", "A neu", label="TASK-001")  # in der DB geändert
    rig.write(rig.text().replace("B alt", "B neu"))  # in der Datei geändert
    result = rig.sync()
    assert (result.to_files, result.to_database, result.state) == (1, 1, "in_sync")
    assert rig.db.rows[U2].fields["title"] == "B neu"
    assert "A neu" in rig.text() and "B neu" in rig.text()


def test_backup_with_reason_sync_is_made_before_the_database_is_written(rig: Rig) -> None:
    rig.write("# Items\n\n" + line("NEW-x", "", "task", "Neu"))
    rig.sync()
    assert rig.backups.reasons == ["sync"]
    assert rig.transactions.committed == 1


def test_no_backup_and_no_transaction_when_only_files_change(rig: Rig) -> None:
    rig.db.add(U1, "task", "Nur Datei")
    rig.sync()
    assert rig.backups.reasons == [] and rig.transactions.committed == 0


# --- Neue Einträge aus den Dateien -----------------------------------------------------------------------------------


def test_new_entry_gets_uid_and_label_and_is_written_back(rig: Rig) -> None:
    rig.db.add(U3, "story", "Eltern")  # STORY-001
    rig.write("# Items\n\n" + line("NEW-login", "", "task", "Login", parent="STORY-001"))
    result = rig.sync()
    uid = "00000000-0000-0000-0000-000000000001"  # erste vergebene uid der SequentialIds
    assert result.created == ["TASK-001"] and result.to_database == 1
    assert rig.db.rows[uid].label == "TASK-001" and rig.db.rows[uid].refs == {"parent": ("STORY-001",)}
    assert line("TASK-001", uid, "task", "Login", parent="STORY-001") in rig.text()
    assert "NEW-login" not in rig.text()
    assert rig.service.status(P).state == "in_sync"


def test_placeholder_references_in_other_entries_are_rewritten(rig: Rig) -> None:
    rig.write(
        "# Items\n\n"
        + line("NEW-eltern", "", "story", "Eltern")
        + line("NEW-kind", "", "task", "Kind", parent="NEW-eltern")
        + line("NEW-spaeter", "", "task", "Später", deps="NEW-kind,NEW-eltern")
    )
    result = rig.sync()
    assert sorted(result.created) == ["STORY-001", "TASK-001", "TASK-002"]
    by_title = {e.fields["title"]: e for e in rig.db.rows.values()}
    assert by_title["Kind"].refs == {"parent": ("STORY-001",)}
    assert by_title["Später"].refs == {"deps": ("TASK-001", "STORY-001")}
    assert "NEW-" not in rig.text()
    assert "parent=STORY-001" in rig.text() and "deps=TASK-001,STORY-001" in rig.text()


def test_existing_entry_pointing_to_a_placeholder_is_updated_and_rewritten(rig: Rig) -> None:
    rig.db.add(U1, "task", "Bestehend")
    rig.write("# Items\n\n" + line("TASK-001", U1, "task", "Bestehend"))
    rig.sync()
    rig.write(rig.text().rstrip().replace("parent= |", "parent=NEW-neu |") + "\n" + line("NEW-neu", "", "epic", "Neu"))
    rig.sync()
    assert rig.db.rows[U1].refs == {"parent": ("EPIC-001",)}
    assert "NEW-neu" not in rig.text() and "parent=EPIC-001" in rig.text()


def test_duplicate_placeholders_are_a_format_error(rig: Rig) -> None:
    rig.write("# Items\n\n" + line("NEW-x", "", "task", "A") + line("NEW-x", "", "task", "B"))
    status = rig.service.status(P)
    assert (status.state, status.reason) == ("paused", "duplicate_label")


def test_new_entries_are_not_imported_when_files_may_not_be_written(rig: Rig) -> None:
    rig.write("# Items\n\n" + line("NEW-x", "", "task", "Neu"))
    preview = rig.service.preview(P, "to_database")
    assert preview.transfers == [] and [t.key for t in preview.not_imported] == ["new:NEW-x"]
    rig.sync("to_database")
    assert rig.db.rows == {} and rig.backups.reasons == []


def test_old_label_in_a_reference_is_the_same_element(rig: Rig) -> None:
    rig.db.add(U1, "task", "Ziel", label="TASK-040")
    rig.db.history["STORY-012"] = "TASK-040"  # Typwechsel: STORY-012 → TASK-040
    rig.db.add(U2, "task", "Verweist", label="TASK-002", deps=("TASK-040",))
    rig.write(
        "# Items\n\n"
        + line("TASK-040", U1, "task", "Ziel")
        + line("TASK-002", U2, "task", "Verweist", deps="STORY-012")
    )
    assert rig.service.status(P).state == "in_sync"  # kein scheinbarer Konflikt wegen des alten Labels


# --- Richtung --------------------------------------------------------------------------------------------------------


def test_direction_to_files_leaves_file_changes_alone(rig: Rig) -> None:
    rig.db.add(U1, "task", "DB")
    rig.write("# Items\n\n" + line("TASK-009", U2, "task", "Datei"))
    result = rig.sync("to_files")
    assert (result.to_files, result.to_database) == (1, 0)
    assert U2 not in rig.db.rows and "DB" in rig.text()
    assert rig.service.preview(P).transfers[0].target == "database"


def test_direction_to_database_leaves_the_files_alone(rig: Rig) -> None:
    rig.db.add(U1, "task", "DB")
    rig.write("# Items\n\n" + line("TASK-009", U2, "task", "Datei"))
    before = rig.text()
    result = rig.sync("to_database")
    assert (result.to_files, result.to_database) == (0, 1)
    assert U2 in rig.db.rows and rig.text() == before


# --- Konflikte -------------------------------------------------------------------------------------------------------


def make_conflict(rig: Rig) -> None:
    rig.db.add(U1, "task", "alt")
    rig.write("# Items\n\n" + line("TASK-001", U1, "task", "alt"))
    rig.sync()
    rig.db.add(U1, "task", "von der DB", label="TASK-001")
    rig.write(rig.text().replace("alt", "von der Datei"))


def test_both_changed_is_a_conflict_and_nothing_is_overwritten(rig: Rig) -> None:
    make_conflict(rig)
    preview = rig.service.preview(P)
    assert preview.state == "conflicts" and [c.conflict for c in preview.conflicts] == ["both_changed"]
    assert preview.conflicts[0].database["fields"] == {"title": "von der DB"}  # type: ignore[index]
    assert preview.conflicts[0].files["fields"] == {"title": "von der Datei"}  # type: ignore[index]
    result = rig.service.execute(P, preview.token)
    assert result.state == "conflicts" and len(result.conflicts_left) == 1
    assert rig.db.rows[U1].fields["title"] == "von der DB" and "von der Datei" in rig.text()


def test_decision_database_wins(rig: Rig) -> None:
    make_conflict(rig)
    result = rig.sync(decisions=[Decision(U1, "database")])
    assert result.state == "in_sync" and "von der DB" in rig.text() and "von der Datei" not in rig.text()


def test_decision_files_wins(rig: Rig) -> None:
    make_conflict(rig)
    result = rig.sync(decisions=[Decision(U1, "files")])
    assert result.state == "in_sync" and rig.db.rows[U1].fields["title"] == "von der Datei"


def test_decision_defer_keeps_the_conflict_for_later(rig: Rig) -> None:
    make_conflict(rig)
    result = rig.sync(decisions=[Decision(U1, "defer")])
    assert result.state == "conflicts" and rig.service.status(P).conflicts == 1


def test_decision_for_something_that_is_no_conflict_is_rejected(rig: Rig) -> None:
    make_conflict(rig)
    token = rig.service.preview(P).token
    with pytest.raises(InvalidInput):
        rig.service.execute(P, token, decisions=[Decision("gibt-es-nicht", "files")])


def test_both_created_with_different_content_is_a_conflict(rig: Rig) -> None:
    rig.db.add(U1, "task", "DB")
    rig.write("# Items\n\n" + line("TASK-001", U1, "task", "Datei"))
    assert [c.conflict for c in rig.service.preview(P).conflicts] == ["both_created"]


def test_deleted_in_files_is_a_conflict_that_needs_confirmation_to_delete(rig: Rig) -> None:
    rig.db.add(U1, "task", "Eins")
    rig.write("# Items\n\n" + line("TASK-001", U1, "task", "Eins"))
    rig.sync()
    rig.write("# Items\n\n")
    assert [c.conflict for c in rig.service.preview(P).conflicts] == ["deleted_in_files"]
    token = rig.service.preview(P).token
    with pytest.raises(DeletionNotConfirmed):
        rig.service.execute(P, token, decisions=[Decision(U1, "files")])
    assert U1 in rig.db.rows
    rig.sync(decisions=[Decision(U1, "files")], delete_missing=True)
    assert U1 not in rig.db.rows and rig.service.status(P).state == "in_sync"


def test_deleted_in_files_can_be_restored_from_the_database(rig: Rig) -> None:
    rig.db.add(U1, "task", "Eins")
    rig.write("# Items\n\n" + line("TASK-001", U1, "task", "Eins"))
    rig.sync()
    rig.write("# Items\n\n")
    rig.sync(decisions=[Decision(U1, "database")])
    assert "TASK-001" in rig.text() and U1 in rig.db.rows


def test_deleted_in_database_can_delete_the_file_entry_or_bring_it_back(rig: Rig) -> None:
    for choice, flag in (("database", True), ("files", False)):
        rig2 = rig
        rig2.db.rows.clear()
        rig2.db.add(U1, "task", "Eins", label="TASK-001")  # dasselbe Label wie in der Datei: sonst zieht die Datei nach
        rig2.write("# Items\n\n" + line("TASK-001", U1, "task", "Eins"))
        rig2.state.hashes.clear()
        rig2.sync()
        del rig2.db.rows[U1]
        assert [c.conflict for c in rig2.service.preview(P).conflicts] == ["deleted_in_database"]
        rig2.sync(decisions=[Decision(U1, choice)], delete_missing=flag)  # type: ignore[arg-type]
        assert (U1 in rig2.db.rows) == (choice == "files")
        assert ("TASK-001" in rig2.text()) == (choice == "files")


def test_gone_on_both_sides_is_forgotten_without_conflict(rig: Rig) -> None:
    rig.db.add(U1, "task", "Eins")
    rig.write("# Items\n\n" + line("TASK-001", U1, "task", "Eins"))
    rig.sync()
    del rig.db.rows[U1]
    rig.write("# Items\n\n")
    rig.sync()
    assert rig.state.hashes[P] == {}


def test_a_conflict_carries_origin_time_and_a_recommendation(rig: Rig) -> None:
    make_conflict(rig)
    conflict = rig.service.preview(P).conflicts[0]
    assert (conflict.database_changed, conflict.files_changed) == (True, True)
    assert conflict.synced_at == rig.clock.now()
    assert (conflict.recommendation, conflict.reason) == ("none", "both_changed")


def test_a_file_deleted_in_the_files_with_an_unchanged_database_recommends_the_deletion(rig: Rig) -> None:
    rig.db.add(U1, "task", "Eins")
    rig.write("# Items\n\n" + line("TASK-001", U1, "task", "Eins"))
    rig.sync()
    rig.write("# Items\n\n")
    conflict = rig.service.preview(P).conflicts[0]
    assert conflict.conflict == "deleted_in_files"
    assert (conflict.database_changed, conflict.files_changed) == (False, None)
    assert (conflict.recommendation, conflict.reason) == ("files", "deleted_other_unchanged")


def test_a_renamed_entry_is_named_as_the_partner_of_the_conflict(rig: Rig) -> None:
    rig.db.add(U1, "task", "Eine längere Überschrift mit viel Text")
    rig.write("# Items\n\n" + line("TASK-001", U1, "task", "Eine längere Überschrift mit viel Text"))
    rig.sync()
    rig.write("# Items\n\n" + line("TASK-002", U2, "task", "Eine längere Überschrift mit viel Text!"))
    rig.db.add(U2, "task", "Eine längere Überschrift mit viel Text!", label="TASK-002")
    conflict = rig.service.preview(P).conflicts[0]
    assert conflict.renamed_to is not None and conflict.renamed_to.key == U2
    assert conflict.reason == "renamed" and conflict.recommendation == "files"


# --- Token -------------------------------------------------------------------------------------------------------


def test_execute_with_an_outdated_token_is_refused(rig: Rig) -> None:
    rig.db.add(U1, "task", "Eins")
    token = rig.service.preview(P).token
    rig.db.add(U2, "task", "Noch eins")
    with pytest.raises(SyncPreviewStale) as err:
        rig.service.execute(P, token)
    assert err.value.code == "sync_preview_stale" and U1 not in rig.files.folders[str(FOLDER)].get(FILE, b"").decode()


def test_token_is_stable_while_nothing_changes(rig: Rig) -> None:
    rig.db.add(U1, "task", "Eins")
    assert rig.service.preview(P).token == rig.service.preview(P).token


# --- Ordner und Formatfehler -----------------------------------------------------------------------------------------


def test_format_error_stops_with_file_and_line(rig: Rig) -> None:
    rig.write("# Items\n\n" + line("TASK-001", U1, "task", "ok") + "- kaputt | nur | drei\n")
    status = rig.service.status(P)
    assert (status.state, status.reason, status.files) == ("paused", "invalid_value", [FILE])
    with pytest.raises(MirrorFormatError) as err:
        rig.service.preview(P)
    assert err.value.details == {"file": FILE, "line": 4}


def test_missing_folder_merge_markers_and_git_lock_pause_the_project(rig: Rig) -> None:
    rig.write("# Items\n\n<<<<<<< HEAD\n- x\n=======\n- y\n>>>>>>> b\n")
    assert rig.service.status(P).reason == "merge_markers"
    rig.write("# Items\n\n")
    rig.files.add_git_lock(FOLDER)
    assert rig.service.status(P).reason == "git_operation"
    rig.files.git_locks.clear()
    del rig.files.folders[str(FOLDER)]
    assert rig.service.status(P).reason == "missing"


# --- Auto-Sync ---------------------------------------------------------------------------------------------------


def test_auto_carries_only_conflict_free_changes(rig: Rig) -> None:
    rig.db.add(U1, "task", "alt")
    rig.db.add(U2, "task", "zwei alt")
    rig.write("# Items\n\n" + line("TASK-001", U1, "task", "alt") + line("TASK-002", U2, "task", "zwei alt"))
    rig.sync()
    rig.db.add(U1, "task", "DB", label="TASK-001")  # Konflikt: beide Seiten ändern TASK-001
    rig.db.add(U2, "task", "zwei neu", label="TASK-002")  # nur DB geändert
    rig.write(rig.text().replace("alt |", "Datei |", 1))
    status = rig.service.auto(P)
    assert status.state == "conflicts" and status.conflicts == 1
    assert "zwei neu" in rig.text() and "Datei" in rig.text() and rig.db.rows[U1].fields["title"] == "DB"


def test_auto_never_deletes(rig: Rig) -> None:
    rig.db.add(U1, "task", "Eins")
    rig.write("# Items\n\n" + line("TASK-001", U1, "task", "Eins"))
    rig.sync()
    rig.write("# Items\n\n")
    status = rig.service.auto(P)
    assert status.state == "conflicts" and U1 in rig.db.rows
    del rig.db.rows[U1]
    rig.write("# Items\n\n" + line("TASK-001", U1, "task", "Eins"))
    rig.service.auto(P)
    assert "TASK-001" in rig.text()


def test_auto_deletes_ephemeral_entries_gone_from_the_database(rig: Rig) -> None:
    rig.service = SyncService(
        lambda: [MirrorBinding("test", LineCodec(), rig.db, ephemeral=True)],
        projects=rig.projects,
        files=rig.files,
        state=rig.state,
        database=rig.transactions,
        backups=rig.backups,
        events=rig.events,
        scheduler=rig.scheduler,
        clock=rig.clock,
        ids=SequentialIds(),
    )
    rig.db.add(U1, "task", "Eins")
    rig.db.add(U2, "task", "Zwei")
    rig.write("# Items\n\n" + line("TASK-001", U1, "task", "Eins") + line("TASK-002", U2, "task", "Zwei"))
    rig.sync()
    del rig.db.rows[U1]
    status = rig.service.auto(P)
    assert status.state == "in_sync"
    assert "TASK-001" not in rig.text() and "TASK-002" in rig.text()
    rig.write("# Items\n\n")  # in den Dateien gelöscht: weiter ein Konflikt
    assert rig.service.auto(P).state == "conflicts" and U2 in rig.db.rows


# --- Endgültig gelöschte Einträge ------------------------------------------------------------------------------------


def _synced_pair(rig: Rig) -> None:
    rig.db.add(U1, "task", "Eins")
    rig.db.add(U2, "task", "Zwei")
    rig.write("# Items\n\n" + line("TASK-001", U1, "task", "Eins") + line("TASK-002", U2, "task", "Zwei"))
    rig.sync()


def test_purged_entry_is_deleted_in_the_unchanged_files_without_a_conflict(rig: Rig) -> None:
    _synced_pair(rig)
    del rig.db.rows[U1]
    rig.service.carry_purged([U1])
    assert "TASK-001" not in rig.text() and "TASK-002" in rig.text()
    assert U1 not in rig.state.hashes[P] and U2 in rig.state.hashes[P]
    assert rig.service.status(P).state == "in_sync"
    assert rig.backups.reasons == [] and rig.transactions.committed == 0


def test_purged_entry_changed_in_the_files_stays_a_conflict_and_is_kept(rig: Rig) -> None:
    _synced_pair(rig)
    del rig.db.rows[U1]
    rig.write(rig.text().replace("Eins", "Eins geändert"))
    rig.service.carry_purged([U1])
    assert "Eins geändert" in rig.text()
    assert [c.conflict for c in rig.service.preview(P).conflicts] == ["deleted_in_database"]


def test_carry_purged_leaves_other_open_differences_alone(rig: Rig) -> None:
    _synced_pair(rig)
    del rig.db.rows[U1]
    del rig.db.rows[U2]  # nicht endgültig gelöscht gemeldet: bleibt ein Konflikt
    rig.db.add("00000000-0000-0000-0000-000000000009", "task", "Neu in der DB")
    rig.service.carry_purged([U1])
    assert "TASK-001" not in rig.text() and "TASK-002" in rig.text() and "Neu in der DB" not in rig.text()
    assert [c.key for c in rig.service.preview(P).conflicts] == [U2]


def test_carry_purged_does_not_raise_when_the_folder_is_blocked(rig: Rig) -> None:
    _synced_pair(rig)
    del rig.db.rows[U1]
    rig.files.add_git_lock(FOLDER)
    rig.service.carry_purged([U1])
    rig.files.git_locks.clear()
    assert "TASK-001" in rig.text()
    assert [c.conflict for c in rig.service.preview(P).conflicts] == ["deleted_in_database"]


def test_carry_purged_skips_projects_without_a_mirror(rig: Rig) -> None:
    rig.projects.configs.clear()
    rig.service.carry_purged([U1])  # kein Fehler


def test_auto_imports_new_entries_and_backs_up_first(rig: Rig) -> None:
    rig.write("# Items\n\n" + line("NEW-x", "", "task", "Neu"))
    status = rig.service.auto(P)
    assert status.state == "in_sync" and rig.backups.reasons == ["sync"] and len(rig.db.rows) == 1


def test_auto_pauses_on_problems_and_changes_nothing(rig: Rig) -> None:
    rig.db.add(U1, "task", "DB")
    rig.write("# Items\n\n<<<<<<< a\n=======\n>>>>>>> b\n")
    status = rig.service.auto(P)
    assert (status.state, status.reason) == ("paused", "merge_markers")
    assert rig.backups.reasons == [] and "DB" not in rig.text()


def test_timer_runs_only_while_a_project_has_auto_sync_on(rig: Rig) -> None:
    rig.service.refresh_auto()
    assert rig.scheduler.appointments["core.sync"] is None
    rig.projects.configs[P] = MirrorConfig(FOLDER, auto_sync=True)
    rig.service.refresh_auto()
    appointment = rig.scheduler.appointments["core.sync"]
    assert appointment is not None
    at, callback = appointment
    assert at == rig.clock.now() + timedelta(seconds=30)
    rig.db.add(U1, "task", "Eins")
    callback()
    assert "TASK-001" in rig.text()
    assert rig.scheduler.appointments["core.sync"] is not None  # neu gesetzt
    rig.projects.configs[P] = MirrorConfig(FOLDER, auto_sync=False)
    rig.service.refresh_auto()
    assert rig.scheduler.appointments["core.sync"] is None


def test_a_failing_project_does_not_stop_the_tick(rig: Rig) -> None:
    rig.projects.configs["kaputt"] = MirrorConfig(Path("/gibt-es-nicht"), auto_sync=True)
    rig.projects.configs[P] = MirrorConfig(FOLDER, auto_sync=True)
    rig.db.add(U1, "task", "Eins")
    rig.service.refresh_auto()
    appointment = rig.scheduler.appointments["core.sync"]
    assert appointment is not None
    appointment[1]()
    assert "TASK-001" in rig.text()


# --- Ereignisse ----------------------------------------------------------------------------------------------------


def test_state_event_is_public_and_sent_after_a_run_and_on_changes_in_auto(rig: Rig) -> None:
    rig.db.add(U1, "task", "Eins")
    rig.sync()
    topics = [(e.topic, e.public, e.payload["state"]) for e in rig.events.events]
    assert topics == [("core.sync.state", True, "in_sync")]
    rig.service.auto(P)  # keine Änderung, kein neues Ereignis
    assert len(rig.events.events) == 1
    rig.db.add(U2, "task", "Zwei")
    rig.write(rig.text() + line("TASK-009", U2, "task", "anders"))
    rig.service.auto(P)  # Konflikt: Zustandswechsel
    assert rig.events.events[-1].payload["state"] == "conflicts"

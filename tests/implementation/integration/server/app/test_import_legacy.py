from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import legacy_db
import pytest
from fastapi.testclient import TestClient
from viewer.app.composition import create_app
from viewer.app.import_legacy import LegacyError, import_legacy, main
from viewer.app.import_legacy.report import Report
from viewer.core.domain.settings import Settings

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)


@pytest.fixture
def legacy(tmp_path: Path) -> Path:
    return legacy_db.build(tmp_path / "todo.db")


def run(legacy: Path, target: Path, **options: Any) -> Report:
    return import_legacy(legacy, target, now=NOW, backup_dir=target.parent / "backups", **options)


@pytest.fixture
def imported(legacy: Path, tmp_path: Path) -> Iterator[tuple[sqlite3.Connection, Report]]:
    target = tmp_path / "out" / "viewer.db"
    report = run(legacy, target)
    connection = sqlite3.connect(target)
    connection.row_factory = sqlite3.Row
    yield connection, report
    connection.close()


def rows(db: sqlite3.Connection, sql: str, *args: Any) -> list[dict[str, Any]]:
    return [dict(r) for r in db.execute(sql, args)]


def scalar(db: sqlite3.Connection, sql: str, *args: Any) -> Any:
    return db.execute(sql, args).fetchone()[0]


def test_projects_keep_their_ids_mirror_settings_and_order(imported: tuple[sqlite3.Connection, Report]) -> None:
    db, _ = imported

    projects = rows(db, "SELECT * FROM workspace_projects ORDER BY position")

    assert [(p["name"], p["position"]) for p in projects] == [("Allgemein", 0), ("Viewer", 1), ("Zwei", 2)]
    viewer, two = projects[1], projects[2]
    assert (viewer["uid"], viewer["mirror_folder"], viewer["mirror_enabled"], viewer["auto_sync"]) == (
        legacy_db.P_MAIN,
        "/spiegel/viewer",
        1,
        1,
    )
    assert (two["mirror_folder"], two["mirror_enabled"], two["auto_sync"]) == ("/spiegel/zwei", 0, 0)
    assert viewer["sync_direction"] == "both"


def test_items_keep_uid_and_label_and_priorities_are_mapped(imported: tuple[sqlite3.Connection, Report]) -> None:
    db, _ = imported

    items = {
        r["label"] + ("@2" if r["project_uid"] == legacy_db.P_TWO else ""): r
        for r in rows(
            db,
            "SELECT e.uid, e.label, e.project_uid, e.kind, e.deleted_at, e.created_at, i.* FROM backlog_items i "
            "JOIN workspace_elements e ON e.uid = i.uid",
        )
    }

    priorities = {label: row["priority"] for label, row in items.items()}
    assert priorities == {
        "EPIC-001": "Urgent",
        "STORY-001": "Urgent",
        "STORY-002": "Normal",
        "TASK-001": "Normal",
        "TASK-002": "Normal",
        "STORY-003": "Important",
        "STORY-004": "Prospective",
        "TASK-003": "Important",
        "STORY-005": "Important",
        "TASK-001@2": "Urgent",
    }
    story = items["STORY-001"]
    assert (story["uid"], story["kind"], story["parent_uid"], story["required_for_parent"]) == ("s1", "story", "e1", 1)
    assert (story["status"], story["summary"], story["created"]) == ("In progress", "Fertig bald", "2026-01-02")
    assert items["TASK-002"]["deleted_at"] == "2026-03-01T10:00:00+00:00"
    assert items["TASK-001"]["status"] == "Completed" and items["TASK-001"]["resolution"] == "Erledigt"
    assert items["TASK-003"]["parent_uid"] is None
    assert items["STORY-002"]["created_at"] == "2026-01-02T00:00:00+00:00"


def test_areas_dependencies_and_documents(imported: tuple[sqlite3.Connection, Report]) -> None:
    db, _ = imported

    areas = rows(db, "SELECT project_uid, name FROM backlog_areas ORDER BY name")
    assert areas == [
        {"project_uid": legacy_db.P_MAIN, "name": "Client"},
        {"project_uid": legacy_db.P_MAIN, "name": "Server"},
    ]
    assert (
        scalar(db, "SELECT a.name FROM backlog_items i JOIN backlog_areas a ON a.uid = i.area_uid WHERE i.uid='s2'")
        == "Client"
    )
    assert rows(db, "SELECT item_uid, depends_on_uid FROM backlog_dependencies") == [
        {"item_uid": "t1", "depends_on_uid": "s2"}
    ]
    documents = {(r["item_uid"], r["name"]): r for r in rows(db, "SELECT * FROM backlog_documents")}
    assert set(documents) == {("s1", "STORY-001_spec.md"), ("s3", "STORY-003_spec.md")}
    assert documents[("s1", "STORY-001_spec.md")]["kind"] == "spec"
    notes = rows(db, "SELECT item_uid, name FROM backlog_notes ORDER BY item_uid")
    assert notes == [
        {"item_uid": "s2", "name": "STORY-002_notes.md"},
        {"item_uid": "s3", "name": "STORY-003_notes.md"},
    ]


def test_extra_fields_become_one_dated_notes_entry(imported: tuple[sqlite3.Connection, Report]) -> None:
    db, _ = imported

    def entries(uid: str) -> list[dict[str, Any]]:
        return rows(db, "SELECT day, topic, body FROM backlog_notes_entries WHERE item_uid = ? ORDER BY position", uid)

    created, appended = entries("s2"), entries("s3")

    assert scalar(db, "SELECT preamble FROM backlog_notes WHERE item_uid='s2'") == "\n"
    assert [(e["day"], e["topic"]) for e in created] == [("2026-10-17", "Übernommene Zusatzfelder")]
    assert "- Implementation: Erste Zeile Zweite Zeile\n- Context: Kontext\n" in created[0]["body"]
    assert (appended[-1]["day"], appended[-1]["topic"]) == ("2026-10-17", "Übernommene Zusatzfelder")
    assert "- Verification: Geprüft\n" in appended[-1]["body"]


def test_topics_and_notes_keep_their_state(imported: tuple[sqlite3.Connection, Report]) -> None:
    db, _ = imported

    topics = {
        r["label"]: r
        for r in rows(
            db, "SELECT e.label, e.deleted_at, t.* FROM notes_topics t JOIN workspace_elements e ON e.uid = t.uid"
        )
    }
    assert (topics["TOPIC-002"]["parent_uid"], topics["TOPIC-002"]["due_at"]) == ("tp1", "2026-11-30T00:00:00+00:00")
    assert topics["TOPIC-003"]["deleted_at"] == "2026-03-02T10:00:00+00:00"
    notes = {
        r["label"] + ("@2" if r["project_uid"] == legacy_db.P_TWO else ""): r
        for r in rows(
            db,
            "SELECT e.label, e.project_uid, e.deleted_at, e.title, n.* FROM notes_notes n "
            "JOIN workspace_elements e ON e.uid = n.uid",
        )
    }
    assert (notes["NOTE-001"]["topic_uid"], notes["NOTE-001"]["body"]) == ("tp1", "Langtext")
    assert (notes["NOTE-002"]["status"], notes["NOTE-003"]["status"], notes["NOTE-003"]["archived"]) == (
        "snoozed",
        "done",
        1,
    )
    assert notes["NOTE-004"]["trigger_mode"] == "all" and notes["NOTE-006"]["deleted_at"] is not None
    assert notes["NOTE-001"]["title"] == "Kurzfassung NOTE-001" and "NOTE-001@2" in notes
    assert rows(db, "SELECT note_uid, name FROM notes_documents") == [{"note_uid": "n1", "name": "NOTE-001_notes.md"}]


def test_links_triggers_and_time_triggers_as_alarms(imported: tuple[sqlite3.Connection, Report]) -> None:
    db, _ = imported

    links = {(r["from_uid"], r["to_uid"], r["role"]) for r in rows(db, "SELECT * FROM workspace_links")}
    assert links == {
        ("n4", "s1", "trigger"),
        ("n1", "s1", "reference"),
        ("n7", "s2", "reference"),
        ("n3", "s5", "origin"),
        ("n2", "n1", "reference"),
        ("n2", "tp1", "reference"),
    }
    triggers = {r["uid"]: r for r in rows(db, "SELECT * FROM notes_triggers")}
    assert sorted((t["note_uid"], t["kind"], t["target_uid"], t["status"]) for t in triggers.values()) == [
        ("n4", "event", "s1", "Completed"),
        ("n5", "topic_date", None, None),
    ]
    event = next(t for t in triggers.values() if t["kind"] == "event")
    assert (event["fired_at"], event["already_met"]) == ("2026-04-01T09:00:00+00:00", 1)
    assert scalar(db, "SELECT role FROM workspace_links WHERE uid = ?", event["link_uid"]) == "trigger"
    alarms = rows(
        db,
        "SELECT e.project_uid, e.label, t.element_uid AS target_uid, a.* FROM alarms_alarms a "
        "JOIN workspace_elements e ON e.uid = a.uid LEFT JOIN alarms_targets t ON t.alarm_uid = a.uid "
        "ORDER BY a.at DESC",
    )
    assert [(a["project_uid"], a["label"], a["target_uid"], a["status"], a["at"], a["text"]) for a in alarms] == [
        (legacy_db.P_MAIN, "ALARM-001", "n2", "Pending", "2030-01-01T09:00:00+00:00", "Kurzfassung NOTE-002"),
        (legacy_db.P_TWO, "ALARM-001", "n7", "Due", "2026-05-01T09:00:00+00:00", "Kurzfassung NOTE-001"),
    ]


def test_notices_and_counters(imported: tuple[sqlite3.Connection, Report]) -> None:
    db, _ = imported

    notices = rows(
        db, "SELECT side, subject_uid, source_uid, kind, decided_at, decision FROM notes_notices ORDER BY side"
    )
    assert notices == [
        {"side": "item", "subject_uid": "s2", "source_uid": "n3", "kind": "note_promoted",
         "decided_at": "2026-05-04T09:00:00+00:00", "decision": "acknowledge"},
        {"side": "note", "subject_uid": "n1", "source_uid": "s1", "kind": "item_completed", "decided_at": None,
         "decision": None},
    ]  # fmt: skip
    counters = {(r["project_uid"], r["prefix"]): r["last"] for r in rows(db, "SELECT * FROM workspace_label_counters")}
    assert counters[(legacy_db.P_MAIN, "NOTE")] == 9
    assert counters[(legacy_db.P_MAIN, "TOPIC")] == 5
    assert counters[(legacy_db.P_MAIN, "STORY")] == 5
    assert counters[(legacy_db.P_MAIN, "TASK")] == 3
    assert counters[(legacy_db.P_MAIN, "ALARM")] == 1
    assert counters[(legacy_db.P_TWO, "NOTE")] == 3 and counters[(legacy_db.P_TWO, "TASK")] == 1
    assert scalar(db, "SELECT COUNT(*) FROM workspace_label_history") == scalar(
        db, "SELECT COUNT(*) FROM workspace_elements"
    )


def test_the_report_names_numbers_per_type_and_every_deviation(imported: tuple[sqlite3.Connection, Report]) -> None:
    _, report = imported

    assert dict(report.counts) == {
        "Projekte": 2,
        "Bereiche": 2,
        "Items Epic": 1,
        "Items Story": 5,
        "Items Task": 4,
        "Abhängigkeiten": 1,
        "Dokumente der Items": 4,
        "Einträge „Übernommene Zusatzfelder“": 2,
        "Zusatzfelder": 3,
        "Topics": 3,
        "Notes": 7,
        "Dokumente der Notes": 1,
        "Verknüpfungen": 6,
        "Auslöser Ereignis": 1,
        "Auslöser Topic-Termin": 1,
        "Wecker aus Zeit-Auslösern": 2,
        "Hinweise": 2,
    }
    text = "\n".join(report.deviations)
    for expected in (
        "Projekt 'Allgemein' wird das eingebaute Projekt",
        "STORY-002: Priorität '' → Normal",
        "STORY-001: Priorität 'dringend' → Urgent",
        "TASK-003: der Parent missing fehlt",
        "Abhängigkeit t1 → gone",
        "Dokument STORY-001_spec.md von STORY-001 steht nicht in der Namensliste",
        "Dokument STORY-003_spec_ui.md von STORY-003 ist gelistet, hat aber keinen Inhalt",
        "Verknüpfung 5 → p-main:STORY-999 hat kein Ziel",
        "Verknüpfung 8 gibt es schon",
        "Auslöser 5 von NOTE-004 hat kein Ziel",
        "Dokument NOTE-099_notes.md: die Note gone gibt es nicht",
        "Hinweis 3 (Projekt nicht erreichbar) entfällt",
        "Zähler 'weird'",
    ):
        assert expected in text, expected
    rendered = report.render(dry_run=False)
    assert "Items Story" in rendered and f"Abweichungen: {len(report.deviations)}" in rendered


def dump(path: Path) -> dict[str, list[tuple[Any, ...]]]:
    connection = sqlite3.connect(path)
    try:
        builtin = connection.execute("SELECT uid FROM workspace_projects WHERE position = 0").fetchone()[0]
        names = [
            r[0]
            for r in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'core_%'"
            )
        ]
        return {
            name: sorted(
                (
                    tuple("BUILTIN" if v == builtin else v for v in row)
                    for row in connection.execute(f"SELECT * FROM {name}")
                    if not (
                        name == "workspace_projects" and row[0] == builtin
                    )  # sein Zeitstempel ist der der Migration
                ),
                key=repr,
            )
            for name in sorted(names)
        }
    finally:
        connection.close()


def test_a_second_run_on_a_fresh_database_gives_the_same_result(legacy: Path, tmp_path: Path) -> None:
    first, second = tmp_path / "a" / "viewer.db", tmp_path / "b" / "viewer.db"

    report_one, report_two = run(legacy, first), run(legacy, second)

    one, two = dump(first), dump(second)
    assert one["backlog_items"] and one == two
    assert report_one.render(dry_run=False) == report_two.render(dry_run=False)


def test_a_dry_run_reports_the_same_and_changes_nothing(legacy: Path, tmp_path: Path) -> None:
    target = tmp_path / "out" / "viewer.db"
    legacy_bytes = legacy.read_bytes()

    dry = run(legacy, target, dry_run=True)

    assert not target.exists() and not (target.parent / "backups").exists()
    assert legacy.read_bytes() == legacy_bytes
    assert dry.render(dry_run=False) == run(legacy, target).render(dry_run=False)


def test_an_existing_empty_target_is_backed_up_first(legacy: Path, tmp_path: Path) -> None:
    target = tmp_path / "out" / "viewer.db"
    run(legacy_db.build(tmp_path / "leer.db", items=[], topics=[], notes=[], projects=[]), target)

    other = legacy_db.build(tmp_path / "zweite.db")
    sqlite3.connect(target).close()  # die Datei besteht schon und hat nur das eingebaute Projekt
    with sqlite3.connect(target) as connection:
        connection.execute("DELETE FROM workspace_projects WHERE position > 0")
    run(other, target)

    backups = list((target.parent / "backups").glob("viewer-*-import.db"))
    assert len(backups) == 1


def test_the_target_must_be_empty(legacy: Path, tmp_path: Path) -> None:
    target = tmp_path / "out" / "viewer.db"
    run(legacy, target)

    with pytest.raises(LegacyError, match="nicht leer"):
        run(legacy, target)


def test_a_markdown_primary_project_stops_the_import_and_is_named(tmp_path: Path) -> None:
    projects = legacy_db.content()["projects"]
    projects[0] = {**projects[0], "backend": "markdown"}
    legacy = legacy_db.build(tmp_path / "todo.db", projects=projects)

    with pytest.raises(LegacyError, match="Das Projekt 'Viewer' ist noch Markdown-primär"):
        run(legacy, tmp_path / "out" / "viewer.db")

    assert not (tmp_path / "out").exists()


def test_unknown_values_stop_the_import_with_the_whole_list(tmp_path: Path) -> None:
    content = legacy_db.content()
    items = [dict(i) for i in content["items"]]
    items[0]["priority"] = "Kritisch"
    items[1]["priority"] = "Sofort"
    items[2]["status"] = "Halb"
    legacy = legacy_db.build(tmp_path / "todo.db", items=items)

    with pytest.raises(LegacyError) as error:
        run(legacy, tmp_path / "out" / "viewer.db")

    text = str(error.value)
    assert "Unbekannte Prioritäten: EPIC-001 ('Kritisch'), STORY-001 ('Sofort')" in text
    assert "STORY-002: unbekannter Status 'Halb'" in text
    assert not (tmp_path / "out").exists()


def test_a_missing_or_incomplete_legacy_database_is_refused(tmp_path: Path) -> None:
    with pytest.raises(LegacyError, match="gibt es nicht"):
        run(tmp_path / "nope.db", tmp_path / "viewer.db")
    broken = tmp_path / "broken.db"
    with sqlite3.connect(broken) as connection:
        connection.execute("CREATE TABLE projects (id TEXT)")
    with pytest.raises(LegacyError, match="fehlen Tabellen"):
        run(broken, tmp_path / "viewer.db")


def test_the_imported_database_runs_in_the_viewer(legacy: Path, tmp_path: Path) -> None:
    target = tmp_path / "out" / "viewer.db"
    run(legacy, target)
    settings = Settings(db_path=str(target), backup_dir=str(tmp_path / "b"), log_dir=str(tmp_path / "l"))

    with TestClient(create_app(settings)) as client:
        items = client.get("/api/backlog/items").json()
        index = client.get("/api/notes/index").json()
        alarms = client.get("/api/alarms/alarms").json()
        item = client.get("/api/backlog/items/s2").json()
        note = client.get("/api/notes/notes/n4").json()
        trash = client.get("/api/workspace/trash").json()
        lines = client.get("/api/backlog/index", params={"projects": legacy_db.P_MAIN}).json()

    assert len(items) == 9  # ohne das gelöschte TASK-002
    assert {n["label"] for n in index["notes"] if n["project_uid"] == legacy_db.P_MAIN} >= {"NOTE-001", "NOTE-004"}
    assert len(alarms) == 2
    assert (item["label"], item["priority"], item["area"]) == ("STORY-002", "Normal", "Client")
    assert note["triggers"][0]["target"]["label"] == "STORY-001" and note["triggers"][0]["arrived"] is True
    assert {t["label"] for t in trash} == {"TASK-002", "TOPIC-003", "NOTE-006"}
    assert "STORY-001 | Story | In progress | Server | Titel STORY-001 | EPIC-001 | -" in lines["text"].splitlines()


def test_the_command_prints_the_report_and_writes_a_log(
    legacy: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target, logs = tmp_path / "out" / "viewer.db", tmp_path / "logs"
    arguments = ["--legacy-db", str(legacy), "--target", str(target), "--log-dir", str(logs)]
    arguments += ["--backup-dir", str(tmp_path / "bk")]

    assert main([*arguments, "--dry-run"]) == 0
    assert not target.exists() and not logs.exists()
    assert main(arguments) == 0

    printed = capsys.readouterr().out
    assert "Items Story" in printed and "Probelauf" in printed
    [log] = list(logs.glob("import-*.log"))
    assert "Items Story" in log.read_text(encoding="utf-8") and target.exists()
    assert main(arguments) == 1
    assert "nicht leer" in capsys.readouterr().err


def test_a_nameless_project_row_with_the_name_of_another_project_is_merged_into_it(tmp_path: Path) -> None:
    placeholder = {
        "id": "Viewer", "name": None, "backend": None, "path": None, "sync_path": None, "mirror_database": False,
        "mirror_disabled": False, "auto_sync": False, "position": None,
    }  # fmt: skip
    note = legacy_db._note("pn1", "NOTE-099", project_id="Viewer", summary="Alte Note")
    base = legacy_db.content()
    legacy = legacy_db.build(
        tmp_path / "todo.db",
        projects=[*base["projects"], placeholder],
        notes=[*base["notes"], note],
        note_counters=[
            *base["note_counters"],
            {"project_id": "Viewer", "kind": "note", "last": 99},
        ],
    )
    target = tmp_path / "out" / "viewer.db"

    run(legacy, target)

    db = sqlite3.connect(target)
    try:
        assert scalar(db, "SELECT COUNT(*) FROM workspace_projects WHERE name = 'Viewer'") == 1
        assert scalar(db, "SELECT project_uid FROM workspace_elements WHERE label = 'NOTE-099'") == legacy_db.P_MAIN
        counter = "SELECT last FROM workspace_label_counters WHERE project_uid = ? AND prefix = 'NOTE'"
        assert scalar(db, counter, legacy_db.P_MAIN) >= 99
    finally:
        db.close()

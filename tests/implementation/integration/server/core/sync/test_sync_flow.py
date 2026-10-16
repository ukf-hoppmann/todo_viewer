"""Sync mit echter SQLite-Datei, echtem Ordner und dem Test-Plugin, über HTTP wie im Betrieb."""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest
from fakes import FixedClock
from mirror_plugin.plugin import MIRROR_PLUGIN, MirrorTestServices
from starlette.testclient import TestClient
from sync_fakes import FILE, MemoryProjects
from viewer.app.composition import create_app
from viewer.core.application.sync import MirrorConfig
from viewer.core.domain.events import Event
from viewer.core.domain.settings import Settings

P = "project-1"
U1, U2 = "00000000-0000-0000-0000-0000000000a1", "00000000-0000-0000-0000-0000000000a2"


class Env:
    def __init__(self, tmp_path: Path, settings: Settings) -> None:
        self.folder = tmp_path / "mirror"
        self.folder.mkdir()
        self.settings = settings
        self.projects = MemoryProjects({P: MirrorConfig(self.folder)})
        self.app = create_app(settings, plugins=[MIRROR_PLUGIN], clock=FixedClock(), mirror_projects=self.projects)
        self.events: list[Event] = []
        self.app.state.events.subscribe("core.sync.*", self.events.append)
        self.client = TestClient(self.app)
        self.backups = Path(settings.backup_dir)

    @property
    def services(self) -> MirrorTestServices:
        services = self.app.state.plugin_host.services("mirror-test")
        assert isinstance(services, MirrorTestServices)
        return services

    @property
    def text(self) -> str:
        return (self.folder / FILE).read_text(encoding="utf-8")

    def write(self, text: str) -> None:
        (self.folder / FILE).write_text(text, encoding="utf-8")

    def sql(self, query: str) -> list[tuple[object, ...]]:
        conn = sqlite3.connect(self.settings.db_path)
        try:
            return conn.execute(query).fetchall()
        finally:
            conn.close()

    def sync(self, direction: str = "both", **body: object):  # type: ignore[no-untyped-def]
        preview = self.client.get(f"/api/core/sync/{P}/preview", params={"direction": direction})
        assert preview.status_code == 200, preview.text
        payload = {"token": preview.json()["token"], "direction": direction, **body}
        return self.client.post(f"/api/core/sync/{P}/execute", json=payload)


@pytest.fixture
def env(tmp_path: Path, settings: Settings) -> Iterator[Env]:
    environment = Env(tmp_path, replace(settings, auto_sync_interval_seconds=0.05))
    with environment.client:
        yield environment


def test_database_entries_reach_the_files_and_the_state_is_remembered(env: Env) -> None:
    label = env.services.seed(P, "story", "Aus der DB", U1)
    assert env.client.get(f"/api/core/sync/{P}/status").json()["state"] == "primary_changed"
    preview = env.client.get(f"/api/core/sync/{P}/preview").json()
    assert [(t["target"], t["action"], t["label"]) for t in preview["transfers"]] == [("files", "create", label)]
    result = env.sync()
    assert result.status_code == 200 and result.json()["state"] == "in_sync" and result.json()["to_files"] == 1
    assert f"- {label} | {U1} | story | Aus der DB | parent= | deps=" in env.text
    assert [row[0] for row in env.sql("SELECT uid FROM core_sync_state")] == [U1]
    assert env.client.get(f"/api/core/sync/{P}/status").json() == {
        "project": P, "state": "in_sync", "to_database": 0, "to_files": 0, "conflicts": 0, "reason": None, "files": []
    }  # fmt: skip
    assert [e.payload["state"] for e in env.events] == ["in_sync"]
    assert not env.backups.exists() or not list(env.backups.glob("*-sync.db"))  # nur Dateien geschrieben


def test_new_entries_from_the_files_get_uid_label_and_references_in_the_database(env: Env) -> None:
    parent_label = env.services.seed(P, "epic", "Eltern", U1)
    env.sync()
    env.write(
        env.text
        + f"- NEW-a |  | story | Neue Story | parent={parent_label} | deps=\n"
        + "- NEW-b |  | task | Neuer Task | parent=NEW-a | deps=\n"
    )
    result = env.sync()
    assert result.status_code == 200, result.text
    assert sorted(result.json()["created"]) == ["STORY-001", "TASK-001"]
    titles = env.services.titles(P)
    assert titles == {"EPIC-001": "Eltern", "STORY-001": "Neue Story", "TASK-001": "Neuer Task"}
    refs = env.sql(
        "SELECT a.label, f.field, t.label FROM mirror_test_refs f JOIN mirror_test_entries a ON a.uid = f.uid "
        "JOIN mirror_test_entries t ON t.uid = f.target_uid ORDER BY a.label"
    )
    assert refs == [("STORY-001", "parent", "EPIC-001"), ("TASK-001", "parent", "STORY-001")]
    assert "NEW-" not in env.text and "parent=STORY-001" in env.text
    assert env.client.get(f"/api/core/sync/{P}/status").json()["state"] == "in_sync"
    assert len(list(env.backups.glob("viewer-*-sync.db"))) == 1  # die Datenbank wurde vorher gesichert


def test_backup_made_by_sync_holds_the_state_before_the_import(env: Env) -> None:
    env.services.seed(P, "epic", "Alt", U1)
    env.sync()
    env.write(env.text + "- NEW-a |  | task | Neu | parent= | deps=\n")
    env.sync()
    (backup,) = env.backups.glob("viewer-*-sync.db")
    conn = sqlite3.connect(backup)
    try:
        assert conn.execute("SELECT count(*) FROM mirror_test_entries").fetchone() == (1,)
    finally:
        conn.close()
    assert env.sql("SELECT count(*) FROM mirror_test_entries") == [(2,)]


def test_conflict_is_listed_and_decided_over_http(env: Env) -> None:
    env.services.seed(P, "task", "alt", U1)
    env.sync()
    env.write(env.text.replace("alt", "Datei"))
    conn = sqlite3.connect(env.settings.db_path)
    conn.execute("UPDATE mirror_test_entries SET title = 'DB'")
    conn.commit()
    conn.close()
    preview = env.client.get(f"/api/core/sync/{P}/preview").json()
    assert preview["state"] == "conflicts" and preview["conflicts"][0]["conflict"] == "both_changed"
    assert env.sync().json()["conflicts_left"][0]["key"] == U1
    assert "Datei" in env.text and env.services.titles(P) == {"TASK-001": "DB"}
    env.sync(decisions=[{"uid": U1, "choice": "files"}])
    assert env.services.titles(P) == {"TASK-001": "Datei"}


def test_deletion_needs_decision_and_confirmation(env: Env) -> None:
    env.services.seed(P, "task", "Eins", U1)
    env.sync()
    env.write("# Items\n\n")
    refused = env.sync(decisions=[{"uid": U1, "choice": "files"}])
    assert refused.status_code == 422 and refused.json()["code"] == "deletion_not_confirmed"
    assert env.services.titles(P) == {"TASK-001": "Eins"}
    done = env.sync(decisions=[{"uid": U1, "choice": "files"}], delete_missing=True)
    assert done.status_code == 200 and env.services.titles(P) == {}


def test_outdated_token_is_refused_with_409(env: Env) -> None:
    env.services.seed(P, "task", "Eins", U1)
    token = env.client.get(f"/api/core/sync/{P}/preview").json()["token"]
    env.services.seed(P, "task", "Zwei", U2)
    r = env.client.post(f"/api/core/sync/{P}/execute", json={"token": token})
    assert r.status_code == 409 and r.json()["code"] == "sync_preview_stale"
    assert not (env.folder / FILE).exists()


def test_format_error_names_file_and_line_and_changes_nothing(env: Env) -> None:
    env.services.seed(P, "task", "Eins", U1)
    env.write("# Items\n\n- zu | kurz\n")
    status = env.client.get(f"/api/core/sync/{P}/status").json()
    assert (status["state"], status["reason"], status["files"]) == ("paused", "invalid_value", [FILE])
    r = env.client.get(f"/api/core/sync/{P}/preview")
    assert r.status_code == 422
    assert (r.json()["code"], r.json()["details"]) == ("invalid_value", {"file": FILE, "line": 3})
    assert env.text == "# Items\n\n- zu | kurz\n"


def test_blocked_folder_and_missing_configuration(env: Env) -> None:
    env.write("# Items\n\n<<<<<<< HEAD\na\n=======\nb\n>>>>>>> x\n")
    assert env.client.get(f"/api/core/sync/{P}/status").json()["reason"] == "merge_markers"
    r = env.client.get(f"/api/core/sync/{P}/preview")
    assert r.status_code == 409 and r.json()["code"] == "mirror_blocked"
    unknown = env.client.get("/api/core/sync/ohne-ordner/status").json()
    assert (unknown["state"], unknown["reason"]) == ("paused", "not_configured")
    assert env.client.get("/api/core/sync/ohne-ordner/preview").status_code == 404


def test_database_write_is_atomic_when_one_entry_fails(env: Env) -> None:
    env.services.seed(P, "epic", "Alt", U1)
    env.sync()
    before = env.text
    env.write(
        before
        + "- NEW-ok |  | task | Gut | parent= | deps=\n"
        + "- NEW-bad |  | task | Schlecht | parent=GIBT-ES-NICHT | deps=\n"
    )
    r = env.sync()
    assert r.status_code == 400 or r.status_code == 422
    assert r.json()["code"] == "invalid_input"
    assert env.services.titles(P) == {"EPIC-001": "Alt"}  # nichts Halbes in der Datenbank
    assert env.sql("SELECT count(*) FROM mirror_test_counters WHERE n > 1") == [(0,)]  # auch die Zähler zurückgerollt
    assert "NEW-ok" in env.text  # Dateien unberührt


def test_auto_sync_runs_by_itself_while_a_project_has_it_on(env: Env) -> None:
    env.projects.configs[P] = MirrorConfig(env.folder, auto_sync=True)
    env.app.state.sync.refresh_auto()
    env.services.seed(P, "task", "Automatisch", U1)
    deadline = time.time() + 5
    while time.time() < deadline and not (env.folder / FILE).exists():
        time.sleep(0.02)
    assert "Automatisch" in env.text
    env.projects.configs[P] = MirrorConfig(env.folder, auto_sync=False)
    env.app.state.sync.refresh_auto()  # kein Projekt mehr mit Auto-Sync: der Termin ist weg
    time.sleep(0.2)
    env.services.seed(P, "task", "Danach", U2)
    time.sleep(0.4)
    assert "Danach" not in env.text


def test_auto_sync_never_overwrites_a_conflict(env: Env) -> None:
    env.services.seed(P, "task", "alt", U1)
    env.sync()
    env.write(env.text.replace("alt", "Datei"))
    conn = sqlite3.connect(env.settings.db_path)
    conn.execute("UPDATE mirror_test_entries SET title = 'DB'")
    conn.commit()
    conn.close()
    status = env.app.state.sync.auto(P)
    assert status.state == "conflicts"
    assert "Datei" in env.text and env.services.titles(P) == {"TASK-001": "DB"}

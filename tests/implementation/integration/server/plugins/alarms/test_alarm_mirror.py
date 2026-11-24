"""Die Wecker im Spiegel und das ganze Beispielprojekt mit allen Plugins (echte Datenbank, Ordner, Codecs)."""

from __future__ import annotations

import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from mirror_files import FIXTURES
from workspace_env import Env


class Mirror:
    def __init__(self, env: Env, tmp_path: Path, fixture: str | None = None, name: str = "Beispiel") -> None:
        self.env = env
        self.folder = tmp_path / "mirror"
        if fixture:
            shutil.copytree(FIXTURES / fixture, self.folder)
        else:
            self.folder.mkdir()
        created = env.client.post(
            "/api/workspace/projects", json={"name": name, "mirror_folder": str(self.folder), "mirror_enabled": True}
        )
        assert created.status_code == 200, created.text
        self.project = str(created.json()["uid"])

    def sync(self, **body: Any) -> Any:
        preview = self.env.client.get(f"/api/core/sync/{self.project}/preview")
        if preview.status_code != 200:
            return preview
        payload = {"token": preview.json()["token"], "direction": "both", **body}
        return self.env.client.post(f"/api/core/sync/{self.project}/execute", json=payload)

    def status(self) -> dict[str, Any]:
        return self.env.client.get(f"/api/core/sync/{self.project}/status").json()  # type: ignore[no-any-return]

    def text(self, path: str) -> str:
        return (self.folder / path).read_text(encoding="utf-8")

    def alarms(self) -> dict[str, dict[str, Any]]:
        listed = self.env.client.get("/api/alarms/alarms", params={"projects": self.project}).json()
        return {a["label"]: a for a in listed}


def test_the_whole_example_project_imports_with_all_plugins_and_settles(full: Env, tmp_path: Path) -> None:
    mirror = Mirror(full, tmp_path, "valid")

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert mirror.status()["state"] == "in_sync"
    alarms = mirror.alarms()
    assert sorted(alarms) == ["ALARM-001", "ALARM-002", "ALARM-003"]
    assert {"ALARM-003", "MEMO-003", "TOPIC-003", "TASK-004"} <= set(result.json()["created"])
    again = mirror.sync()
    assert (again.json()["to_database"], again.json()["to_files"]) == (0, 0)


def test_alarms_are_imported_with_time_status_and_targets(full: Env, tmp_path: Path) -> None:
    mirror = Mirror(full, tmp_path, "valid")
    mirror.sync()
    alarms = mirror.alarms()

    first, second, new = alarms["ALARM-001"], alarms["ALARM-002"], alarms["ALARM-003"]
    assert (first["text"], first["status"], first["at"][:16], first["targets"][0]["label"]) == (
        "An die Story erinnern",
        "Pending",
        "2026-10-20T07:00",
        "STORY-001",
    )
    assert (second["status"], second["snoozed_until"][:16], second["targets"]) == ("Snoozed", "2026-10-17T07:00", [])
    assert (new["targets"], new["target_text"]) == (
        [],
        "Misc:MEMO-003",
    )  # ein Ziel, das es hier nicht gibt, bleibt Text
    assert full.app.state.scheduler.pending_at("alarms") == datetime.fromisoformat("2026-10-17T07:00:00+00:00")


def test_a_new_alarm_is_written_back_with_uid_label_and_created_and_keeps_its_foreign_target(
    full: Env, tmp_path: Path
) -> None:
    mirror = Mirror(full, tmp_path, "valid")
    mirror.sync()

    text = mirror.text("alarms.md")
    new = mirror.alarms()["ALARM-003"]

    assert "- `NEW-standup`" not in text
    assert f"- `ALARM-003` **Neuer Wecker aus der Cloud, Ziel in anderem Projekt**\n  - Uid: {new['uid']}.\n" in text
    assert "  - Target: `Misc:MEMO-003`.\n" in text and "  - Created: 20" in text


def test_an_alarm_set_in_the_database_appears_in_the_file_and_comes_back_unchanged(full: Env, tmp_path: Path) -> None:
    mirror = Mirror(full, tmp_path)
    item = full.client.post(
        "/api/backlog/items",
        json={
            "project": mirror.project,
            "type": "Task",
            "fields": {"title": "Ziel", "goal": "G", "completion_criteria": "K"},
        },
    ).json()
    created = full.client.post(
        "/api/alarms/alarms",
        json={
            "project": mirror.project,
            "fields": {"text": "Anrufen", "at": "2026-10-20T07:00:00Z", "target": item["uid"]},
        },
    ).json()

    assert mirror.sync().status_code == 200

    text = mirror.text("alarms.md")
    assert f"- `ALARM-001` **Anrufen**\n  - Uid: {created['uid']}.\n  - At: 2026-10-20T07:00:00Z.\n" in text
    assert f"  - Target: `{item['label']}`.\n  - Status: Pending.\n" in text
    again = mirror.sync()
    assert (again.json()["to_database"], again.json()["to_files"]) == (0, 0)


def test_a_series_alarm_travels_both_ways_and_stays_in_sync(full: Env, tmp_path: Path) -> None:
    mirror = Mirror(full, tmp_path)
    (mirror.folder / "alarms.md").write_text(
        "# Alarms\n\nFormat: Claude_Harness backlog format version 2.\n\n## Alarms\n\n"
        "- `NEW-montag` **Backlog sichten**\n  - At: 2026-10-16T09:00:00Z.\n  - Target: None.\n"
        "  - Repeat: Daily.\n  - Series from: 2026-10-16T09:00:00Z.\n  - Status: Due.\n",
        encoding="utf-8",
    )

    assert mirror.sync().status_code == 200

    series = mirror.alarms()["ALARM-001"]
    assert (series["repeat"], series["series_from"][:16], series["missed"]) == ("daily", "2026-10-16T09:00", 0)
    assert "  - Repeat: Daily.\n  - Series from: 2026-10-16T09:00:00Z.\n" in mirror.text("alarms.md")
    done = full.client.post(f"/api/alarms/alarms/{series['uid']}/finish", json={"version": series["version"]})
    assert done.status_code == 200, done.text
    assert mirror.sync().status_code == 200
    text = mirror.text("alarms.md")
    assert "  - At: 2026-10-17T09:00:00Z.\n" in text and "  - Series from: 2026-10-16T09:00:00Z.\n" in text
    assert "  - Status: Pending.\n" in text and "Done at" not in text
    again = mirror.sync()
    assert (again.json()["to_database"], again.json()["to_files"]) == (0, 0)


def test_a_purged_alarm_leaves_the_file_without_a_conflict(full: Env, tmp_path: Path) -> None:
    mirror = Mirror(full, tmp_path, "valid")
    mirror.sync()
    first = mirror.alarms()["ALARM-001"]
    done = full.client.post(f"/api/alarms/alarms/{first['uid']}/finish", json={"version": first["version"]})
    assert done.status_code == 200, done.text
    mirror.sync()
    assert "  - Done at: 2026-10-16T12:00:00Z.\n" in mirror.text("alarms.md")

    full.clock.advance(timedelta(hours=24))
    assert full.alarms.alarms.purge() == [first["uid"]]

    status = mirror.status()
    assert (status["state"], status["conflicts"]) == ("primary_changed", 0)
    assert mirror.sync().status_code == 200
    assert "ALARM-001" not in mirror.text("alarms.md") and "ALARM-002" in mirror.text("alarms.md")
    assert mirror.status()["conflicts"] == 0  # ALARM-002 hat sich inzwischen gemeldet, sonst ist nichts offen


def test_an_edit_in_the_file_reaches_the_database_and_moves_the_timer(full: Env, tmp_path: Path) -> None:
    mirror = Mirror(full, tmp_path, "valid")
    mirror.sync()
    path = mirror.folder / "alarms.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("At: 2026-10-20T07:00:00Z.", "At: 2026-10-16T13:00:00Z."),
        encoding="utf-8",
    )

    assert mirror.sync().status_code == 200

    assert mirror.alarms()["ALARM-001"]["at"].startswith("2026-10-16T13:00")
    assert full.app.state.scheduler.pending_at("alarms") == datetime.fromisoformat("2026-10-16T13:00:00+00:00")


def test_an_unknown_target_in_the_own_project_stops_the_sync_with_file_and_line(full: Env, tmp_path: Path) -> None:
    mirror = Mirror(full, tmp_path, "valid")
    path = mirror.folder / "alarms.md"
    path.write_text(path.read_text(encoding="utf-8").replace("`STORY-001`", "`STORY-099`"), encoding="utf-8")

    result = mirror.sync()

    body = result.json()
    assert result.status_code in (400, 409, 422), result.text
    assert (body["code"], body["details"]["file"], body["details"]["line"]) == ("unknown_reference", "alarms.md", 11)
    assert mirror.alarms() == {}


def test_a_format_error_in_alarms_md_stops_the_sync(full: Env, tmp_path: Path) -> None:
    mirror = Mirror(full, tmp_path, "valid")
    path = mirror.folder / "alarms.md"
    path.write_text(path.read_text(encoding="utf-8").replace("Status: Pending", "Status: Waiting", 1), encoding="utf-8")

    result = mirror.sync()

    assert result.status_code in (400, 409, 422) and result.json()["code"] == "invalid_value"
    assert mirror.alarms() == {}


def test_an_alarm_deleted_in_the_database_is_marked_in_its_file_and_stops_the_timer(full: Env, tmp_path: Path) -> None:
    mirror = Mirror(full, tmp_path, "valid")
    mirror.sync()
    second = mirror.alarms()["ALARM-001"]
    full.client.request("DELETE", f"/api/workspace/elements/{second['uid']}", params={"version": second["version"]})

    assert mirror.sync().status_code == 200

    assert "  - Deleted: 20" in mirror.text("alarms.md")
    assert "ALARM-001" not in mirror.alarms()

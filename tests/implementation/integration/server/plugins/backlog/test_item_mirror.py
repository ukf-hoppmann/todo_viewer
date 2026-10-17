"""Der Backlog im Spiegel: der Sync-Dienst mit echter SQLite-Datei, echtem Ordner und dem echten Codec."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from mirror_files import FIXTURES
from workspace_env import Env

BASE = {"title": "Ein Item", "area": "Server", "goal": "Ziel", "completion_criteria": "Kriterien"}


class Mirror:
    def __init__(self, env: Env, tmp_path: Path, fixture: str | None = None) -> None:
        self.env = env
        self.folder = tmp_path / "mirror"
        if fixture:
            shutil.copytree(FIXTURES / fixture, self.folder)
        else:
            self.folder.mkdir()
        created = env.client.post(
            "/api/workspace/projects",
            json={"name": "Spiegel", "mirror_folder": str(self.folder), "mirror_enabled": True},
        )
        assert created.status_code == 200, created.text
        self.project = str(created.json()["uid"])

    def sync(self, **body: Any) -> Any:
        preview = self.env.client.get(f"/api/core/sync/{self.project}/preview")
        if preview.status_code != 200:
            return preview  # ein Formatfehler zeigt sich schon in der Vorschau
        payload = {"token": preview.json()["token"], "direction": "both", **body}
        return self.env.client.post(f"/api/core/sync/{self.project}/execute", json=payload)

    def status(self) -> dict[str, Any]:
        return self.env.client.get(f"/api/core/sync/{self.project}/status").json()  # type: ignore[no-any-return]

    def text(self, path: str) -> str:
        return (self.folder / path).read_text(encoding="utf-8")

    def items(self) -> dict[str, dict[str, Any]]:
        listed = self.env.client.get("/api/backlog/items", params={"projects": self.project}).json()
        return {item["label"]: item for item in listed}

    def create(self, type_: str = "Task", **fields: Any) -> dict[str, Any]:
        body = {"project": self.project, "type": type_, "fields": {**BASE, **fields}}
        response = self.env.client.post("/api/backlog/items", json=body)
        assert response.status_code == 200, response.text
        return response.json()  # type: ignore[no-any-return]


def test_the_example_project_is_imported_into_an_empty_database_and_settles(backlog: Env, tmp_path: Path) -> None:
    mirror = Mirror(backlog, tmp_path, "valid")

    result = mirror.sync()

    assert result.status_code == 200, result.text
    items = mirror.items()
    assert sorted(items) == ["EPIC-001", "STORY-001", "STORY-002", "STORY-003", "TASK-001", "TASK-002", "TASK-004"]
    assert result.json()["created"] == ["TASK-004", "TASK-004_notes.md"]  # der neue Task und sein Dokument
    new = items["TASK-004"]
    assert (new["title"], new["parent_uid"] == items["STORY-001"]["uid"], new["status"]) == (
        "Neuer Task aus der Cloud",
        True,
        "Open",
    )
    assert items["TASK-002"]["dependencies"] == [new["uid"]]
    assert items["STORY-003"]["status"] == "Completed"
    assert mirror.status()["state"] == "in_sync"


def test_the_new_item_is_written_back_with_uid_label_and_created_and_its_documents_move(
    backlog: Env, tmp_path: Path
) -> None:
    mirror = Mirror(backlog, tmp_path, "valid")

    mirror.sync()

    todo = mirror.text("TODO.md")
    assert "NEW-login-dialog" not in todo.replace("`items/NEW-login-dialog/`", "")
    assert "- `TASK-004` **Neuer Task aus der Cloud**\n  - Uid: " in todo
    assert "  - Dependencies: `TASK-004`." in todo  # der Verweis von TASK-002
    assert (mirror.folder / "items" / "TASK-004" / "TASK-004_notes.md").is_file()
    assert not (mirror.folder / "items" / "NEW-login-dialog").exists()
    uid = mirror.items()["TASK-004"]["uid"]
    documents = backlog.client.get(f"/api/backlog/items/{uid}/documents").json()
    assert [d["name"] for d in documents] == ["TASK-004_notes.md"]
    again = mirror.sync()
    assert again.status_code == 200 and again.json()["to_files"] == 0  # nichts mehr zu tun


def test_documents_of_an_existing_item_are_imported(backlog: Env, tmp_path: Path) -> None:
    mirror = Mirror(backlog, tmp_path, "valid")
    mirror.sync()
    uid = mirror.items()["STORY-001"]["uid"]

    names = [d["name"] for d in backlog.client.get(f"/api/backlog/items/{uid}/documents").json()]
    notes = backlog.client.get(f"/api/backlog/items/{uid}/documents/STORY-001_notes.md").json()

    assert names == ["STORY-001_notes.md", "STORY-001_spec.md"]
    assert notes["content"].startswith("# STORY-001 — Pflicht-Story mit Dokumenten")


def test_items_made_in_the_viewer_arrive_in_the_files_in_the_right_places(backlog: Env, tmp_path: Path) -> None:
    mirror = Mirror(backlog, tmp_path)
    epic = mirror.create("Epic")
    story = mirror.create("Story", parent=epic["uid"], required_for_parent=True)
    backlog.client.put(
        f"/api/backlog/items/{story['uid']}",
        json={"version": 1, "fields": {"status": "Completed"}, "resolution": "Fertig."},
    )

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert "- `EPIC-001` **Ein Item**" in mirror.text("TODO.md") and "STORY-001" not in mirror.text("TODO.md")
    archive = mirror.text("archive.md")
    assert "- `STORY-001` **Ein Item**" in archive and "  - Resolution: Fertig." in archive
    assert mirror.status()["state"] == "in_sync"


def test_a_changed_field_in_the_viewer_changes_only_that_line_in_the_file(backlog: Env, tmp_path: Path) -> None:
    mirror = Mirror(backlog, tmp_path)
    item = mirror.create()
    mirror.sync()
    before = mirror.text("TODO.md").splitlines()

    backlog.client.put(f"/api/backlog/items/{item['uid']}", json={"version": 1, "fields": {"priority": "Urgent"}})
    mirror.sync()

    after = mirror.text("TODO.md").splitlines()
    assert [(a, b) for a, b in zip(before, after, strict=True) if a != b] == [
        ("  - Priority: Normal.", "  - Priority: Urgent.")
    ]


def test_an_edit_in_the_file_reaches_the_database_and_raises_the_version(backlog: Env, tmp_path: Path) -> None:
    mirror = Mirror(backlog, tmp_path)
    item = mirror.create()
    mirror.sync()
    path = mirror.folder / "TODO.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("  - Status: Open.", "  - Status: In progress."), encoding="utf-8"
    )

    result = mirror.sync()

    assert result.json()["to_database"] == 1
    current = backlog.client.get(f"/api/backlog/items/{item['uid']}").json()
    assert (current["status"], current["version"]) == ("In progress", 2)


def test_a_new_document_in_the_files_and_one_made_in_the_viewer_travel_both_ways(backlog: Env, tmp_path: Path) -> None:
    mirror = Mirror(backlog, tmp_path)
    item = mirror.create(summary="Kurz")
    mirror.sync()
    folder = mirror.folder / "items" / item["label"]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{item['label']}_spec_Teil.md").write_text("# Teil\n", encoding="utf-8")
    backlog.client.post(
        f"/api/backlog/items/{item['uid']}/notes",
        json={"topic": "Thema", "discussed": ["Ja"], "decided": [], "open": []},
    )

    mirror.sync()

    names = [d["name"] for d in backlog.client.get(f"/api/backlog/items/{item['uid']}/documents").json()]
    assert names == [f"{item['label']}_notes.md", f"{item['label']}_spec_Teil.md"]
    assert "## 2026-10-16 — Thema" in (folder / f"{item['label']}_notes.md").read_text(encoding="utf-8")


def test_a_type_change_renames_the_documents_in_the_files_and_the_references_follow(
    backlog: Env, tmp_path: Path
) -> None:
    mirror = Mirror(backlog, tmp_path)
    story = mirror.create("Story", summary="Kurz")
    other = mirror.create("Task", dependencies=[story["uid"]])
    backlog.client.post(
        f"/api/backlog/items/{story['uid']}/notes", json={"topic": "T", "discussed": ["x"], "decided": [], "open": []}
    )
    mirror.sync()
    assert (mirror.folder / "items" / "STORY-001" / "STORY-001_notes.md").is_file()

    retyped = backlog.client.post(
        f"/api/backlog/items/{story['uid']}/retype", json={"version": 1, "type": "Task"}
    ).json()
    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert result.json()["conflicts_left"] == []
    new_label = retyped["new_label"]
    assert new_label == "TASK-002"
    assert (mirror.folder / "items" / new_label / f"{new_label}_notes.md").is_file()
    assert not (mirror.folder / "items" / "STORY-001").exists()
    assert f"- `{new_label}` **Ein Item**" in mirror.text("TODO.md") and "- `STORY-001`" not in mirror.text("TODO.md")
    assert other["label"] == "TASK-001"
    # Der alte Verweis in der Datei der anderen Aufgabe löst weiter auf und zieht beim nächsten Schreiben nach.
    assert mirror.status()["state"] == "in_sync"
    again = mirror.sync().json()
    assert (again["to_files"], again["to_database"]) == (0, 0)


def test_an_old_label_in_the_files_still_finds_the_item_and_is_written_back_as_the_current_one(
    backlog: Env, tmp_path: Path
) -> None:
    mirror = Mirror(backlog, tmp_path)
    story = mirror.create("Story")
    other = mirror.create("Task", dependencies=[story["uid"]])
    mirror.sync()
    backlog.client.post(f"/api/backlog/items/{story['uid']}/retype", json={"version": 1, "type": "Task"})
    mirror.sync()  # die Datei zieht nach; der Verweis in der Datei des abhängigen Items bleibt vorerst beim alten Label
    path = mirror.folder / "TODO.md"
    assert "  - Dependencies: `STORY-001`." in mirror.text("TODO.md")
    # Eine LLM hat in der Zwischenzeit mit dem alten Label gearbeitet und ändert die Priorität des abhängigen Items.
    text = path.read_text(encoding="utf-8")
    start = text.index(f"- `{other['label']}`")
    path.write_text(
        text[:start] + text[start:].replace("  - Priority: Normal.", "  - Priority: Urgent.", 1), encoding="utf-8"
    )

    result = mirror.sync()

    assert result.status_code == 200, result.text
    todo = mirror.text("TODO.md")
    assert "- `STORY-001`" not in todo and "- `TASK-002` **Ein Item**" in todo
    assert "  - Dependencies: `TASK-002`." in todo  # der alte Verweis wurde beim Schreiben zum aktuellen Label
    assert backlog.client.get(f"/api/backlog/items/{other['uid']}").json()["priority"] == "Urgent"


def test_unknown_references_formats_and_rules_stop_the_sync_with_file_and_line_and_change_nothing(
    backlog: Env, tmp_path: Path
) -> None:
    expected = {
        "unknown_reference": ("TODO.md", 48),
        "format_version": ("TODO.md", 7),
        "invalid_value": ("TODO.md", 33),
        "rule_violation": ("TODO.md", 42),
    }
    for index, (code, (file, line)) in enumerate(expected.items()):
        sub = tmp_path / f"case{index}"
        sub.mkdir()
        mirror = Mirror(backlog, sub, f"invalid/{code}")
        mirror.env.client.get(f"/api/core/sync/{mirror.project}/preview")

        result = mirror.sync()

        body = result.json()
        assert result.status_code in (409, 422), (code, result.text)
        assert (body["code"], body["details"]["file"], body["details"]["line"]) == (code, file, line), code
        assert mirror.items() == {}, code
        backlog.client.request(
            "DELETE", f"/api/workspace/projects/{mirror.project}", params={"version": 1, "confirm": True}
        )


def test_an_item_that_disappears_from_the_files_is_a_conflict_and_goes_to_the_trash_only_when_confirmed(
    backlog: Env, tmp_path: Path
) -> None:
    mirror = Mirror(backlog, tmp_path)
    keep = mirror.create()
    gone = mirror.create()
    mirror.sync()
    path = mirror.folder / "TODO.md"
    text = path.read_text(encoding="utf-8")
    start = text.index(f"- `{gone['label']}`")
    path.write_text(text[:start].rstrip("\n") + "\n", encoding="utf-8")

    refused = mirror.sync(decisions=[{"uid": gone["uid"], "choice": "files"}])
    done = mirror.sync(decisions=[{"uid": gone["uid"], "choice": "files"}], delete_missing=True)

    assert refused.status_code == 422 and refused.json()["code"] == "deletion_not_confirmed"
    assert done.status_code == 200, done.text
    assert sorted(mirror.items()) == [keep["label"]]
    trash = backlog.client.get("/api/workspace/trash").json()
    assert [e["uid"] for e in trash] == [gone["uid"]]  # im Papierkorb, nicht endgültig gelöscht


def test_an_item_in_the_trash_is_written_to_the_archive_with_its_day_and_comes_back_from_there(
    backlog: Env, tmp_path: Path
) -> None:
    mirror = Mirror(backlog, tmp_path)
    item = mirror.create()
    mirror.sync()

    backlog.client.delete(f"/api/workspace/elements/{item['uid']}", params={"version": 1})
    mirror.sync()

    assert f"- `{item['label']}`" not in mirror.text("TODO.md")
    assert "  - Deleted: 2026-10-16." in mirror.text("archive.md")
    backlog.client.post("/api/workspace/trash/restore", json={"uids": [item["uid"]]})
    mirror.sync()
    assert f"- `{item['label']}`" in mirror.text("TODO.md") and "Deleted:" not in mirror.text("archive.md")


def test_the_status_names_the_time_of_the_last_sync(backlog: Env, tmp_path: Path) -> None:
    mirror = Mirror(backlog, tmp_path)
    mirror.create()
    assert mirror.status()["last_sync"] is None

    mirror.sync()

    assert mirror.status()["last_sync"].startswith("2026-10-16T12:00:00")

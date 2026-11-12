"""Die Memos im Spiegel: der Sync-Dienst mit echter SQLite-Datei, echtem Ordner und den echten Codecs."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from mirror_files import FIXTURES
from workspace_env import Env

NOTES = "/api/memos"


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

    def write(self, path: str, text: str) -> None:
        (self.folder / path).parent.mkdir(parents=True, exist_ok=True)
        (self.folder / path).write_text(text, encoding="utf-8")

    def index(self) -> dict[str, Any]:
        return self.env.client.get(f"{NOTES}/index", params={"projects": self.project}).json()  # type: ignore[no-any-return]

    def memos(self) -> dict[str, dict[str, Any]]:
        return {n["label"]: n for n in self.index()["memos"]}

    def topics(self) -> dict[str, dict[str, Any]]:
        return {t["label"]: t for t in self.index()["topics"]}

    def memo(self, label: str) -> dict[str, Any]:
        response = self.env.client.get(f"{NOTES}/memos/{label}", params={"project": self.project})
        assert response.status_code == 200, response.text
        return response.json()  # type: ignore[no-any-return]

    def create_memo(self, summary: str = "Aus der Datenbank", **fields: Any) -> dict[str, Any]:
        response = self.env.client.post(
            f"{NOTES}/memos", json={"project": self.project, "fields": {"summary": summary, **fields}}
        )
        assert response.status_code == 200, response.text
        return response.json()  # type: ignore[no-any-return]

    def create_item(self, **fields: Any) -> dict[str, Any]:
        base = {"title": "Ein Item", "area": "Server", "goal": "Ziel", "completion_criteria": "Kriterien"}
        response = self.env.client.post(
            "/api/backlog/items", json={"project": self.project, "type": "Task", "fields": {**base, **fields}}
        )
        assert response.status_code == 200, response.text
        return response.json()  # type: ignore[no-any-return]


def test_the_example_project_is_imported_with_memos_topics_links_and_triggers(memos: Env, tmp_path: Path) -> None:
    mirror = Mirror(memos, tmp_path, "valid")

    result = mirror.sync()

    assert result.status_code == 200, result.text
    assert sorted(mirror.topics()) == ["TOPIC-001", "TOPIC-002", "TOPIC-003"]
    assert sorted(mirror.memos()) == ["MEMO-001", "MEMO-003"]  # MEMO-002 liegt im Papierkorb
    assert {"TASK-004", "MEMO-003", "TOPIC-003"} <= set(result.json()["created"])
    topics = mirror.topics()
    assert topics["TOPIC-002"]["parent_uid"] == topics["TOPIC-001"]["uid"] and topics["TOPIC-002"]["archived"] is True
    assert topics["TOPIC-001"]["due_at"].startswith("2026-12-01")
    shown = mirror.memo("MEMO-001")
    assert (shown["status"], shown["stored_status"], shown["review_at"][:10]) == ("waiting", "waiting", "2026-11-07")
    assert shown["topic_uid"] == topics["TOPIC-001"]["uid"] and shown["body"].startswith("# Überschrift")
    assert shown["documents"] == ["MEMO-001_notes.md"]
    assert [(t["kind"], t["status"], t["arrived"]) for t in shown["triggers"]] == [
        ("event", "Completed", True),
        ("event", "Completed", False),
        ("topic_date", None, False),
    ]
    assert shown["triggers"][0]["already_met"] is True and shown["triggers"][0]["target"]["label"] == "STORY-003"
    assert mirror.status()["state"] == "in_sync"


def test_links_resolve_to_the_right_elements_including_new_ones(memos: Env, tmp_path: Path) -> None:
    mirror = Mirror(memos, tmp_path, "valid")
    mirror.sync()
    links = memos.client.get(f"/api/workspace/elements/{mirror.memo('MEMO-001')['uid']}/links").json()["outgoing"]

    assert sorted((entry["role"], entry["label"]) for entry in links) == [
        ("origin", "STORY-002"),
        ("reference", "MEMO-003"),
        ("reference", "STORY-001"),
        ("reference", "TOPIC-002"),
        ("trigger", "STORY-003"),
        ("trigger", "TASK-001"),
    ]
    new_links = memos.client.get(f"/api/workspace/elements/{mirror.memo('MEMO-003')['uid']}/links").json()["outgoing"]
    assert [(e["role"], e["label"]) for e in new_links] == [("reference", "TASK-004")]  # das neue Item derselben Runde


def test_new_memos_and_topics_are_written_back_with_uid_label_and_resolved_references(
    memos: Env, tmp_path: Path
) -> None:
    mirror = Mirror(memos, tmp_path, "valid")
    mirror.sync()

    assert not (mirror.folder / "memos" / "new-idee-export.md").exists()
    memo = mirror.memo("MEMO-003")
    text = mirror.text("memos/MEMO-003.md")
    assert text.startswith(
        f"# MEMO-003\nUid: {memo['uid']}\nSummary: In der Cloud angelegte Memo in einem neuen Topic\n"
    )
    assert "Topic: TOPIC-003\n" in text and "- reference Beispiel:TASK-004\n" in text
    topics = mirror.text("memos/topics.md")
    assert f"- TOPIC-003 | Ideen aus der Cloud | uid={mirror.topics()['TOPIC-003']['uid']}" in topics
    assert "- NEW |" not in topics
    assert "- reference memo:MEMO-003\n" in mirror.text("memos/MEMO-001.md")
    assert not (mirror.folder / "memos" / "counters.md").exists()


def test_the_second_sync_changes_nothing(memos: Env, tmp_path: Path) -> None:
    mirror = Mirror(memos, tmp_path, "valid")
    mirror.sync()
    before = {p.name: p.read_text(encoding="utf-8") for p in (mirror.folder / "memos").iterdir()}

    result = mirror.sync()

    assert result.status_code == 200 and (result.json()["to_database"], result.json()["to_files"]) == (0, 0)
    assert {p.name: p.read_text(encoding="utf-8") for p in (mirror.folder / "memos").iterdir()} == before


def test_a_memo_made_in_the_database_appears_as_a_file_and_comes_back_unchanged(memos: Env, tmp_path: Path) -> None:
    mirror = Mirror(memos, tmp_path)
    target = mirror.create_item()
    topic = memos.client.post(f"{NOTES}/topics", json={"project": mirror.project, "name": "Thema | eins"}).json()
    entry = mirror.create_memo("Mit allem", body="Ein Text\nüber zwei Zeilen", topic=topic["uid"])
    memos.client.post(
        "/api/workspace/links", json={"from_uid": entry["uid"], "to_uid": target["uid"], "role": "reference"}
    )
    memos.client.post(
        f"{NOTES}/memos/{entry['uid']}/triggers", json={"kind": "event", "target": target["uid"], "status": "Completed"}
    )
    memos.client.put(f"{NOTES}/memos/{entry['uid']}/documents/{entry['label']}_notes.md", json={"content": "# Doku\n"})

    assert mirror.sync().status_code == 200

    text = mirror.text(f"memos/{entry['label']}.md")
    assert f"Uid: {entry['uid']}\n" in text and "Topic: TOPIC-001\n" in text
    assert f"- event Beispiel:{target['label']} Completed\n" in text
    assert f"Links:\n- reference Beispiel:{target['label']}\n" in text
    assert text.endswith("\nEin Text\nüber zwei Zeilen\n")
    assert mirror.text(f"memos/{entry['label']}_notes.md") == "# Doku\n"
    assert "Thema \\| eins" in mirror.text("memos/topics.md")
    again = mirror.sync()
    assert (again.json()["to_database"], again.json()["to_files"]) == (0, 0)
    assert mirror.status()["state"] == "in_sync"


def test_an_edit_in_the_file_reaches_the_database_and_an_edit_in_the_database_the_file(
    memos: Env, tmp_path: Path
) -> None:
    mirror = Mirror(memos, tmp_path, "valid")
    mirror.sync()
    path = "memos/MEMO-001.md"
    mirror.write(
        path, mirror.text(path).replace("Status: waiting", "Status: snoozed").replace("Mode: all", "Mode: any")
    )

    assert mirror.sync().status_code == 200
    shown = mirror.memo("MEMO-001")
    assert (shown["stored_status"], shown["version"]) == ("snoozed", shown["version"])

    kept = memos.client.post(f"{NOTES}/memos/{shown['uid']}/keep", json={"version": shown["version"]})
    assert kept.status_code == 200
    assert mirror.sync().status_code == 200
    assert f"Review: {kept.json()['review_at'][:19]}" in mirror.text(path)


def test_a_file_that_removes_trigger_and_link_removes_them_in_the_database(memos: Env, tmp_path: Path) -> None:
    mirror = Mirror(memos, tmp_path, "valid")
    mirror.sync()
    text = mirror.text("memos/MEMO-001.md")
    start, end = text.index("Triggers:"), text.index("\n# Überschrift")
    mirror.write("memos/MEMO-001.md", text[:start] + text[end:])

    assert mirror.sync().status_code == 200

    shown = mirror.memo("MEMO-001")
    assert shown["triggers"] == []
    links = memos.client.get(f"/api/workspace/elements/{shown['uid']}/links").json()["outgoing"]
    assert links == []


def test_a_memo_deleted_in_the_database_is_marked_deleted_in_its_file(memos: Env, tmp_path: Path) -> None:
    mirror = Mirror(memos, tmp_path, "valid")
    mirror.sync()
    shown = mirror.memo("MEMO-003")
    memos.client.request("DELETE", f"/api/workspace/elements/{shown['uid']}", params={"version": shown["version"]})

    assert mirror.sync().status_code == 200

    assert "Deleted: 20" in mirror.text("memos/MEMO-003.md")
    assert "MEMO-003" not in mirror.memos()


def test_a_memo_that_disappears_from_the_files_is_a_conflict_and_goes_to_the_trash_only_when_confirmed(
    memos: Env, tmp_path: Path
) -> None:
    mirror = Mirror(memos, tmp_path, "valid")
    mirror.sync()
    shown = mirror.memo("MEMO-003")
    (mirror.folder / "memos" / "MEMO-003.md").unlink()

    refused = mirror.sync(decisions=[{"uid": shown["uid"], "choice": "files"}])
    done = mirror.sync(decisions=[{"uid": shown["uid"], "choice": "files"}], delete_missing=True)

    assert refused.status_code == 422 and refused.json()["code"] == "deletion_not_confirmed"
    assert done.status_code == 200, done.text
    assert "MEMO-003" not in mirror.memos()


def test_both_sides_changing_one_memo_is_a_conflict(memos: Env, tmp_path: Path) -> None:
    mirror = Mirror(memos, tmp_path, "valid")
    mirror.sync()
    shown = mirror.memo("MEMO-001")
    memos.client.put(
        f"{NOTES}/memos/{shown['uid']}", json={"version": shown["version"], "fields": {"summary": "Datenbank"}}
    )
    path = "memos/MEMO-001.md"
    mirror.write(path, mirror.text(path).replace("Summary: Memo mit", "Summary: Datei mit"))

    result = mirror.sync()

    assert result.status_code == 200 and [c["conflict"] for c in result.json()["conflicts_left"]] == ["both_changed"]
    assert mirror.memo("MEMO-001")["summary"] == "Datenbank"


def test_a_retyped_target_is_still_found_through_its_old_label_in_the_files(memos: Env, tmp_path: Path) -> None:
    mirror = Mirror(memos, tmp_path)
    target = mirror.create_item()
    story = mirror.create_item()
    entry = mirror.create_memo()
    memos.client.post(
        "/api/workspace/links", json={"from_uid": entry["uid"], "to_uid": target["uid"], "role": "reference"}
    )
    mirror.sync()
    assert f"- reference Beispiel:{target['label']}\n" in mirror.text(f"memos/{entry['label']}.md")
    memos.client.put(
        f"/api/backlog/items/{target['uid']}",
        json={"version": target["version"], "fields": {"parent": story["uid"]}, "resolution": None},
    )
    current = memos.client.get(f"/api/backlog/items/{target['uid']}").json()
    retyped = memos.client.post(
        f"/api/backlog/items/{target['uid']}/retype", json={"version": current["version"], "type": "Story"}
    )
    assert retyped.status_code == 200, retyped.text

    result = mirror.sync()

    # die Datei nennt weiter das alte Label, die Verknüpfung hängt an der uid: nichts ist zu tun, nichts ein Konflikt
    assert result.status_code == 200, result.text
    assert result.json()["conflicts_left"] == [] and mirror.status()["state"] == "in_sync"
    links = memos.client.get(f"/api/workspace/elements/{entry['uid']}/links").json()["outgoing"]
    assert [(e["role"], e["uid"]) for e in links] == [("reference", target["uid"])]


def _broken(memos: Env, tmp_path: Path, code: str) -> Any:
    mirror = Mirror(memos, tmp_path, f"invalid/{code}")
    return mirror, mirror.sync()


def test_format_errors_in_memos_stop_the_sync_with_file_and_line_and_change_nothing(memos: Env, tmp_path: Path) -> None:
    for index, code in enumerate(("file_label_mismatch", "unknown_trigger")):
        sub = tmp_path / f"case{index}"
        sub.mkdir()
        expected = json.loads((FIXTURES / "invalid" / code / "expected.json").read_text())
        mirror, result = _broken(memos, sub, code)
        body = result.json()
        assert result.status_code in (400, 409, 422), (code, result.text)
        assert (body["code"], body["details"]["file"], body["details"]["line"]) == (
            code,
            expected["file"],
            expected["line"],
        )
        assert mirror.memos() == {} and mirror.topics() == {}
        memos.client.request(
            "DELETE", f"/api/workspace/projects/{mirror.project}", params={"version": 1, "confirm": True}
        )


def test_an_unknown_reference_in_a_memo_names_file_and_line_and_changes_nothing(memos: Env, tmp_path: Path) -> None:
    mirror = Mirror(memos, tmp_path, "valid")
    path = "memos/new-idee-export.md"
    mirror.write(path, mirror.text(path).replace("Beispiel:NEW-login-dialog", "Beispiel:STORY-099"))

    result = mirror.sync()

    body = result.json()
    assert result.status_code in (400, 409, 422), result.text
    assert (body["code"], body["details"]["file"], body["details"]["line"]) == ("unknown_reference", path, 12)
    assert mirror.memos() == {}


def test_a_reference_to_another_project_is_found_by_its_name(memos: Env, tmp_path: Path) -> None:
    (tmp_path / "other").mkdir()
    other = Mirror(memos, tmp_path / "other", name="Anderes")
    foreign = other.create_item(title="Fremd")
    mirror = Mirror(memos, tmp_path, name="Beispiel")
    mirror.write(
        "memos/new-ref.md",
        f"# NEW\nSummary: Verweist\nStatus: waiting\nLinks:\n- reference Anderes:{foreign['label']}\n",
    )

    assert mirror.sync().status_code == 200

    created = mirror.memo("MEMO-001")
    links = memos.client.get(f"/api/workspace/elements/{created['uid']}/links").json()["outgoing"]
    assert [(e["role"], e["uid"]) for e in links] == [("reference", foreign["uid"])]
    assert f"- reference Anderes:{foreign['label']}\n" in mirror.text("memos/MEMO-001.md")

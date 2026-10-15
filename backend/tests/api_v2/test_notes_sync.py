"""Notes in the one sync of POST /sources/{id}/sync: same preview, token, status, and decisions as the backlog."""
from __future__ import annotations

import json
from pathlib import Path

from tests.api_v2.conftest import BASE, PROJECT


def _sources(api, workspace) -> str:
    """The project `demo` of the notes tests, now with a markdown folder to sync with."""
    sources = [{"project": PROJECT, "path": "demo", "backend": "database", "sync_path": str(workspace.root / "md")}]
    (workspace.config_dir / "config.json").write_text(json.dumps({"sources": sources}), encoding="utf-8")
    sid = api.get("/api/v2/sources").body[0]["id"]
    saved = api.put(f"/api/v2/sources/{sid}", {"project": PROJECT, "sync_path": str(workspace.root / "md"),
                                               "mirror": "markdown"})
    assert saved.status_code == 200, saved.body
    return sid


def _sync(api, sid: str, **body):
    return api.post(f"/api/v2/sources/{sid}/sync", body)


def _confirm(api, sid: str, **body):
    token = _sync(api, sid).body["token"]
    return _sync(api, sid, confirm=True, token=token, **body)


def test_the_preview_lists_topics_notes_and_note_documents(notes_api, workspace):
    sid = _sources(notes_api, workspace)
    notes_api.post(f"{BASE}/topics", {"name": "Ideas"})
    notes_api.post(f"{BASE}/notes", {"summary": "an idea", "topic": "TOPIC-001"})

    preview = _sync(notes_api, sid).body

    assert [e["label"] for e in preview["topics"]["created"]] == ["TOPIC-001"]
    assert [(e["label"], e["origin"]) for e in preview["notes"]["created"]] == [("NOTE-001", "database")]
    assert preview["note_documents"] == {"created": [], "changed": [], "unchanged": 0}
    assert not (workspace.root / "md" / "notes").exists()


def test_confirming_writes_the_notes_folder_and_a_note_from_the_cloud_gets_its_label(notes_api, workspace):
    sid = _sources(notes_api, workspace)
    notes_api.post(f"{BASE}/notes", {"summary": "an idea", "body": "text"})

    done = _confirm(notes_api, sid)
    folder = Path(workspace.root / "md" / "notes")
    assert done.status_code == 200, done.body
    assert (folder / "NOTE-001.md").read_text(encoding="utf-8").startswith("# NOTE-001\nSummary: an idea\n")

    (folder / "new-from-the-cloud.md").write_text("# NEW\nSummary: written in claude.ai\n", encoding="utf-8")
    done = _confirm(notes_api, sid)

    assert [e["label"] for e in done.body["resolved"]] == ["new-from-the-cloud"]
    note = notes_api.get(f"{BASE}/notes/NOTE-002").body
    assert note["summary"] == "written in claude.ai"
    assert not (folder / "new-from-the-cloud.md").exists() and (folder / "NOTE-002.md").is_file()


def test_a_note_conflict_is_decided_with_a_resolution_of_the_note_kind(notes_api, workspace):
    sid = _sources(notes_api, workspace)
    notes_api.post(f"{BASE}/notes", {"summary": "an idea"})
    _confirm(notes_api, sid)
    note = notes_api.get(f"{BASE}/notes/NOTE-001").body
    notes_api.patch(f"{BASE}/notes/NOTE-001", {"version": note["version"], "summary": "in the database"})
    file = workspace.root / "md" / "notes" / "NOTE-001.md"
    file.write_text(file.read_text(encoding="utf-8").replace("Summary: an idea", "Summary: in the file"),
                    encoding="utf-8")

    preview = _sync(notes_api, sid).body
    [conflict] = preview["conflicts"]
    assert (conflict["kind"], conflict["label"], conflict["reason"]) == ("note", "NOTE-001", "both_changed")
    assert {f["name"]: f["value"] for f in conflict["markdown"]["fields"]}["summary"] == "in the file"
    assert notes_api.get(f"/api/v2/sources/{sid}/sync-status").body["conflicts"] == 1

    done = _sync(notes_api, sid, confirm=True, token=preview["token"],
                 resolutions=[{"kind": "note", "label": "NOTE-001", "choice": "markdown"}])

    assert done.status_code == 200 and done.body["deferred"] == []
    assert notes_api.get(f"{BASE}/notes/NOTE-001").body["summary"] == "in the file"


def test_a_broken_notes_file_stops_the_sync_with_its_line(notes_api, workspace):
    sid = _sources(notes_api, workspace)
    notes_api.post(f"{BASE}/notes", {"summary": "an idea"})
    _confirm(notes_api, sid)
    (workspace.root / "md" / "notes" / "NOTE-001.md").write_text("# NOTE-001\nSummary: x\nStatus: sleeping\n",
                                                                 encoding="utf-8")

    resp = _sync(notes_api, sid)

    assert resp.status_code == 400 and resp.body["code"] == "sync_source_invalid"
    assert resp.body["details"]["reason"] == "note_format" and "line 3" in resp.body["message"]

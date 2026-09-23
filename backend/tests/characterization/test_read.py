"""Characterization tests: pin the current read behavior of the HTTP API."""
from __future__ import annotations


def test_data_for_all_formats(api, workspace, golden):
    sources = [
        {"project": "Backlog", "path": str(workspace.add_backlog("backlog"))},
        {"project": "Checklist", "path": str(workspace.add_backlog("checklist"))},
        {"project": "NoArchive", "path": str(workspace.add_backlog("no_archive"))},
        {"project": "EmptyArchive", "path": str(workspace.add_backlog("empty_archive"))},
    ]
    workspace.write_config(sources)

    resp = api.get("/api/data")

    assert resp.status_code == 200
    golden("read/data_all_formats.json", resp.body)


def test_data_reports_broken_sources(api, workspace, golden):
    plain = workspace.repos / "plain"
    plain.mkdir()
    a_file = workspace.repos / "file.txt"
    a_file.write_text("x", encoding="utf-8")
    workspace.write_config([
        {"project": "Missing", "path": str(workspace.repos / "missing")},
        {"project": "NoTodo", "path": str(plain)},
        {"project": "NotADir", "path": str(a_file)},
    ])

    resp = api.get("/api/data")

    assert resp.status_code == 200
    golden("read/data_broken_sources.json", resp.body)


def test_data_without_config(api):
    resp = api.get("/api/data")

    assert resp.status_code == 404
    assert resp.body == {"items": [], "sources": [], "error": "config.json not found"}


def test_config_migrates_file_paths_to_folders(api, workspace):
    folder = workspace.add_backlog("backlog")
    workspace.write_config([{"project": "Backlog", "path": str(folder / "TODO.md")}])

    resp = api.get("/api/config")

    assert resp.status_code == 200
    assert resp.body == {"sources": [{"project": "Backlog", "path": str(folder)}]}
    assert workspace.read_config() == resp.body


def test_item_file(api, workspace):
    folder = workspace.add_backlog("backlog")
    workspace.write_config([{"project": "Backlog", "path": str(folder)}])

    ok = api.get("/api/itemfile", source="0", path="items/TASK-002/notes.md")
    missing = api.get("/api/itemfile", source="0", path="items/TASK-002/spec.md")
    escape = api.get("/api/itemfile", source="0", path="../../../etc/passwd.md")
    wrong_type = api.get("/api/itemfile", source="0", path="TODO.json")
    bad_source = api.get("/api/itemfile", source="7", path="TODO.md")
    no_source = api.get("/api/itemfile", path="TODO.md")

    assert ok.status_code == 200
    assert ok.body == {"path": "items/TASK-002/notes.md",
                       "content": "# Notes for TASK-002\n\nSome *markdown* notes.\n"}
    assert (missing.status_code, missing.body["code"]) == (404, "file_not_found")
    assert missing.body["path"] == "items/TASK-002/spec.md"
    assert (escape.status_code, escape.body["code"]) == (403, "forbidden")
    assert (wrong_type.status_code, wrong_type.body["code"]) == (403, "forbidden")
    assert (bad_source.status_code, bad_source.body["code"]) == (404, "source_gone")
    assert (no_source.status_code, no_source.body["code"]) == (400, "bad_request")


def test_browse(api, workspace, golden):
    workspace.add_backlog("backlog", name="repo_a")
    (workspace.repos / "repo_b").mkdir()
    (workspace.repos / ".hidden").mkdir()
    (workspace.repos / "a_file.md").write_text("x", encoding="utf-8")

    default = api.get("/api/browse")
    inside = api.get("/api/browse", path=str(workspace.repos / "repo_a" / "docs"))
    fallback = api.get("/api/browse", path=str(workspace.repos / "repo_b" / "gone" / "deeper"))

    golden("read/browse_default.json", default.body)
    golden("read/browse_inside.json", inside.body)
    assert fallback.body["path"] == str((workspace.repos / "repo_b").resolve())


def test_ui_state_roundtrip(api, workspace):
    assert api.get("/api/state").body == {}

    saved = api.post("/api/state", {"view": "kanban", "hidden": {"status": ["Rejected"]}})
    bad = api.post("/api/state", ["not", "an", "object"])

    assert saved.body == {"ok": True}
    assert bad.status_code == 400
    assert api.get("/api/state").body == {"view": "kanban", "hidden": {"status": ["Rejected"]}}

    (workspace.config_dir / "ui_state.json").write_text("{broken", encoding="utf-8")
    assert api.get("/api/state").body == {}

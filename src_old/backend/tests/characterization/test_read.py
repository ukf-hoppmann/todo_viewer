"""Characterization tests: what the API reads from backlogs, configs and the file system."""
from __future__ import annotations

import json


def _stable_ids(body):
    """Source ids depend on the (temporary) path; replace them for golden files."""
    text = json.dumps(body)
    for n, source in enumerate(body["sources"]):
        text = text.replace(source["id"], f"<SOURCE{n}>")
    return json.loads(text)


def test_backlog_for_all_formats(api, workspace, golden):
    workspace.write_config([
        {"project": "Backlog", "path": str(workspace.add_backlog("backlog"))},
        {"project": "Checklist", "path": str(workspace.add_backlog("checklist"))},
        {"project": "NoArchive", "path": str(workspace.add_backlog("no_archive"))},
        {"project": "EmptyArchive", "path": str(workspace.add_backlog("empty_archive"))},
    ])

    resp = api.get("/api/v2/backlog")

    assert resp.status_code == 200
    golden("read/backlog_all_formats.json", _stable_ids(resp.body))


def test_backlog_reports_broken_sources(api, workspace, golden):
    plain = workspace.repos / "plain"
    plain.mkdir()
    a_file = workspace.repos / "file.txt"
    a_file.write_text("x", encoding="utf-8")
    workspace.write_config([
        {"project": "Missing", "path": str(workspace.repos / "missing")},
        {"project": "NoTodo", "path": str(plain)},
        {"project": "NotADir", "path": str(a_file)},
    ])

    resp = api.get("/api/v2/backlog")

    assert resp.status_code == 200
    golden("read/backlog_broken_sources.json", _stable_ids(resp.body))


def test_config_migrates_file_paths_to_folders(api, workspace):
    folder = workspace.add_backlog("backlog")
    workspace.config_dir.mkdir(parents=True, exist_ok=True)
    (workspace.config_dir / "config.json").write_text(json.dumps({
        "sources": [{"project": "Backlog", "path": str(folder / "TODO.md"), "color": "red"}],
        "other": 1,
    }), encoding="utf-8")

    resp = api.get("/api/v2/sources")

    assert [(s["project"], s["path"]) for s in resp.body] == [("Backlog", str(folder))]
    assert workspace.read_config() == {"other": 1}  # the sources moved into the database


def test_documents(api, workspace):
    folder = workspace.add_backlog("backlog")
    workspace.write_config([{"project": "Backlog", "path": str(folder)}])
    source_id = api.get("/api/v2/sources").body[0]["id"]
    url = f"/api/v2/items/{source_id}/TASK-002/documents"

    ok = api.get(f"{url}/notes.md")
    missing = api.get(f"{url}/spec.md")  # listed in the item, file does not exist
    unknown = api.get(f"{url}/other.md")
    bad_item = api.get(f"/api/v2/items/{source_id}/TASK-999/documents/notes.md")
    bad_source = api.get("/api/v2/items/nope/TASK-002/documents/notes.md")

    assert ok.body == {"name": "notes.md", "kind": "notes",
                       "content": "# Notes for TASK-002\n\nSome *markdown* notes.\n", "version": ok.body["version"]}
    assert [d for d in api.get(f"/api/v2/items/{source_id}/TASK-002").body["documents"]] == [
        {"name": "notes.md", "kind": "notes"}, {"name": "spec.md", "kind": "spec"},
        {"name": "extra.md", "kind": "spec"}]
    assert (missing.status_code, missing.body["code"]) == (404, "file_not_found")
    assert (unknown.status_code, unknown.body["code"]) == (404, "file_not_found")
    assert (bad_item.status_code, bad_item.body["code"]) == (404, "item_not_found")
    assert (bad_source.status_code, bad_source.body["code"]) == (404, "source_gone")


def test_folders(api, workspace, golden):
    workspace.add_backlog("backlog", name="repo_a")
    (workspace.repos / "repo_b").mkdir()
    (workspace.repos / ".hidden").mkdir()
    (workspace.repos / "a_file.md").write_text("x", encoding="utf-8")

    default = api.get("/api/v2/folders")
    inside = api.get("/api/v2/folders", path=str(workspace.repos / "repo_a" / "docs"))
    fallback = api.get("/api/v2/folders", path=str(workspace.repos / "repo_b" / "gone" / "deeper"))

    golden("read/browse_default.json", default.body)
    golden("read/browse_inside.json", inside.body)
    assert fallback.body["path"] == str((workspace.repos / "repo_b").resolve())


def test_ui_state_roundtrip(api, workspace):
    assert api.get("/api/v2/ui-state").body == {}

    saved = api.put("/api/v2/ui-state", {"view": "kanban", "hidden": {"status": ["Rejected"]}})
    bad = api.put("/api/v2/ui-state", ["not", "an", "object"])

    assert saved.status_code == 200
    assert bad.status_code == 400
    assert api.get("/api/v2/ui-state").body == {"view": "kanban", "hidden": {"status": ["Rejected"]}}

    # A leftover ui_state.json of an earlier version, even a broken one, does not replace the stored state.
    (workspace.config_dir / "ui_state.json").write_text("{broken", encoding="utf-8")
    assert api.get("/api/v2/ui-state").body == {"view": "kanban", "hidden": {"status": ["Rejected"]}}
    assert (workspace.config_dir / "ui_state.json.bak").is_file()

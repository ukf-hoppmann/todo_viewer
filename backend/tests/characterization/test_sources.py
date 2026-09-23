"""Characterization tests: managing the configured backlog folders."""
from __future__ import annotations


def test_add_source_suggests_repo_name(api, workspace):
    folder = workspace.add_backlog("backlog", name="MyRepo")

    resp = api.post("/api/v2/sources", {"path": str(folder) + "/"})

    assert resp.status_code == 200
    assert (resp.body["project"], resp.body["path"]) == ("MyRepo", str(folder))
    assert workspace.read_config() == {"sources": [{"project": "MyRepo", "path": str(folder)}]}


def test_add_source_with_name_and_duplicate(api, workspace):
    folder = workspace.add_backlog("backlog")
    workspace.write_config([])

    first = api.post("/api/v2/sources", {"path": str(folder), "project": " Custom "})
    dup = api.post("/api/v2/sources", {"path": str(folder), "project": "Other"})

    assert first.body["project"] == "Custom"
    assert (dup.status_code, dup.body["code"]) == (409, "duplicate")


def test_add_source_validation(api, workspace):
    plain = workspace.repos / "plain"
    plain.mkdir()
    a_file = workspace.repos / "f.txt"
    a_file.write_text("x", encoding="utf-8")

    cases = {
        "bad_request": ["x"],
        "missing_path": {"path": "  "},
        "not_found": {"path": str(workspace.repos / "nope")},
        "not_a_dir": {"path": str(a_file)},
        "no_todo": {"path": str(plain)},
    }
    for code, body in cases.items():
        resp = api.post("/api/v2/sources", body)
        assert (resp.status_code, resp.body["code"]) == (400, code), code
        assert isinstance(resp.body["message"], str)


def test_update_source_keeps_unknown_keys(api, workspace):
    a = workspace.add_backlog("backlog", name="A")
    b = workspace.add_backlog("checklist", name="B")
    workspace.write_config([
        {"project": "A", "path": str(a), "extra": "kept"},
        {"project": "B", "path": str(b)},
    ])
    ids = [s["id"] for s in api.get("/api/v2/sources").body]

    renamed = api.put(f"/api/v2/sources/{ids[0]}", {"path": str(a), "project": "A2"})
    dup = api.put(f"/api/v2/sources/{ids[0]}", {"path": str(b)})
    gone = api.put("/api/v2/sources/unknown", {"path": str(a)})

    assert renamed.body["project"] == "A2"
    assert workspace.read_config()["sources"][0] == {"project": "A2", "path": str(a), "extra": "kept"}
    assert (dup.status_code, dup.body["code"]) == (409, "duplicate")
    assert (gone.status_code, gone.body["code"]) == (404, "source_gone")


def test_remove_source(api, workspace):
    a = workspace.add_backlog("backlog", name="A")
    b = workspace.add_backlog("checklist", name="B")
    workspace.write_config([{"project": "A", "path": str(a)}, {"project": "B", "path": str(b)}])
    ids = [s["id"] for s in api.get("/api/v2/sources").body]

    removed = api.delete(f"/api/v2/sources/{ids[0]}")
    gone = api.delete(f"/api/v2/sources/{ids[0]}")

    assert removed.body["path"] == str(a)
    assert (gone.status_code, gone.body["code"]) == (404, "source_gone")
    assert workspace.read_config() == {"sources": [{"project": "B", "path": str(b)}]}

"""/api/v2/sources names the primary side and the mirror of each project and lets the mirror be switched."""
from __future__ import annotations


def _central(api, **fields) -> dict:
    return api.post("/api/v2/sources", {"backend": "database", "project": "Central", **fields})


def _view(source: dict) -> tuple:
    return source["primary"], source["markdown_path"], source["mirror"]


def test_sources_name_their_primary_side_markdown_folder_and_mirror(api, workspace):
    folder = workspace.add_backlog("backlog")
    md = api.post("/api/v2/sources", {"path": str(folder)}).body
    db = _central(api, sync_path="/repos/central").body
    bare = _central(api, project="Bare").body

    assert _view(md) == ("markdown", str(folder), "none")
    assert _view(db) == ("database", "/repos/central", "markdown")
    assert _view(bare) == ("database", None, "none")
    assert [_view(s) for s in api.get("/api/v2/sources").body] == [_view(md), _view(db), _view(bare)]
    assert all("primary" in s and "mirror" in s for s in api.get("/api/v2/backlog").body["sources"])


def test_a_markdown_project_keeps_a_database_mirror_when_asked(api, workspace):
    folder = workspace.add_backlog("backlog")

    added = api.post("/api/v2/sources", {"path": str(folder), "mirror": "database"}).body
    url = f"/api/v2/sources/{added['id']}"
    off = api.put(url, {"path": str(folder), "mirror": "none"}).body
    on = api.put(url, {"path": str(folder), "mirror": "database"}).body
    kept = api.put(url, {"path": str(folder)}).body

    assert (added["mirror"], off["mirror"], on["mirror"], kept["mirror"]) == ("database", "none", "database", "database")


def test_a_mirror_on_the_primary_side_or_without_a_folder_is_refused(api, workspace):
    folder = workspace.add_backlog("backlog")
    md = api.post("/api/v2/sources", {"path": str(folder)}).body["id"]
    db = _central(api).body["id"]

    wrong = api.put(f"/api/v2/sources/{md}", {"path": str(folder), "mirror": "markdown"})
    no_folder = api.put(f"/api/v2/sources/{db}", {"backend": "database", "project": "Central", "mirror": "markdown"})

    assert (wrong.status_code, wrong.body["code"]) == (400, "invalid_value")
    assert (no_folder.status_code, no_folder.body["code"]) == (400, "sync_path_missing")

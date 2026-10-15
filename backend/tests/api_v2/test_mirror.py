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

    mirrors = (added["mirror"], off["mirror"], on["mirror"], kept["mirror"])
    assert mirrors == ("database", "none", "database", "database")


def test_a_mirror_on_the_primary_side_or_without_a_folder_is_refused(api, workspace):
    folder = workspace.add_backlog("backlog")
    md = api.post("/api/v2/sources", {"path": str(folder)}).body["id"]
    db = _central(api).body["id"]

    wrong = api.put(f"/api/v2/sources/{md}", {"path": str(folder), "mirror": "markdown"})
    no_folder = api.put(f"/api/v2/sources/{db}", {"backend": "database", "project": "Central", "mirror": "markdown"})

    assert (wrong.status_code, wrong.body["code"]) == (400, "invalid_value")
    assert (no_folder.status_code, no_folder.body["code"]) == (400, "sync_path_missing")


def _sync(api, sid: str, direction: str) -> dict:
    """Previews, then runs the sync; returns the preview."""
    preview = api.post(f"/api/v2/sources/{sid}/sync", {"direction": direction}).body
    done = api.post(f"/api/v2/sources/{sid}/sync", {"direction": direction, "confirm": True, "token": preview["token"]})
    assert done.status_code == 200, done.body
    return preview


def _counts(preview: dict) -> tuple[int, int]:
    return len(preview["items"]["created"]), len(preview["items"]["changed"])


def test_a_markdown_primary_project_and_its_database_mirror_sync_both_ways_and_trade_places(api, workspace):
    folder = workspace.add_backlog("backlog")
    sid = api.post("/api/v2/sources", {"path": str(folder), "mirror": "database"}).body["id"]
    url = f"/api/v2/items/{sid}/TASK-001"

    first = _sync(api, sid, "from_md")  # primary -> mirror: the copy in the database is created
    again = api.post(f"/api/v2/sources/{sid}/sync", {"direction": "from_md"}).body
    item = api.get(url).body
    api.patch(url, {"version": item["version"], "fields": {"priority": "Urgent"}})
    stale_mirror = api.post(f"/api/v2/sources/{sid}/sync", {"direction": "from_md"}).body
    _sync(api, sid, "from_md")
    back = api.post(f"/api/v2/sources/{sid}/sync", {"direction": "to_md"}).body  # mirror -> primary: nothing to do

    assert _counts(first)[0] > 0 and _counts(again) == (0, 0)
    assert _counts(stale_mirror) == (0, 1) and _counts(back) == (0, 0)

    switched = api.put(f"/api/v2/sources/{sid}", {"backend": "database"}).body
    assert _view(switched) == ("database", str(folder), "markdown")
    assert api.get(url).body["priority"] == "Urgent"  # now read from the database, same item

    off = api.put(f"/api/v2/sources/{sid}", {"backend": "database", "project": switched["project"],
                                             "mirror": "none"}).body
    assert _view(off) == ("database", None, "none")
    assert api.get(url).body["priority"] == "Urgent"


def test_the_primary_source_is_not_switched_while_the_mirror_differs(api, workspace):
    folder = workspace.add_backlog("backlog")
    sid = api.post("/api/v2/sources", {"path": str(folder), "mirror": "database"}).body["id"]
    _sync(api, sid, "from_md")
    url = f"/api/v2/items/{sid}/TASK-001"
    api.patch(url, {"version": api.get(url).body["version"], "fields": {"priority": "Urgent"}})  # the folder moves on

    early = api.put(f"/api/v2/sources/{sid}", {"backend": "database"})

    assert (early.status_code, early.body["code"]) == (409, "sync_required")
    assert _view(api.get("/api/v2/sources").body[0]) == ("markdown", str(folder), "database")

    _sync(api, sid, "from_md")
    done = api.put(f"/api/v2/sources/{sid}", {"backend": "database"})

    assert (done.status_code, _view(done.body)) == (200, ("database", str(folder), "markdown"))
    assert api.get(url).body["priority"] == "Urgent"


def test_a_database_project_keeps_its_folder_when_the_mirror_is_switched_off_and_on(api, workspace):
    folder = str(workspace.root / "md")
    sid = _central(api, sync_path=folder).body["id"]
    url = f"/api/v2/sources/{sid}"
    put = {"backend": "database", "project": "Central", "sync_path": folder}

    off = api.put(url, {**put, "mirror": "none"}).body
    status = api.get(f"{url}/sync-status").body
    on = api.put(url, {**put, "mirror": "markdown"}).body

    assert _view(off) == ("database", folder, "none")
    assert (status["state"], status["last_sync_at"]) == ("none", None)
    assert _view(on) == ("database", folder, "markdown")


def test_an_emptied_folder_really_removes_it(api, workspace):
    folder = str(workspace.root / "md")
    sid = _central(api, sync_path=folder).body["id"]

    gone = api.put(f"/api/v2/sources/{sid}", {"backend": "database", "project": "Central", "sync_path": ""}).body

    assert _view(gone) == ("database", None, "none")


def test_the_automatic_sync_is_a_switch_per_project_that_needs_a_mirror(api, workspace):
    sid = api.post("/api/v2/sources", {"backend": "database", "project": "Central"}).body["id"]
    assert api.get("/api/v2/sources").body[0]["auto_sync"] is False

    refused = api.put(f"/api/v2/sources/{sid}", {"backend": None, "project": "Central", "auto_sync": True})
    assert (refused.status_code, refused.body["code"]) == (400, "auto_sync_needs_mirror")

    on = api.put(f"/api/v2/sources/{sid}", {"project": "Central", "sync_path": str(workspace.root / "md"),
                                            "mirror": "markdown", "auto_sync": True})
    assert on.status_code == 200 and on.body["auto_sync"] is True
    kept = api.put(f"/api/v2/sources/{sid}", {"project": "Central", "sync_path": str(workspace.root / "md")})
    assert kept.body["auto_sync"] is True
    off = api.put(f"/api/v2/sources/{sid}", {"project": "Central", "sync_path": str(workspace.root / "md"),
                                             "auto_sync": False})
    assert off.body["auto_sync"] is False

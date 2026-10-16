from __future__ import annotations

from workspace_env import Env


def test_the_built_in_project_exists_and_comes_first(env: Env) -> None:
    projects = env.projects()

    assert [(p["name"], p["builtin"], p["position"]) for p in projects] == [("Allgemein", True, 0)]
    assert projects[0]["mirror_folder"] is None and projects[0]["mirror_enabled"] is False


def test_create_project_with_a_name_only_and_with_a_mirror(env: Env) -> None:
    plain = env.create("Notizen")
    mirrored = env.create(
        "Viewer", mirror_folder="/work/viewer/docs/todo", mirror_enabled=True, auto_sync=True, sync_direction="to_files"
    )

    assert (plain["name"], plain["version"], plain["position"], plain["mirror_enabled"]) == ("Notizen", 1, 1, False)
    assert mirrored["position"] == 2
    assert (mirrored["mirror_folder"], mirrored["auto_sync"], mirrored["sync_direction"]) == (
        "/work/viewer/docs/todo",
        True,
        "to_files",
    )
    assert [p["name"] for p in env.projects()] == ["Allgemein", "Notizen", "Viewer"]


def test_a_name_is_unique_and_validated(env: Env) -> None:
    env.create("Eins")

    taken = env.client.post("/api/workspace/projects", json={"name": " Eins "})
    empty = env.client.post("/api/workspace/projects", json={"name": "  "})
    relative = env.client.post("/api/workspace/projects", json={"name": "X", "mirror_folder": "relativ/pfad"})
    needs_folder = env.client.post("/api/workspace/projects", json={"name": "Y", "mirror_enabled": True})
    bad_direction = env.client.post("/api/workspace/projects", json={"name": "Z", "sync_direction": "sideways"})

    assert (taken.status_code, taken.json()["code"]) == (400, "project_name_taken")
    assert (empty.status_code, empty.json()["code"]) == (422, "invalid_input")
    assert (relative.status_code, relative.json()["details"]) == (422, {"field": "mirror_folder"})
    assert needs_folder.json()["details"] == {"field": "mirror_folder"}
    assert bad_direction.status_code == 422 and bad_direction.json()["code"] == "validation_error"


def test_update_changes_only_the_sent_fields_and_bumps_the_version(env: Env) -> None:
    project = env.create("Alt", mirror_folder="/a/b", mirror_enabled=True)

    r = env.client.put(f"/api/workspace/projects/{project['uid']}", json={"version": 1, "name": "Neu"})

    assert r.status_code == 200
    assert (r.json()["name"], r.json()["version"], r.json()["mirror_folder"], r.json()["mirror_enabled"]) == (
        "Neu",
        2,
        "/a/b",
        True,
    )


def test_update_can_clear_the_folder_and_switching_the_mirror_off_stops_auto_sync(env: Env) -> None:
    project = env.create("P", mirror_folder="/a/b", mirror_enabled=True, auto_sync=True)

    off = env.client.put(
        f"/api/workspace/projects/{project['uid']}", json={"version": 1, "mirror_enabled": False}
    ).json()
    cleared = env.client.put(
        f"/api/workspace/projects/{project['uid']}", json={"version": 2, "mirror_folder": ""}
    ).json()

    assert (off["mirror_enabled"], off["auto_sync"], off["mirror_folder"]) == (False, False, "/a/b")
    assert cleared["mirror_folder"] is None


def test_update_with_an_old_version_is_a_conflict_and_changes_nothing(env: Env) -> None:
    project = env.create("P")
    env.client.put(f"/api/workspace/projects/{project['uid']}", json={"version": 1, "name": "Zwischendurch"})

    r = env.client.put(f"/api/workspace/projects/{project['uid']}", json={"version": 1, "name": "Zu spät"})

    assert (r.status_code, r.json()["code"]) == (409, "version_conflict")
    assert env.projects()[1]["name"] == "Zwischendurch"


def test_the_built_in_project_cannot_be_renamed_or_removed_but_can_get_a_mirror(env: Env) -> None:
    general = env.general()

    rename = env.client.put(f"/api/workspace/projects/{general['uid']}", json={"version": 1, "name": "Anders"})
    remove = env.client.request(
        "DELETE", f"/api/workspace/projects/{general['uid']}", params={"version": 1, "confirm": True}
    )
    mirror = env.client.put(
        f"/api/workspace/projects/{general['uid']}",
        json={"version": 1, "mirror_folder": "/x/y", "mirror_enabled": True},
    )

    assert rename.json()["code"] == "builtin_project" and remove.json()["code"] == "builtin_project"
    assert mirror.status_code == 200 and mirror.json()["mirror_folder"] == "/x/y"


def test_unknown_project_is_not_found(env: Env) -> None:
    r = env.client.put("/api/workspace/projects/gibt-es-nicht", json={"version": 1, "name": "X"})
    assert (r.status_code, r.json()["code"]) == (404, "not_found")


def test_move_changes_the_order(env: Env) -> None:
    env.create("A")
    env.create("B")
    c = env.create("C")

    moved = env.client.post(f"/api/workspace/projects/{c['uid']}/move", json={"version": 1, "position": 1})

    assert [p["name"] for p in moved.json()] == ["Allgemein", "C", "A", "B"]
    assert [p["position"] for p in moved.json()] == [0, 1, 2, 3]
    assert [p["name"] for p in env.projects()] == ["Allgemein", "C", "A", "B"]
    stale = env.client.post(f"/api/workspace/projects/{c['uid']}/move", json={"version": 1, "position": 0})
    assert stale.status_code == 409


def test_an_empty_project_is_deleted_for_good_and_its_name_is_free_again(env: Env) -> None:
    project = env.create("Leer")

    r = env.client.request("DELETE", f"/api/workspace/projects/{project['uid']}", params={"version": 1})

    assert r.status_code == 200 and r.json() == {"trashed": 0}
    assert [p["name"] for p in env.projects()] == ["Allgemein"]
    env.create("Leer")


def test_a_project_with_content_needs_confirmation_and_then_goes_to_the_trash_with_it(env: Env) -> None:
    project = env.create("Voll")
    uid = str(project["uid"])
    first = env.kinds.run(lambda registry, tx: registry.register(tx, uid, "task"))
    env.kinds.run(lambda registry, tx: registry.register(tx, uid, "story"))

    refused = env.client.request("DELETE", f"/api/workspace/projects/{uid}", params={"version": 1})
    assert (refused.status_code, refused.json()["code"], refused.json()["details"]) == (
        400,
        "project_not_empty",
        {"elements": 2},
    )
    done = env.client.request("DELETE", f"/api/workspace/projects/{uid}", params={"version": 1, "confirm": True})

    assert done.json() == {"trashed": 2}
    assert [p["name"] for p in env.projects()] == ["Allgemein"]
    assert env.kinds.run(lambda registry, tx: registry.get(tx, first.uid)).deleted_at is not None
    env.create("Voll")  # der Name ist wieder frei


def test_changes_are_published_as_public_events(env: Env) -> None:
    seen: list[tuple[str, bool, dict[str, object]]] = []
    env.app.state.events.subscribe("workspace.*", lambda e: seen.append((e.topic, e.public, e.payload)))

    project = env.create("Ereignis")
    env.client.put(f"/api/workspace/projects/{project['uid']}", json={"version": 1, "name": "Ereignis 2"})

    assert [(topic, public, payload["change"]) for topic, public, payload in seen] == [
        ("workspace.project.changed", True, "created"),
        ("workspace.project.changed", True, "updated"),
    ]


def test_settings_changing_operations_are_not_mcp_tools_but_reading_ones_are(env: Env) -> None:
    host = env.app.state.plugin_host
    names = {
        f"workspace_{op.name}"
        for p in host.plugins
        if p.definition.id == "workspace"
        for op in p.definition.operations
        if op.mcp
    }

    assert names == {
        "workspace_list_projects",
        "workspace_browse_folders",
        "workspace_resolve_label",
        "workspace_add_link",
        "workspace_remove_link",
        "workspace_list_links",
        "workspace_search_elements",
    }

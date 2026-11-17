"""Dokumente (Notizen, Specs) eines Knotens über die HTTP-Schnittstelle."""

from __future__ import annotations

from typing import Any

from viewer.core.domain.events import Event
from workspace_env import Env

API = "/api/mindmap"


def _project(env: Env) -> str:
    return str(env.general()["uid"])


def _create(env: Env, title: str = "Thema") -> dict[str, Any]:
    response = env.client.post(f"{API}/nodes", json={"project": _project(env), "title": title})
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _node(env: Env, node: dict[str, Any]) -> dict[str, Any]:
    return env.client.get(f"{API}/nodes/{node['uid']}").json()  # type: ignore[no-any-return]


def _entry(env: Env, node: dict[str, Any], topic: str = "Idee") -> Any:
    return env.client.post(f"{API}/nodes/{node['uid']}/entries", json={"topic": topic, "discussed": ["a"]})


def _trash(env: Env, node: dict[str, Any]) -> None:
    version = _node(env, node)["version"]
    deleted = env.client.request(
        "DELETE", f"/api/workspace/elements/{node['uid']}", params={"version": version, "cascade": True}
    )
    assert deleted.status_code == 200, deleted.text


def test_a_node_starts_without_documents(mindmap: Env) -> None:
    node = _create(mindmap)

    assert node["documents"] == []
    assert mindmap.client.get(f"{API}/nodes/{node['uid']}/documents").json() == []


def test_the_first_entry_creates_the_notes_with_the_title_in_the_header(mindmap: Env) -> None:
    node = _create(mindmap, "Ideen sammeln")

    response = _entry(mindmap, node)

    assert response.status_code == 200, response.text
    document = response.json()
    assert (document["name"], document["kind"], document["version"]) == ("NODE-001_notes.md", "notes", 1)
    assert document["content"].startswith("# NODE-001 — Ideen sammeln\n\n## ")
    assert "### Discussed\n\n- a\n" in document["content"]
    assert _node(mindmap, node)["documents"] == ["NODE-001_notes.md"]


def test_a_later_entry_is_appended_and_raises_the_version(mindmap: Env) -> None:
    node = _create(mindmap)
    _entry(mindmap, node, "Eins")

    second = _entry(mindmap, node, "Zwei").json()

    assert second["version"] == 2
    assert second["content"].index("— Eins") < second["content"].index("— Zwei")


def test_a_spec_is_created_without_version_and_replaced_with_it(mindmap: Env) -> None:
    node = _create(mindmap)
    url = f"{API}/nodes/{node['uid']}/documents/NODE-001_spec.md"

    created = mindmap.client.put(url, json={"content": "# Spec\n"})
    again = mindmap.client.put(url, json={"content": "# Spec\n"})
    replaced = mindmap.client.put(url, json={"content": "# Neu\n", "version": 1})
    stale = mindmap.client.put(url, json={"content": "# Alt\n", "version": 1})

    assert created.status_code == 200 and created.json()["kind"] == "spec"
    assert again.status_code == 400 and again.json()["code"] == "document_exists"
    assert replaced.status_code == 200 and replaced.json()["version"] == 2
    assert stale.status_code == 409 and stale.json()["code"] == "version_conflict"
    assert mindmap.client.get(url).json()["content"] == "# Neu\n"


def test_names_not_following_the_label_are_refused_and_unknown_ones_are_not_found(mindmap: Env) -> None:
    node = _create(mindmap)

    wrong = mindmap.client.put(f"{API}/nodes/{node['uid']}/documents/other.md", json={"content": "x"})
    missing = mindmap.client.get(f"{API}/nodes/{node['uid']}/documents/NODE-001_spec.md")

    assert wrong.status_code == 422
    assert missing.status_code == 400 and missing.json()["code"] == "document_not_found"


def test_the_notes_come_first_in_the_list_and_in_the_tree(mindmap: Env) -> None:
    node = _create(mindmap)
    mindmap.client.put(f"{API}/nodes/{node['uid']}/documents/NODE-001_spec.md", json={"content": "# S\n"})
    _entry(mindmap, node)
    other = _create(mindmap, "Ohne")

    listed = mindmap.client.get(f"{API}/nodes/{node['uid']}/documents").json()
    tree = {n["uid"]: n for n in mindmap.client.get(f"{API}/trees/{_project(mindmap)}").json()["nodes"]}

    assert [d["name"] for d in listed] == ["NODE-001_notes.md", "NODE-001_spec.md"]
    assert tree[node["uid"]]["documents"] == ["NODE-001_notes.md", "NODE-001_spec.md"]
    assert tree[other["uid"]]["documents"] == []


def test_a_node_in_the_trash_can_be_read_but_not_written(mindmap: Env) -> None:
    node = _create(mindmap)
    _entry(mindmap, node)
    _trash(mindmap, node)

    read = mindmap.client.get(f"{API}/nodes/{node['uid']}/documents/NODE-001_notes.md")
    write = _entry(mindmap, node, "Neu")

    assert read.status_code == 200
    assert write.status_code == 400 and write.json()["code"] == "mindmap_node_deleted"


def test_documents_survive_the_trash_and_go_with_the_purge(mindmap: Env) -> None:
    node = _create(mindmap)
    _entry(mindmap, node)
    _trash(mindmap, node)
    mindmap.client.post("/api/workspace/trash/restore", json={"uids": [node["uid"]]})
    assert _node(mindmap, node)["documents"] == ["NODE-001_notes.md"]

    _trash(mindmap, node)
    assert mindmap.client.post("/api/workspace/trash/purge", json={"uids": [node["uid"]]}).status_code == 200

    with mindmap.app.state.database.transaction() as tx:
        count = tx.connection.exec_driver_sql("SELECT COUNT(*) FROM mindmap_documents").scalar_one()
    assert count == 0


def test_writing_a_document_is_announced_as_a_public_event(mindmap: Env) -> None:
    seen: list[Event] = []
    mindmap.app.state.events.subscribe("mindmap.document.*", seen.append)
    node = _create(mindmap)

    _entry(mindmap, node)
    _entry(mindmap, node, "Zwei")

    assert all(e.topic == "mindmap.document.changed" and e.public for e in seen)
    assert [(e.payload["change"], e.payload["name"]) for e in seen] == [
        ("created", "NODE-001_notes.md"),
        ("updated", "NODE-001_notes.md"),
    ]
    assert seen[0].payload["uid"] == node["uid"]

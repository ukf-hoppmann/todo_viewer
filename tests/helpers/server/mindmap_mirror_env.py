"""Hilfen für die Tests des Mindmap-Spiegels: Ordner, Sync und Dateien von Knoten und Bäumen."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workspace_env import Env

API = "/api/mindmap"
PROJECT_UID = "9a2b0f4c-0d5e-4f60-8a71-2b3c4d5e6f70"
MAP_UID = "9a2b0f4c-0d5e-4f60-8a71-2b3c4d5e6f71"
NODE_UIDS = [f"5d1c0c2e-7a53-4a0e-9f3b-0c9f8f6e1a0{n}" for n in range(1, 5)]
BASE = {"title": "Item", "area": "Server", "goal": "Ziel", "completion_criteria": "Kriterien"}


class Mirror:
    def __init__(self, env: Env, tmp_path: Path, name: str = "Beispiel") -> None:
        self.env = env
        self.folder = tmp_path / "mirror"
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

    def node(self, title: str, tree: str | None = None, **fields: Any) -> dict[str, Any]:
        body = {"project": self.project, "title": title, "tree": tree, **fields}
        response = self.env.client.post(f"{API}/nodes", json=body)
        assert response.status_code == 200, response.text
        return response.json()  # type: ignore[no-any-return]

    def new_map(self, name: str = "Ideen") -> str:
        response = self.env.client.post(f"{API}/maps", json={"project": self.project, "name": name})
        assert response.status_code == 200, response.text
        return str(response.json()["tree_uid"])

    def tree(self, tree: str | None = None) -> list[tuple[str, str | None]]:
        """(Titel, Titel des Parents) der lebenden Knoten, Eltern vor Kindern."""
        nodes = self.env.client.get(f"{API}/trees/{self.project}", params={"tree": tree} if tree else {}).json()[
            "nodes"
        ]
        titles = {n["uid"]: n["title"] for n in nodes}
        return [(n["title"], titles.get(n["parent_uid"])) for n in nodes]

    def nodes(self, tree: str | None = None) -> dict[str, dict[str, Any]]:
        nodes = self.env.client.get(f"{API}/trees/{self.project}", params={"tree": tree} if tree else {}).json()[
            "nodes"
        ]
        return {n["title"]: n for n in nodes}

    def maps(self) -> list[dict[str, Any]]:
        return self.env.client.get(f"{API}/maps/{self.project}").json()  # type: ignore[no-any-return]


def node_file(label: str | None, uid: str | None, title: str, body: str = "", mark: str = "", deleted: str = "") -> str:
    lines = [f"# {label or 'NEW'}"]
    if uid:
        lines.append(f"Uid: {uid}")
    lines += [f"Title: {title}", f"Mark: {mark}".rstrip(), f"Deleted: {deleted}".rstrip()]
    return "\n".join(lines) + "\n" + (f"\n{body}\n" if body else "")


def project_file(listing: str, uid: str = PROJECT_UID) -> str:
    return f"# Projekt\nFormat: mindmap format version 1\nUid: {uid}\nKind: project\n\n{listing}"


def map_file(name: str, listing: str, uid: str | None = MAP_UID) -> str:
    uid_line = f"Uid: {uid}\n" if uid else ""
    return (
        f"# {name if uid else 'NEW'}\nFormat: mindmap format version 1\n{uid_line}"
        f"Kind: free\nName: {name}\nDeleted:\n\n{listing}"
    )


def example_files(mirror: Mirror) -> None:
    """Projektbaum: A (B, C), D; Map „Ideen“: C."""
    for index, (title, text) in enumerate([("A", "Text A"), ("B", ""), ("C", ""), ("D", "")]):
        label = f"NODE-00{index + 1}"
        mirror.write(f"mindmap/{label}.md", node_file(label, NODE_UIDS[index], title, text))
    mirror.write("mindmap/project.md", project_file("- NODE-001\n  - NODE-002\n  - NODE-003\n- NODE-004\n"))
    mirror.write("mindmap/maps/ideen.md", map_file("Ideen", "- NODE-003\n"))

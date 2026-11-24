"""Ein typischer Ablauf des Harness über MCP, gegen den ganzen Viewer (STORY-081).

Jeder Schritt entspricht einem Befehl von `backlog_api.py` oder `memos_api.py`; die Zuordnung steht in
`docs/techdocs/interfaces.md`, „MCP-Tools für den Harness“.
"""

from __future__ import annotations

import asyncio
import json
import socket
import threading
import time
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import uvicorn
from mcp import Client
from mcp.types import TextContent
from running_server import RunningServer
from viewer.app.composition import create_app
from viewer.core.domain.settings import Settings


@pytest.fixture
def viewer(tmp_path: Path) -> Iterator[RunningServer]:
    """Der ganze Viewer mit allen Plugins (`PLUGINS`) als echter uvicorn-Server auf einem freien Port."""
    settings = Settings(
        sse_keepalive_seconds=0.2,
        db_path=str(tmp_path / "viewer.db"),
        backup_dir=str(tmp_path / "backups"),
        log_dir=str(tmp_path / "logs"),
    )
    app = create_app(settings)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", lifespan="on"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not server.started and time.time() < deadline:
        time.sleep(0.02)
    assert server.started, "Server startet nicht"
    try:
        yield RunningServer(f"http://127.0.0.1:{port}", app)
    finally:
        server.should_exit = True
        thread.join(timeout=10)


def _body(content: Any) -> Any:
    assert isinstance(content, TextContent)
    return json.loads(content.text)


class Harness:
    def __init__(self, client: Client) -> None:
        self._client = client

    async def call(self, tool: str, **arguments: Any) -> Any:
        result = await self._client.call_tool(tool, arguments)
        body = _body(result.content[0])
        assert not result.is_error, f"{tool}: {body}"
        return body

    async def fails(self, tool: str, **arguments: Any) -> dict[str, Any]:
        result = await self._client.call_tool(tool, arguments)
        assert result.is_error, f"{tool} hätte scheitern müssen"
        body: dict[str, Any] = _body(result.content[0])
        return body


ITEM = {"title": "Login bauen", "goal": "Anmelden", "completion_criteria": "Tests grün"}


async def session(harness: Harness) -> None:
    assert (await harness.call("core_health")) == {"status": "ok"}

    # sources: die Projekte mit ihren Ordnern
    projects = await harness.call("workspace_list_projects")
    general = next(p for p in projects if p["builtin"])["uid"]

    # index: die kompakten Zeilen, zuerst leer
    empty = await harness.call("backlog_index_lines", projects=general)
    assert empty == {"text": "ID | Type | Status | Title | Parent | Notes", "count": 0}

    # create und update mit Version
    epic = await harness.call("backlog_create_item", project=general, type="Epic", fields=ITEM)
    story = await harness.call(
        "backlog_create_item",
        project=general,
        type="Story",
        fields={**ITEM, "title": "Maske", "parent": epic["uid"], "required_for_parent": True},
    )
    assert (epic["label"], story["label"]) == ("EPIC-001", "STORY-001")
    started = await harness.call(
        "backlog_update_item", ref=story["uid"], version=story["version"], fields={"status": "In progress"}
    )
    assert started["status"] == "In progress" and started["version"] > story["version"]
    stale = await harness.fails(
        "backlog_update_item", ref=story["uid"], version=story["version"], fields={"priority": "Urgent"}
    )
    assert stale["code"] == "version_conflict"
    index = await harness.call("backlog_index_lines", projects=general)
    assert index["count"] == 2
    assert "STORY-001 | Story | In progress | Maske | EPIC-001 | -" in index["text"].splitlines()

    # note: Eintrag an die Notizen des Items
    entry = await harness.call(
        "backlog_append_note",
        ref=story["uid"],
        topic="Start",
        discussed=["Maske"],
        decided=["Los"],
        open=[],
        summary="Maske gebaut",
    )
    assert entry["name"] == "STORY-001_notes.md"
    document = await harness.call("backlog_get_document", ref=story["uid"], name="STORY-001_notes.md")
    assert "Start" in document["content"]
    assert entry["notes_state"] == "missing" and entry["hints"][0]["code"] == "notes_state_stale"

    # state, put-state, confirm-state: der Kopf der Notizen ohne Protokoll (STORY-093)
    head = await harness.call("backlog_put_notes_state", ref=story["uid"], content="- Goal/Status: Maske", version=1)
    assert head["state"] == "current" and head["stamp"]["topic"] == "Start"
    later = await harness.call(
        "backlog_append_note", ref=story["uid"], topic="Weiter", discussed=["Feinschliff"], decided=[], open=[]
    )
    assert later["notes_state"] == "stale"
    assert (await harness.call("backlog_get_notes_state", ref=story["uid"]))["state"] == "stale"
    confirmed = await harness.call("backlog_confirm_notes_state", ref=story["uid"], version=head["version"])
    assert confirmed["state"] == "current" and confirmed["content"] == "- Goal/Status: Maske"
    last = await harness.call("backlog_list_notes_entries", ref=story["uid"], last=1)
    assert [e["topic"] for e in last] == ["Weiter"]

    # Note anlegen, im Index sehen, mit dem Item verknüpfen
    memo = await harness.call("memos_create_memo", project=general, fields={"summary": "Passwort-Regeln klären"})
    assert memo["label"] == "MEMO-001"
    lines = await harness.call("memos_index_lines", projects=general)
    assert lines["memo_count"] == 1 and lines["memos"].splitlines()[1].startswith("MEMO-001 | waiting | - |")
    await harness.call("workspace_add_link", from_uid=memo["uid"], to_uid=story["uid"], role="reference")
    links = await harness.call("workspace_list_links", uid=story["uid"])
    assert [e["uid"] for e in links["incoming"]] == [memo["uid"]]
    assert (await harness.call("memos_get_memos_settings"))["review_days"] == 30

    # Wecker stellen und erledigen
    at = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    alarm = await harness.call(
        "alarms_create_alarm", project=general, fields={"text": "Maske prüfen", "at": at, "target": story["uid"]}
    )
    assert alarm["status"] == "Pending" and alarm["targets"][0]["label"] == "STORY-001"
    listed = await harness.call("alarms_list_alarms", projects=general)
    assert [a["uid"] for a in listed] == [alarm["uid"]]
    done = await harness.call("alarms_finish_alarm", ref=alarm["uid"], version=alarm["version"])
    assert done["status"] == "Done"

    # delete, trash und restore
    current = await harness.call("backlog_get_item", ref=story["uid"])
    gone = await harness.call("workspace_delete_element", uid=story["uid"], version=current["version"], cascade=False)
    assert (gone["has_children"], gone["deleted"]) == (False, 1)
    assert [t["uid"] for t in await harness.call("workspace_list_trash")] == [story["uid"]]
    await harness.call("workspace_restore_elements", uids=[story["uid"]])
    assert (await harness.call("backlog_index_lines", projects=general))["count"] == 2


def test_a_typical_harness_session_works_over_mcp(viewer: RunningServer) -> None:
    async def scenario() -> None:
        async with Client(viewer.base_url + "/mcp") as client:
            await session(Harness(client))

    asyncio.run(scenario())

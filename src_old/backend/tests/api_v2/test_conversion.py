"""Note → item and item → note through API v2, for a database project and a markdown project.

The notes always live in the database; the project decides where the item and its documents are stored.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from tests.conftest import ApiClient, Workspace
from todo_viewer.domain.notes import LinkTarget, NewNotice, NoticeCause, NoticeSide, TargetKind

FIELDS = {"item_type": "Task", "area": "Core", "goal": "A goal.", "completion_criteria": "Checked."}


@dataclass
class Project:
    api: ApiClient
    name: str
    source_id: str

    @property
    def base(self) -> str:
        return f"/api/v2/projects/{self.name}"

    def note(self, summary: str = "an idea", **extra) -> dict:
        resp = self.api.post(f"{self.base}/notes", {"summary": summary, **extra})
        assert resp.status_code == 201, resp.body
        return resp.body

    def promote(self, label: str, version: str, **extra):
        return self.api.post(f"/api/v2/notes/{self.name}/{label}/promote", {"version": version, **FIELDS, **extra})

    def item(self, type_: str = "Task", **extra) -> dict:
        body = {"source_id": self.source_id, "type": type_, "title": "A task", "area": "Core", "goal": "A goal.",
                "completion_criteria": "Checked.", "summary": "What it is.", **extra}
        resp = self.api.post("/api/v2/items", body)
        assert resp.status_code == 201, resp.body
        return resp.body

    def demote(self, item: dict, **extra):
        return self.api.post(f"/api/v2/items/{self.source_id}/{item['id']}/demote",
                             {"version": item["version"], **extra})

    def get_item(self, item_id: str) -> dict:
        return self.api.get(f"/api/v2/items/{self.source_id}/{item_id}").body

    def origin_links(self, label: str) -> list[dict]:
        return [link for link in self.api.get(f"{self.base}/notes/{label}/links").body if link["role"] == "origin"]


@pytest.fixture(params=["database", "markdown"])
def project(request, api: ApiClient, workspace: Workspace) -> Project:
    if request.param == "database":
        workspace.write_config([{"project": "demo", "path": "demo", "backend": "database"}])
    else:
        folder = workspace.add_backlog("empty_archive")
        workspace.write_config([{"project": "demo", "path": str(folder)}])
    source = next(s for s in api.get("/api/v2/sources").body if s["project"] == "demo")
    return Project(api, "demo", source["id"])


# ---------- promote ----------

def test_a_note_becomes_a_task_with_its_texts_and_a_link_back(project: Project):
    note = project.note("an idea", body="Long text.")
    project.api.put(f"{project.base}/notes/NOTE-001/documents/NOTE-001_spec.md",
                    {"content": "# Spec\n", "version": None})

    resp = project.promote("NOTE-001", note["version"])

    assert resp.status_code == 200, resp.body
    item, promoted = resp.body["item"], resp.body["note"]
    item_id = item["id"]
    assert item_id.startswith("TASK-")
    assert (item["title"], item["summary"].rstrip("."), item["status"]) == ("an idea", "an idea", "Open")
    assert (promoted["stored_status"], promoted["archived"]) == ("promoted", True)
    assert [link["target"] for link in project.origin_links("NOTE-001")] == [item_id]
    assert sorted(d["name"] for d in item["documents"]) == [f"{item_id}_notes.md", f"{item_id}_spec.md"]
    notes = project.api.get(f"/api/v2/items/{project.source_id}/{item_id}/documents/{item_id}_notes.md").body
    assert "Aus Note NOTE-001 befördert" in notes["content"] and "- Long text." in notes["content"]
    spec = project.api.get(f"/api/v2/items/{project.source_id}/{item_id}/documents/{item_id}_spec.md").body
    assert spec["content"] == "# Spec\n"


@pytest.mark.parametrize("item_type", ["Story", "Epic"])
def test_a_note_becomes_a_story_or_an_epic(project: Project, item_type):
    note = project.note()

    resp = project.promote("NOTE-001", note["version"], item_type=item_type)

    assert resp.status_code == 200, resp.body
    assert (resp.body["item"]["type"], resp.body["item"]["id"].startswith(item_type.upper() + "-")) == (item_type, True)


def test_the_caller_may_replace_title_and_summary(project: Project):
    note = project.note()

    resp = project.promote("NOTE-001", note["version"], title="Better", summary="Better summary")

    assert (resp.body["item"]["title"], resp.body["item"]["summary"].rstrip(".")) == (
        "Better", "Better summary")


def test_a_missing_field_is_a_bad_request_and_changes_nothing(project: Project):
    note = project.note()
    body = {"version": note["version"], "item_type": "Task", "area": "Core"}

    resp = project.api.post(f"/api/v2/notes/{project.name}/NOTE-001/promote", body)

    assert (resp.status_code, resp.body["code"]) == (400, "bad_request")
    assert project.api.get(f"{project.base}/notes/NOTE-001").body["stored_status"] == "waiting"


def test_a_closed_parent_is_refused_and_the_note_stays_open(project: Project):
    epic = project.item("Epic")
    closed = project.api.patch(f"/api/v2/items/{project.source_id}/{epic['id']}",
                               {"version": epic["version"], "fields": {"status": "Rejected"}, "resolution": "no"})
    assert closed.status_code == 200, closed.body
    note = project.note()

    resp = project.promote("NOTE-001", note["version"], parent=epic["id"], required_for_parent="Yes")

    assert (resp.status_code, resp.body["code"]) == (409, "parent_closed")
    assert project.api.get(f"{project.base}/notes/NOTE-001").body["stored_status"] == "waiting"
    assert project.origin_links("NOTE-001") == []


def test_a_stale_version_and_an_unknown_note_are_refused(project: Project):
    project.note()

    stale = project.promote("NOTE-001", "stale")
    unknown = project.promote("NOTE-009", "x")

    assert (stale.status_code, stale.body["code"]) == (409, "version_conflict")
    assert (unknown.status_code, unknown.body["code"]) == (404, "note_not_found")


def test_a_promoted_note_cannot_be_promoted_again(project: Project):
    note = project.note()
    project.promote("NOTE-001", note["version"])
    promoted = project.api.get(f"{project.base}/notes/NOTE-001").body

    again = project.promote("NOTE-001", promoted["version"])

    assert (again.status_code, again.body["code"]) == (409, "note_closed")


# ---------- the notice decision `promote` ----------

def test_the_decision_promote_promotes_the_note_and_decides_the_notice(project: Project):
    story = project.item("Story")
    note = project.note()
    link = project.api.post(f"{project.base}/notes/NOTE-001/links", {"kind": "item", "target": story["id"]})
    assert link.status_code == 201, link.body
    project.api._raw.app.state.container.notes.add_notice(
        NewNotice(NoticeSide.NOTE, "demo", "NOTE-001", NoticeCause.ITEM_COMPLETED,
                  LinkTarget(TargetKind.ITEM, "demo", story["id"])))
    notice = project.api.get("/api/v2/notices", project="demo", label="NOTE-001", side="note", open="true").body[0]
    url = f"/api/v2/notices/{notice['id']}/decision"

    refused = project.api.post(url, {"decision": "promote"})
    resp = project.api.post(url, {"decision": "promote", "promotion": FIELDS})

    assert (refused.status_code, refused.body["code"]) == (409, "decision_not_available")
    assert resp.status_code == 200, resp.body
    assert (resp.body["note"]["stored_status"], resp.body["notice"]["decision"]) == ("promoted", "promote")
    assert resp.body["item"]["id"].startswith("TASK-")
    assert note["label"] == "NOTE-001"


# ---------- demote ----------

def test_an_open_item_becomes_a_note_and_is_rejected(project: Project):
    item = project.item()
    project.api.put(f"/api/v2/items/{project.source_id}/{item['id']}/documents/{item['id']}_spec.md",
                    {"content": "# Spec\n", "version": None})

    resp = project.demote(project.get_item(item["id"]))

    assert resp.status_code == 200, resp.body
    note, closed = resp.body["note"], resp.body["item"]
    assert (note["label"], note["summary"], note["body"].rstrip("."), note["stored_status"]) == (
        "NOTE-001", "A task", "What it is", "waiting")
    assert (closed["status"], closed["resolution"].rstrip("."), closed["archived"]) == (
        "Rejected", "zur Notiz zurückgestuft", True)
    assert [link["target"] for link in project.origin_links("NOTE-001")] == [item["id"]]
    spec = project.api.get(f"{project.base}/notes/NOTE-001/documents/NOTE-001_spec.md").body
    assert spec["content"] == "# Spec\n"


def test_the_new_note_goes_into_the_given_topic(project: Project):
    topic = project.api.post(f"{project.base}/topics", {"name": "Ideas"}).body
    item = project.item()

    resp = project.demote(item, topic=topic["label"])

    assert resp.body["note"]["topic"] == topic["label"]


def test_an_item_that_is_not_open_is_refused(project: Project):
    item = project.item()
    started = project.api.patch(f"/api/v2/items/{project.source_id}/{item['id']}",
                                {"version": item["version"], "fields": {"status": "In progress"}}).body

    resp = project.demote(started)

    assert (resp.status_code, resp.body["code"]) == (409, "demote_not_open")
    assert project.api.get(f"{project.base}/notes/NOTE-001").status_code == 404


def test_an_item_with_children_is_refused_with_their_ids(project: Project):
    story = project.item("Story")
    child = project.item("Task", parent=story["id"], required_for_parent="Yes")

    resp = project.demote(story)

    assert (resp.status_code, resp.body["code"], resp.body["details"]["items"]) == (
        409, "demote_has_children", child["id"])


def test_an_item_other_items_depend_on_is_refused(project: Project):
    first = project.item()
    second = project.item(dependencies=[first["id"]])

    resp = project.demote(first)

    assert (resp.status_code, resp.body["code"], resp.body["details"]["items"]) == (
        409, "demote_referenced", second["id"])


def test_a_stale_item_version_is_refused(project: Project):
    item = project.item()

    resp = project.demote({**item, "version": "stale"})

    assert (resp.status_code, resp.body["code"]) == (409, "version_conflict")


def test_the_origin_is_visible_on_both_sides_after_a_round_trip(project: Project):
    note = project.note()
    item = project.promote("NOTE-001", note["version"]).body["item"]

    back = project.demote(project.get_item(item["id"]))

    assert back.status_code == 200, back.body
    assert back.body["note"]["label"] == "NOTE-002"
    assert [link["target"] for link in project.origin_links("NOTE-001")] == [item["id"]]
    assert [link["target"] for link in project.origin_links("NOTE-002")] == [item["id"]]
    assert json.dumps(project.api.get(f"{project.base}/items/{item['id']}/notes").body).count("origin") == 2

from __future__ import annotations

from datetime import timedelta

from notes_api import (
    NOTES,
    add_trigger,
    item,
    link,
    links,
    new_item,
    new_note,
    note,
    project,
    set_status,
)
from workspace_env import Env


def _trigger_links(env: Env, uid: str) -> list[str]:
    return [entry["uid"] for entry in links(env, uid)["outgoing"] if entry["role"] == "trigger"]


def test_a_note_waits_until_the_item_reaches_the_status(notes: Env) -> None:
    entry, target = new_note(notes), new_item(notes)
    added = add_trigger(notes, entry, kind="event", target=target["uid"], status="In progress")
    assert added.status_code == 200, added.text
    shown = added.json()
    assert shown["status"] == "waiting"
    trigger = shown["triggers"][0]
    assert (trigger["kind"], trigger["status"], trigger["arrived"], trigger["already_met"]) == (
        "event",
        "In progress",
        False,
        False,
    )
    assert (trigger["target"]["label"], trigger["target"]["title"]) == (target["label"], "Ein Item")

    set_status(notes, target, "In progress")

    fired = note(notes, entry["uid"])
    assert (fired["status"], fired["reason"], fired["stored_status"]) == ("due", "trigger", "waiting")
    assert fired["triggers"][0]["arrived"] is True and fired["triggers"][0]["fired_at"] is not None


def test_a_trigger_for_another_status_does_not_fire(notes: Env) -> None:
    entry, target = new_note(notes), new_item(notes)
    add_trigger(notes, entry, kind="event", target=target["uid"], status="Completed")

    set_status(notes, target, "In progress")

    assert note(notes, entry["uid"])["status"] == "waiting"


def test_an_item_that_has_the_status_already_fires_the_trigger_at_once(notes: Env) -> None:
    entry, target = new_note(notes), new_item(notes)
    set_status(notes, target, "In progress")

    shown = add_trigger(notes, entry, kind="event", target=target["uid"], status="In progress").json()

    assert (shown["status"], shown["reason"]) == ("due", "trigger")
    assert shown["triggers"][0]["already_met"] is True


def test_the_target_can_be_named_by_its_label(notes: Env) -> None:
    entry, target = new_note(notes), new_item(notes)

    shown = add_trigger(notes, entry, kind="event", target=target["label"], status="Completed", project=project(notes))

    assert shown.status_code == 200
    assert shown.json()["triggers"][0]["target"]["uid"] == target["uid"]


def test_an_event_trigger_links_the_note_to_the_item_and_removing_it_removes_the_link(notes: Env) -> None:
    entry, target = new_note(notes), new_item(notes)
    shown = add_trigger(notes, entry, kind="event", target=target["uid"], status="Completed").json()

    assert len(_trigger_links(notes, entry["uid"])) == 1
    removed = notes.client.delete(f"{NOTES}/triggers/{shown['triggers'][0]['uid']}")
    assert removed.status_code == 200 and removed.json()["triggers"] == []
    assert _trigger_links(notes, entry["uid"]) == []


def test_two_triggers_on_one_item_share_the_link_until_both_are_gone(notes: Env) -> None:
    entry, target = new_note(notes), new_item(notes)
    add_trigger(notes, entry, kind="event", target=target["uid"], status="In progress")
    shown = add_trigger(notes, entry, kind="event", target=target["uid"], status="Completed").json()
    first, second = (t["uid"] for t in shown["triggers"])

    assert len(_trigger_links(notes, entry["uid"])) == 1
    notes.client.delete(f"{NOTES}/triggers/{first}")
    assert len(_trigger_links(notes, entry["uid"])) == 1
    notes.client.delete(f"{NOTES}/triggers/{second}")
    assert _trigger_links(notes, entry["uid"]) == []


def test_the_trigger_role_is_reserved_for_triggers(notes: Env) -> None:
    entry, target = new_note(notes), new_item(notes)
    refused = notes.client.post(
        "/api/workspace/links", json={"from_uid": entry["uid"], "to_uid": target["uid"], "role": "trigger"}
    )
    assert refused.status_code == 400 and refused.json()["code"] == "trigger_link_reserved"


def test_in_mode_all_every_trigger_has_to_arrive(notes: Env) -> None:
    entry = new_note(notes, trigger_mode="all")
    first, second = new_item(notes), new_item(notes)
    add_trigger(notes, entry, kind="event", target=first["uid"], status="In progress")
    add_trigger(notes, entry, kind="event", target=second["uid"], status="In progress")

    set_status(notes, first, "In progress")
    assert note(notes, entry["uid"])["status"] == "waiting"
    set_status(notes, second, "In progress")
    assert note(notes, entry["uid"])["status"] == "due"


def test_a_note_in_the_archive_ignores_the_event(notes: Env) -> None:
    entry, target = new_note(notes), new_item(notes)
    added = add_trigger(notes, entry, kind="event", target=target["uid"], status="In progress").json()
    notes.client.post(f"{NOTES}/notes/{entry['uid']}/finish", json={"version": added["version"], "status": "done"})

    set_status(notes, target, "In progress")

    assert note(notes, entry["uid"])["triggers"][0]["fired_at"] is None


def test_snoozing_resets_the_fired_trigger_and_it_fires_again_later(notes: Env) -> None:
    entry, target = new_note(notes), new_item(notes)
    add_trigger(notes, entry, kind="event", target=target["uid"], status="Completed")
    set_status(notes, target, "In progress")
    set_status(notes, target, "Awaiting confirmation")
    set_status(notes, target, "Completed", "Fertig")
    due = note(notes, entry["uid"])
    assert due["status"] == "due"

    snoozed = notes.client.post(f"{NOTES}/notes/{entry['uid']}/snooze", json={"version": due["version"]}).json()
    assert (snoozed["status"], snoozed["triggers"][0]["arrived"]) == ("snoozed", False)

    reopened = item(notes, target["uid"])
    notes.client.put(
        f"/api/backlog/items/{target['uid']}",
        json={"version": reopened["version"], "fields": {"status": "In progress"}, "resolution": None},
    )
    set_status(notes, target, "Awaiting confirmation")
    set_status(notes, target, "Completed", "Wieder fertig")
    assert note(notes, entry["uid"])["status"] == "due"


def test_snoozing_with_a_new_trigger_replaces_all_old_ones(notes: Env) -> None:
    entry = new_note(notes)
    old, new = new_item(notes), new_item(notes)
    first = add_trigger(notes, entry, kind="event", target=old["uid"], status="In progress").json()

    snoozed = notes.client.post(
        f"{NOTES}/notes/{entry['uid']}/snooze",
        json={"version": first["version"], "trigger": {"kind": "event", "target": new["uid"], "status": "Completed"}},
    )

    assert snoozed.status_code == 200, snoozed.text
    triggers = snoozed.json()["triggers"]
    assert [(t["target"]["uid"], t["status"]) for t in triggers] == [(new["uid"], "Completed")]
    assert _trigger_links(notes, entry["uid"]) == [new["uid"]]


def test_a_topic_date_trigger_makes_the_note_due_when_the_date_comes(notes: Env) -> None:
    created = notes.client.post(
        f"{NOTES}/topics", json={"project": project(notes), "name": "Termin", "due_at": "2026-10-20"}
    ).json()
    entry = new_note(notes, topic=created["uid"])
    shown = add_trigger(notes, entry, kind="topic_date").json()
    assert (shown["status"], shown["triggers"][0]["arrived"]) == ("waiting", False)

    notes.clock.advance(timedelta(days=5))

    due = note(notes, entry["uid"])
    assert (due["status"], due["reason"]) == ("due", "topic_due")
    listed = notes.client.get(f"{NOTES}/due").json()
    assert [(n["label"], n["reason"], n["path"]) for n in listed["notes"]] == [
        (entry["label"], "topic_due", ["Termin"])
    ]


def test_a_topic_date_trigger_needs_a_topic_with_a_date(notes: Env) -> None:
    entry = new_note(notes)
    refused = add_trigger(notes, entry, kind="topic_date")
    assert (refused.status_code, refused.json()["code"]) == (400, "trigger_needs_topic_date")


def test_invalid_triggers_are_refused(notes: Env) -> None:
    entry, target = new_note(notes), new_item(notes)
    other = new_note(notes, "Andere")
    for body in (
        {"kind": "time"},
        {"kind": "event", "target": target["uid"], "status": "Open"},
        {"kind": "event", "target": target["uid"]},
        {"kind": "event", "status": "Completed"},
        {"kind": "event", "target": other["uid"], "status": "Completed"},
    ):
        assert add_trigger(notes, entry, **body).status_code == 422, body
    assert add_trigger(notes, entry, kind="event", target="gibt-es-nicht", status="Completed").status_code == 404
    assert note(notes, entry["uid"])["triggers"] == []


def test_a_deleted_item_cannot_be_a_target(notes: Env) -> None:
    entry, target = new_note(notes), new_item(notes)
    notes.client.request("DELETE", f"/api/workspace/elements/{target['uid']}", params={"version": target["version"]})

    assert add_trigger(notes, entry, kind="event", target=target["uid"], status="Completed").status_code == 404


def test_the_due_list_names_the_reason_for_each_note(notes: Env) -> None:
    by_trigger, by_review, quiet = (
        new_note(notes, "Auslöser"),
        new_note(notes, "Prüfung", review_at="2020-01-01"),
        new_note(notes, "Ruhig"),
    )
    target = new_item(notes)
    add_trigger(notes, by_trigger, kind="event", target=target["uid"], status="In progress")
    set_status(notes, target, "In progress")
    link(notes, quiet["uid"], target["uid"])  # only a reference: no notice for In progress

    listed = notes.client.get(f"{NOTES}/due").json()

    assert listed["count"] == 2
    assert {n["label"]: n["reason"] for n in listed["notes"]} == {
        by_trigger["label"]: "trigger",
        by_review["label"]: "review_expired",
    }
    triggered = next(n for n in listed["notes"] if n["reason"] == "trigger")
    assert triggered["triggers"][0]["arrived"] is True


def test_the_index_and_counters_use_the_triggers_too(notes: Env) -> None:
    topic = notes.client.post(f"{NOTES}/topics", json={"project": project(notes), "name": "T"}).json()
    entry, target = new_note(notes, topic=topic["uid"]), new_item(notes)
    add_trigger(notes, entry, kind="event", target=target["uid"], status="In progress")
    set_status(notes, target, "In progress")

    index = notes.client.get(f"{NOTES}/index").json()

    assert [n["status"] for n in index["notes"]] == ["due"]
    assert (index["topics"][0]["open_notes"], index["topics"][0]["due_notes"]) == (1, 1)
    assert notes.client.get(f"{NOTES}/due").json()["count"] == 1

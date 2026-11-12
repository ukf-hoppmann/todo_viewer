from __future__ import annotations

from datetime import timedelta

from memos_api import (
    NOTES,
    add_trigger,
    item,
    link,
    links,
    memo,
    new_item,
    new_memo,
    project,
    set_status,
)
from workspace_env import Env


def _trigger_links(env: Env, uid: str) -> list[str]:
    return [entry["uid"] for entry in links(env, uid)["outgoing"] if entry["role"] == "trigger"]


def test_a_memo_waits_until_the_item_reaches_the_status(memos: Env) -> None:
    entry, target = new_memo(memos), new_item(memos)
    added = add_trigger(memos, entry, kind="event", target=target["uid"], status="In progress")
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

    set_status(memos, target, "In progress")

    fired = memo(memos, entry["uid"])
    assert (fired["status"], fired["reason"], fired["stored_status"]) == ("due", "trigger", "waiting")
    assert fired["triggers"][0]["arrived"] is True and fired["triggers"][0]["fired_at"] is not None


def test_a_trigger_for_another_status_does_not_fire(memos: Env) -> None:
    entry, target = new_memo(memos), new_item(memos)
    add_trigger(memos, entry, kind="event", target=target["uid"], status="Completed")

    set_status(memos, target, "In progress")

    assert memo(memos, entry["uid"])["status"] == "waiting"


def test_an_item_that_has_the_status_already_fires_the_trigger_at_once(memos: Env) -> None:
    entry, target = new_memo(memos), new_item(memos)
    set_status(memos, target, "In progress")

    shown = add_trigger(memos, entry, kind="event", target=target["uid"], status="In progress").json()

    assert (shown["status"], shown["reason"]) == ("due", "trigger")
    assert shown["triggers"][0]["already_met"] is True


def test_the_target_can_be_named_by_its_label(memos: Env) -> None:
    entry, target = new_memo(memos), new_item(memos)

    shown = add_trigger(memos, entry, kind="event", target=target["label"], status="Completed", project=project(memos))

    assert shown.status_code == 200
    assert shown.json()["triggers"][0]["target"]["uid"] == target["uid"]


def test_an_event_trigger_links_the_memo_to_the_item_and_removing_it_removes_the_link(memos: Env) -> None:
    entry, target = new_memo(memos), new_item(memos)
    shown = add_trigger(memos, entry, kind="event", target=target["uid"], status="Completed").json()

    assert len(_trigger_links(memos, entry["uid"])) == 1
    removed = memos.client.delete(f"{NOTES}/triggers/{shown['triggers'][0]['uid']}")
    assert removed.status_code == 200 and removed.json()["triggers"] == []
    assert _trigger_links(memos, entry["uid"]) == []


def test_two_triggers_on_one_item_share_the_link_until_both_are_gone(memos: Env) -> None:
    entry, target = new_memo(memos), new_item(memos)
    add_trigger(memos, entry, kind="event", target=target["uid"], status="In progress")
    shown = add_trigger(memos, entry, kind="event", target=target["uid"], status="Completed").json()
    first, second = (t["uid"] for t in shown["triggers"])

    assert len(_trigger_links(memos, entry["uid"])) == 1
    memos.client.delete(f"{NOTES}/triggers/{first}")
    assert len(_trigger_links(memos, entry["uid"])) == 1
    memos.client.delete(f"{NOTES}/triggers/{second}")
    assert _trigger_links(memos, entry["uid"]) == []


def test_the_trigger_role_is_reserved_for_triggers(memos: Env) -> None:
    entry, target = new_memo(memos), new_item(memos)
    refused = memos.client.post(
        "/api/workspace/links", json={"from_uid": entry["uid"], "to_uid": target["uid"], "role": "trigger"}
    )
    assert refused.status_code == 400 and refused.json()["code"] == "trigger_link_reserved"


def test_in_mode_all_every_trigger_has_to_arrive(memos: Env) -> None:
    entry = new_memo(memos, trigger_mode="all")
    first, second = new_item(memos), new_item(memos)
    add_trigger(memos, entry, kind="event", target=first["uid"], status="In progress")
    add_trigger(memos, entry, kind="event", target=second["uid"], status="In progress")

    set_status(memos, first, "In progress")
    assert memo(memos, entry["uid"])["status"] == "waiting"
    set_status(memos, second, "In progress")
    assert memo(memos, entry["uid"])["status"] == "due"


def test_a_memo_in_the_archive_ignores_the_event(memos: Env) -> None:
    entry, target = new_memo(memos), new_item(memos)
    added = add_trigger(memos, entry, kind="event", target=target["uid"], status="In progress").json()
    memos.client.post(f"{NOTES}/memos/{entry['uid']}/finish", json={"version": added["version"], "status": "done"})

    set_status(memos, target, "In progress")

    assert memo(memos, entry["uid"])["triggers"][0]["fired_at"] is None


def test_snoozing_resets_the_fired_trigger_and_it_fires_again_later(memos: Env) -> None:
    entry, target = new_memo(memos), new_item(memos)
    add_trigger(memos, entry, kind="event", target=target["uid"], status="Completed")
    set_status(memos, target, "In progress")
    set_status(memos, target, "Awaiting confirmation")
    set_status(memos, target, "Completed", "Fertig")
    due = memo(memos, entry["uid"])
    assert due["status"] == "due"

    snoozed = memos.client.post(f"{NOTES}/memos/{entry['uid']}/snooze", json={"version": due["version"]}).json()
    assert (snoozed["status"], snoozed["triggers"][0]["arrived"]) == ("snoozed", False)

    reopened = item(memos, target["uid"])
    memos.client.put(
        f"/api/backlog/items/{target['uid']}",
        json={"version": reopened["version"], "fields": {"status": "In progress"}, "resolution": None},
    )
    set_status(memos, target, "Awaiting confirmation")
    set_status(memos, target, "Completed", "Wieder fertig")
    assert memo(memos, entry["uid"])["status"] == "due"


def test_snoozing_with_a_new_trigger_replaces_all_old_ones(memos: Env) -> None:
    entry = new_memo(memos)
    old, new = new_item(memos), new_item(memos)
    first = add_trigger(memos, entry, kind="event", target=old["uid"], status="In progress").json()

    snoozed = memos.client.post(
        f"{NOTES}/memos/{entry['uid']}/snooze",
        json={"version": first["version"], "trigger": {"kind": "event", "target": new["uid"], "status": "Completed"}},
    )

    assert snoozed.status_code == 200, snoozed.text
    triggers = snoozed.json()["triggers"]
    assert [(t["target"]["uid"], t["status"]) for t in triggers] == [(new["uid"], "Completed")]
    assert _trigger_links(memos, entry["uid"]) == [new["uid"]]


def test_a_topic_date_trigger_makes_the_memo_due_when_the_date_comes(memos: Env) -> None:
    created = memos.client.post(
        f"{NOTES}/topics", json={"project": project(memos), "name": "Termin", "due_at": "2026-10-20"}
    ).json()
    entry = new_memo(memos, topic=created["uid"])
    shown = add_trigger(memos, entry, kind="topic_date").json()
    assert (shown["status"], shown["triggers"][0]["arrived"]) == ("waiting", False)

    memos.clock.advance(timedelta(days=5))

    due = memo(memos, entry["uid"])
    assert (due["status"], due["reason"]) == ("due", "topic_due")
    listed = memos.client.get(f"{NOTES}/due").json()
    assert [(n["label"], n["reason"], n["path"]) for n in listed["memos"]] == [
        (entry["label"], "topic_due", ["Termin"])
    ]


def test_a_topic_date_trigger_needs_a_topic_with_a_date(memos: Env) -> None:
    entry = new_memo(memos)
    refused = add_trigger(memos, entry, kind="topic_date")
    assert (refused.status_code, refused.json()["code"]) == (400, "trigger_needs_topic_date")


def test_invalid_triggers_are_refused(memos: Env) -> None:
    entry, target = new_memo(memos), new_item(memos)
    other = new_memo(memos, "Andere")
    for body in (
        {"kind": "time"},
        {"kind": "event", "target": target["uid"], "status": "Open"},
        {"kind": "event", "target": target["uid"]},
        {"kind": "event", "status": "Completed"},
        {"kind": "event", "target": other["uid"], "status": "Completed"},
    ):
        assert add_trigger(memos, entry, **body).status_code == 422, body
    assert add_trigger(memos, entry, kind="event", target="gibt-es-nicht", status="Completed").status_code == 404
    assert memo(memos, entry["uid"])["triggers"] == []


def test_a_deleted_item_cannot_be_a_target(memos: Env) -> None:
    entry, target = new_memo(memos), new_item(memos)
    memos.client.request("DELETE", f"/api/workspace/elements/{target['uid']}", params={"version": target["version"]})

    assert add_trigger(memos, entry, kind="event", target=target["uid"], status="Completed").status_code == 404


def test_the_due_list_names_the_reason_for_each_memo(memos: Env) -> None:
    by_trigger, by_review, quiet = (
        new_memo(memos, "Auslöser"),
        new_memo(memos, "Prüfung", review_at="2020-01-01"),
        new_memo(memos, "Ruhig"),
    )
    target = new_item(memos)
    add_trigger(memos, by_trigger, kind="event", target=target["uid"], status="In progress")
    set_status(memos, target, "In progress")
    link(memos, quiet["uid"], target["uid"])  # only a reference: no hint for In progress

    listed = memos.client.get(f"{NOTES}/due").json()

    assert listed["count"] == 2
    assert {n["label"]: n["reason"] for n in listed["memos"]} == {
        by_trigger["label"]: "trigger",
        by_review["label"]: "review_expired",
    }
    triggered = next(n for n in listed["memos"] if n["reason"] == "trigger")
    assert triggered["triggers"][0]["arrived"] is True


def test_the_index_and_counters_use_the_triggers_too(memos: Env) -> None:
    topic = memos.client.post(f"{NOTES}/topics", json={"project": project(memos), "name": "T"}).json()
    entry, target = new_memo(memos, topic=topic["uid"]), new_item(memos)
    add_trigger(memos, entry, kind="event", target=target["uid"], status="In progress")
    set_status(memos, target, "In progress")

    index = memos.client.get(f"{NOTES}/index").json()

    assert [n["status"] for n in index["memos"]] == ["due"]
    assert (index["topics"][0]["open_memos"], index["topics"][0]["due_memos"]) == (1, 1)
    assert memos.client.get(f"{NOTES}/due").json()["count"] == 1

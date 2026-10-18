from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from viewer.core.domain.events import Event
from workspace_env import Env

API = "/api/alarms"
AT = "2026-10-16T14:00:00Z"  # zwei Stunden nach der festen Uhr (12:00)


def _project(env: Env) -> str:
    return str(env.general()["uid"])


def _create(env: Env, text: str = "Anrufen", at: str = AT, **fields: Any) -> dict[str, Any]:
    response = env.client.post(
        f"{API}/alarms", json={"project": _project(env), "fields": {"text": text, "at": at, **fields}}
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _post(env: Env, alarm: dict[str, Any], action: str, **body: Any) -> Any:
    return env.client.post(f"{API}/alarms/{alarm['uid']}/{action}", json={"version": alarm["version"], **body})


def _pending(env: Env) -> datetime | None:
    return env.app.state.scheduler.pending_at("alarms")  # type: ignore[no-any-return]


def _events(env: Env) -> list[Event]:
    seen: list[Event] = []
    env.app.state.events.subscribe("alarms.*", seen.append)
    return seen


def test_an_alarm_is_created_with_label_text_time_and_waits(alarms: Env) -> None:
    alarm = _create(alarms, "  Release   vorbereiten ")

    assert (alarm["label"], alarm["text"], alarm["status"]) == ("ALARM-001", "Release vorbereiten", "Pending")
    assert alarm["at"].startswith("2026-10-16T14:00:00") and alarm["targets"] == [] and alarm["deleted"] is False
    assert _pending(alarms) == datetime.fromisoformat("2026-10-16T14:00:00+00:00")


def test_text_and_time_are_required_and_unknown_fields_refused(alarms: Env) -> None:
    project = _project(alarms)
    for fields in (
        {"at": AT},
        {"text": " ", "at": AT},
        {"text": "x"},
        {"text": "x", "at": "morgen"},
        {"text": "x", "at": AT, "colour": 1},
    ):
        response = alarms.client.post(f"{API}/alarms", json={"project": project, "fields": fields})
        assert response.status_code == 422, fields


def test_a_time_without_zone_counts_as_utc_and_a_date_alone_is_midnight(alarms: Env) -> None:
    assert _create(alarms, at="2026-10-17T08:30")["at"].startswith("2026-10-17T08:30:00")
    assert _create(alarms, at="2026-10-18")["at"].startswith("2026-10-18T00:00:00")


def test_the_targets_are_elements_given_by_uid_or_label_in_their_order(alarms: Env) -> None:
    one = _create(alarms, "Eins")
    two = _create(alarms, "Zwei")
    alarm = _create(alarms, "", targets=[two["label"], one["uid"], two["uid"]])

    assert alarm["targets"] == [
        {"uid": two["uid"], "label": two["label"], "title": "Zwei", "kind": "alarm", "deleted": False, "open": True},
        {"uid": one["uid"], "label": one["label"], "title": "Eins", "kind": "alarm", "deleted": False, "open": True},
    ]
    assert alarm["text"] == ""
    assert _create(alarms, target=one["uid"])["targets"][0]["uid"] == one["uid"]  # das frühere Feld geht weiter
    refused = alarms.client.post(
        f"{API}/alarms",
        json={"project": _project(alarms), "fields": {"text": "x", "at": AT, "targets": ["gibt-es-nicht"]}},
    )
    assert refused.status_code == 404


def test_a_text_is_required_only_without_targets(alarms: Env) -> None:
    refused = alarms.client.post(
        f"{API}/alarms", json={"project": _project(alarms), "fields": {"at": AT, "targets": []}}
    )
    assert refused.status_code == 422


def test_a_label_needs_the_project_to_be_resolved(alarms: Env) -> None:
    alarm = _create(alarms)
    found = alarms.client.get(f"{API}/alarms/{alarm['label']}", params={"project": _project(alarms)})
    assert found.json()["uid"] == alarm["uid"]
    assert alarms.client.get(f"{API}/alarms/{alarm['label']}").status_code == 422


def test_there_is_exactly_one_timer_on_the_earliest_waiting_alarm(alarms: Env) -> None:
    _create(alarms, at="2026-10-17T10:00:00Z")
    early = _create(alarms, at="2026-10-16T13:00:00Z")
    assert _pending(alarms) == datetime.fromisoformat("2026-10-16T13:00:00+00:00")

    assert _post(alarms, early, "finish").status_code == 200
    assert _pending(alarms) == datetime.fromisoformat("2026-10-17T10:00:00+00:00")


def test_firing_marks_due_alarms_publishes_the_event_and_sets_the_next_timer(alarms: Env) -> None:
    seen = _events(alarms)
    first = _create(alarms, "Erster", at="2026-10-16T13:00:00Z")
    _create(alarms, "Zweiter", at="2026-10-18T13:00:00Z")
    alarms.clock.advance(timedelta(hours=2))

    fired = alarms.alarms.alarms.fire()

    assert fired == [first["uid"]]
    due = [e for e in seen if e.topic == "alarms.due"]
    assert len(due) == 1 and due[0].payload == {"uids": [first["uid"]]} and due[0].public is True
    shown = alarms.client.get(f"{API}/alarms/{first['uid']}").json()
    assert shown["status"] == "Due" and shown["version"] > first["version"]
    assert _pending(alarms) == datetime.fromisoformat("2026-10-18T13:00:00+00:00")
    assert alarms.alarms.alarms.fire() == []  # ein zweites Mal meldet sich nichts


def test_due_only_lists_the_alarms_that_have_fired(alarms: Env) -> None:
    quiet, loud = (
        _create(alarms, "Leise", at="2026-10-18T13:00:00Z"),
        _create(alarms, "Laut", at="2026-10-16T12:30:00Z"),
    )
    alarms.clock.advance(timedelta(hours=1))
    alarms.alarms.alarms.fire()

    due = alarms.client.get(f"{API}/alarms", params={"due_only": True}).json()
    everything = alarms.client.get(f"{API}/alarms").json()

    assert [a["uid"] for a in due] == [loud["uid"]]
    assert [a["uid"] for a in everything] == [loud["uid"], quiet["uid"]]  # nach Zeitpunkt


def test_alarms_missed_while_the_viewer_was_down_are_caught_up_at_the_start(alarms: Env) -> None:
    missed = _create(alarms, at="2026-10-16T13:00:00Z")
    alarms.clock.advance(timedelta(days=3))

    alarms.alarms.alarms.reschedule()  # so baut das Plugin beim Start den Termin
    assert _pending(alarms) == datetime.fromisoformat("2026-10-16T13:00:00+00:00")  # vergangen: wird sofort ausgeführt
    alarms.alarms.alarms.fire()

    assert alarms.client.get(f"{API}/alarms/{missed['uid']}").json()["status"] == "Due"


def test_snoozing_waits_for_the_new_time_and_fires_again_then(alarms: Env) -> None:
    alarm = _create(alarms, at="2026-10-16T12:30:00Z")
    alarms.clock.advance(timedelta(hours=1))
    alarms.alarms.alarms.fire()
    due = alarms.client.get(f"{API}/alarms/{alarm['uid']}").json()

    snoozed = _post(alarms, due, "snooze").json()  # Standard: eine Stunde

    assert (snoozed["status"], snoozed["snoozed_until"][:16]) == ("Snoozed", "2026-10-16T14:00")
    assert _pending(alarms) == datetime.fromisoformat("2026-10-16T14:00:00+00:00")
    alarms.clock.advance(timedelta(hours=1))
    alarms.alarms.alarms.fire()
    assert alarms.client.get(f"{API}/alarms/{alarm['uid']}").json()["status"] == "Due"


def test_snoozing_until_a_given_time_in_the_future_only(alarms: Env) -> None:
    alarm = _create(alarms)
    assert (
        _post(alarms, alarm, "snooze", until="2026-10-17T07:00:00Z")
        .json()["snoozed_until"]
        .startswith("2026-10-17T07:00")
    )
    again = alarms.client.get(f"{API}/alarms/{alarm['uid']}").json()
    refused = _post(alarms, again, "snooze", until="2026-10-01T07:00:00Z")
    assert (refused.status_code, refused.json()["code"]) == (400, "snooze_in_past")


def test_finishing_ends_the_alarm_and_a_new_time_wakes_it_again(alarms: Env) -> None:
    alarm = _create(alarms)
    done = _post(alarms, alarm, "finish").json()
    assert done["status"] == "Done" and done["done_at"].startswith("2026-10-16T12:00:00")
    assert _pending(alarms) == alarms.clock.now() + timedelta(hours=24)  # dann wird er aufgeräumt
    assert _post(alarms, done, "snooze").json()["code"] == "alarm_done"

    again = alarms.client.put(
        f"{API}/alarms/{alarm['uid']}", json={"version": done["version"], "fields": {"at": "2026-10-20T07:00:00Z"}}
    )

    assert again.json()["status"] == "Pending" and _pending(alarms) == datetime.fromisoformat(
        "2026-10-20T07:00:00+00:00"
    )


def test_updating_changes_text_and_target_and_checks_the_version(alarms: Env) -> None:
    alarm = _create(alarms)
    changed = alarms.client.put(
        f"{API}/alarms/{alarm['uid']}", json={"version": alarm["version"], "fields": {"text": "Neu", "targets": []}}
    )
    assert changed.status_code == 200 and changed.json()["text"] == "Neu"
    stale = alarms.client.put(
        f"{API}/alarms/{alarm['uid']}", json={"version": alarm["version"], "fields": {"text": "Alt"}}
    )
    assert (stale.status_code, stale.json()["code"]) == (409, "version_conflict")


def test_an_alarm_in_the_trash_stops_waiting_and_comes_back_waiting(alarms: Env) -> None:
    alarm = _create(alarms)
    deleted = alarms.client.request(
        "DELETE", f"/api/workspace/elements/{alarm['uid']}", params={"version": alarm["version"]}
    )
    assert deleted.status_code == 200
    assert _pending(alarms) is None
    assert alarms.client.get(f"{API}/alarms").json() == []
    assert (
        alarms.client.put(
            f"{API}/alarms/{alarm['uid']}", json={"version": alarm["version"] + 1, "fields": {"text": "x"}}
        ).json()["code"]
        == "alarm_deleted"
    )

    restored = alarms.client.post("/api/workspace/trash/restore", json={"uids": [alarm["uid"]]})

    assert restored.status_code == 200
    assert _pending(alarms) == datetime.fromisoformat("2026-10-16T14:00:00+00:00")


# --- Erinnerung an Elemente: erlöschen, zurückkehren, rückgängig, aufräumen -------------------------------------


def _task(env: Env, title: str) -> dict[str, Any]:
    fields = {"title": title, "area": "A", "goal": "G", "completion_criteria": "C"}
    response = env.client.post("/api/backlog/items", json={"project": _project(env), "type": "Task", "fields": fields})
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _status(env: Env, item: dict[str, Any], status: str) -> dict[str, Any]:
    body: dict[str, Any] = {"version": item["version"], "fields": {"status": status}}
    if status in ("Completed", "Rejected"):
        body["resolution"] = "ok"
    response = env.client.put(f"/api/backlog/items/{item['uid']}", json=body)
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def _get(env: Env, alarm: dict[str, Any]) -> dict[str, Any]:
    return env.client.get(f"{API}/alarms/{alarm['uid']}").json()  # type: ignore[no-any-return]


def test_an_alarm_expires_when_all_its_elements_are_closed_and_comes_back_when_one_opens(full: Env) -> None:
    one, two = _task(full, "Eins"), _task(full, "Zwei")
    alarm = _create(full, "", targets=[one["uid"], two["uid"]])

    one = _status(full, one, "Completed")
    partly = _get(full, alarm)
    assert partly["status"] == "Pending" and [t["open"] for t in partly["targets"]] == [False, True]

    two = _status(full, two, "Rejected")
    expired = _get(full, alarm)
    assert (expired["status"], expired["done_at"][:16]) == ("Expired", "2026-10-16T12:00")
    assert expired["purge_at"][:16] == "2026-10-17T12:00"
    assert _post(full, expired, "reopen").json()["code"] == "alarm_not_done"  # zurück nur über ein offenes Element

    _status(full, two, "In progress")
    back = _get(full, alarm)
    assert (back["status"], back["done_at"]) == ("Pending", None)


def test_a_deleted_element_counts_as_closed(full: Env) -> None:
    item = _task(full, "Weg")
    alarm = _create(full, targets=[item["uid"]])
    deleted = full.client.delete(f"/api/workspace/elements/{item['uid']}", params={"version": item["version"]})
    assert deleted.status_code == 200, deleted.text
    assert _get(full, alarm)["status"] == "Expired"


def test_a_free_alarm_never_expires(full: Env) -> None:
    alarm = _create(full, "Telefonieren")
    full.alarms.alarms.follow()
    assert _get(full, alarm)["status"] == "Pending"


def test_reopen_takes_back_finish_and_a_missed_time_makes_it_due(alarms: Env) -> None:
    alarm = _create(alarms)
    done = _post(alarms, alarm, "finish").json()
    alarms.clock.advance(timedelta(hours=3))  # die Zeit (14:00) ist vorbei
    reopened = _post(alarms, done, "reopen").json()
    assert (reopened["status"], reopened["done_at"]) == ("Due", None)


def test_finished_alarms_are_purged_a_day_later_without_trash(alarms: Env) -> None:
    keep = _create(alarms, "Bleibt", at="2026-10-30T09:00:00Z")
    alarm = _create(alarms)
    _post(alarms, alarm, "finish")
    alarms.clock.advance(timedelta(hours=23))
    assert alarms.alarms.alarms.purge() == []
    alarms.clock.advance(timedelta(hours=1))

    assert alarms.alarms.alarms.purge() == [alarm["uid"]]
    assert alarms.client.get(f"{API}/alarms/{alarm['uid']}").status_code == 404
    assert alarms.client.get("/api/workspace/trash").json() == []
    assert [a["uid"] for a in alarms.client.get(f"{API}/alarms").json()] == [keep["uid"]]

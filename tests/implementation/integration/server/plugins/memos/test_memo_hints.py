from __future__ import annotations

from typing import Any

from memos_api import (
    NOTES,
    decide,
    item,
    link,
    links,
    memo,
    new_item,
    new_memo,
    set_status,
)
from workspace_env import Env


def _referencing(env: Env) -> tuple[dict[str, Any], dict[str, Any]]:
    entry, target = new_memo(env, "Verweist"), new_item(env)
    link(env, entry["uid"], target["uid"])
    return entry, target


def _complete(env: Env, target: dict[str, Any]) -> None:
    for status in ("In progress", "Awaiting confirmation"):
        set_status(env, target, status)
    set_status(env, target, "Completed", "Fertig")


def _hint(env: Env, uid: str) -> dict[str, Any]:
    hints = memo(env, uid)["hints"]
    assert len(hints) == 1, hints
    return hints[0]  # type: ignore[no-any-return]


def test_a_completed_item_tells_the_memos_that_refer_to_it(memos: Env) -> None:
    entry, target = _referencing(memos)

    _complete(memos, target)

    shown = memo(memos, entry["uid"])
    assert (shown["status"], shown["reason"]) == ("due", "hint")
    hint = shown["hints"][0]
    assert (hint["kind"], hint["source"]["uid"], hint["decisions"]) == (
        "item_completed",
        target["uid"],
        ["keep", "detach", "drop", "promote"],
    )


def test_a_rejected_item_tells_them_too_and_in_progress_does_not(memos: Env) -> None:
    entry, target = _referencing(memos)
    set_status(memos, target, "In progress")
    assert memo(memos, entry["uid"])["hints"] == []

    set_status(memos, target, "Rejected", "Nein")

    assert _hint(memos, entry["uid"])["kind"] == "item_rejected"


def test_an_open_hint_of_the_same_cause_stays_the_only_one(memos: Env) -> None:
    entry, target = _referencing(memos)
    _complete(memos, target)
    set_status(memos, target, "In progress")
    set_status(memos, target, "Awaiting confirmation")
    set_status(memos, target, "Completed", "Noch einmal")

    assert len(memo(memos, entry["uid"])["hints"]) == 1


def test_a_memo_without_a_reference_or_in_the_archive_is_not_told(memos: Env) -> None:
    plain, target = new_memo(memos, "Ohne Verweis"), new_item(memos)
    closed = new_memo(memos, "Abgeschlossen")
    link(memos, closed["uid"], target["uid"])
    memos.client.post(f"{NOTES}/memos/{closed['uid']}/finish", json={"version": closed["version"], "status": "done"})
    link(memos, plain["uid"], target["uid"], "origin")

    _complete(memos, target)

    assert memo(memos, plain["uid"])["hints"] == []
    assert memo(memos, closed["uid"])["hints"] == []


def test_a_deleted_item_tells_the_memos(memos: Env) -> None:
    entry, target = _referencing(memos)

    memos.client.request("DELETE", f"/api/workspace/elements/{target['uid']}", params={"version": target["version"]})

    assert _hint(memos, entry["uid"])["kind"] == "item_deleted"


def test_a_retyped_item_tells_the_memos(memos: Env) -> None:
    entry, target = _referencing(memos)
    story = new_item(memos, "Story")
    memos.client.put(
        f"/api/backlog/items/{target['uid']}",
        json={"version": target["version"], "fields": {"parent": story["uid"]}, "resolution": None},
    )
    current = item(memos, target["uid"])
    retyped = memos.client.post(
        f"/api/backlog/items/{target['uid']}/retype", json={"version": current["version"], "type": "Story"}
    )
    assert retyped.status_code == 200, retyped.text

    assert any(n["kind"] == "item_retyped" for n in memo(memos, entry["uid"])["hints"])


def test_keep_moves_the_review_date_and_decides_the_hint(memos: Env) -> None:
    entry, target = _referencing(memos)
    _complete(memos, target)
    hint = _hint(memos, entry["uid"])

    decided = decide(memos, hint["uid"], "keep")

    assert decided.status_code == 200, decided.text
    result = decided.json()
    assert result["memo"]["hints"] == [] and result["memo"]["status"] == "waiting"
    assert result["memo"]["review_at"].startswith("2026-11-15")


def test_detach_removes_the_reference_to_the_item(memos: Env) -> None:
    entry, target = _referencing(memos)
    _complete(memos, target)

    decided = decide(memos, _hint(memos, entry["uid"])["uid"], "detach")

    assert decided.status_code == 200, decided.text
    assert links(memos, entry["uid"])["outgoing"] == []
    assert decided.json()["memo"]["status"] == "waiting"


def test_drop_archives_the_memo_and_decides_the_hint(memos: Env) -> None:
    entry, target = _referencing(memos)
    _complete(memos, target)

    decided = decide(memos, _hint(memos, entry["uid"])["uid"], "drop").json()

    assert (decided["memo"]["status"], decided["memo"]["archived"], decided["memo"]["hints"]) == ("dropped", True, [])


def test_a_decision_must_fit_the_side_and_a_hint_is_decided_once(memos: Env) -> None:
    entry, target = _referencing(memos)
    _complete(memos, target)
    uid = _hint(memos, entry["uid"])["uid"]

    assert decide(memos, uid, "acknowledge").status_code == 422
    assert decide(memos, uid, "keep").status_code == 200
    again = decide(memos, uid, "keep")
    assert (again.status_code, again.json()["code"]) == (400, "hint_decided")
    assert decide(memos, "gibt-es-nicht", "keep").status_code == 404


def test_a_failing_decision_leaves_the_hint_open(memos: Env) -> None:
    entry, target = _referencing(memos)
    _complete(memos, target)
    uid = _hint(memos, entry["uid"])["uid"]

    refused = decide(memos, uid, "promote", type="Task", fields={})

    assert refused.status_code in (400, 422)
    assert _hint(memos, entry["uid"])["uid"] == uid
    assert memo(memos, entry["uid"])["stored_status"] == "waiting"


def test_promote_as_a_decision_creates_the_item_and_decides_the_hint(memos: Env) -> None:
    entry, target = _referencing(memos)
    _complete(memos, target)
    uid = _hint(memos, entry["uid"])["uid"]

    decided = decide(
        memos, uid, "promote", type="Task", fields={"goal": "Ziel", "completion_criteria": "K"}
    )

    assert decided.status_code == 200, decided.text
    assert decided.json()["memo"]["status"] == "promoted"
    assert decided.json()["hint"]["decisions"] == ["keep", "detach", "drop", "promote"]
    origin = [entry for entry in links(memos, entry["uid"])["outgoing"] if entry["role"] == "origin"]
    assert len(origin) == 1


def test_a_dropped_memo_tells_the_items_it_refers_to_and_they_can_acknowledge(memos: Env) -> None:
    entry, target = _referencing(memos)
    dropped = memos.client.post(
        f"{NOTES}/memos/{entry['uid']}/finish", json={"version": entry["version"], "status": "dropped"}
    )
    assert dropped.status_code == 200

    listed = memos.client.get(f"{NOTES}/items/{target['uid']}/hints").json()

    assert [(n["kind"], n["source"]["uid"], n["decisions"]) for n in listed] == [
        ("memo_dropped", entry["uid"], ["acknowledge"])
    ]
    decided = decide(memos, listed[0]["uid"], "acknowledge")
    assert decided.status_code == 200 and decided.json()["memo"] is None
    assert memos.client.get(f"{NOTES}/items/{target['uid']}/hints").json() == []


def test_a_done_memo_tells_nobody(memos: Env) -> None:
    entry, target = _referencing(memos)

    memos.client.post(f"{NOTES}/memos/{entry['uid']}/finish", json={"version": entry["version"], "status": "done"})

    assert memos.client.get(f"{NOTES}/items/{target['uid']}/hints").json() == []


def test_item_hints_can_be_asked_by_label_with_the_project(memos: Env) -> None:
    entry, target = _referencing(memos)
    memos.client.post(f"{NOTES}/memos/{entry['uid']}/finish", json={"version": entry["version"], "status": "dropped"})
    project_uid = str(memos.general()["uid"])

    by_label = memos.client.get(f"{NOTES}/items/{target['label']}/hints", params={"project": project_uid})

    assert len(by_label.json()) == 1
    assert memos.client.get(f"{NOTES}/items/gibt-es-nicht/hints").status_code == 404

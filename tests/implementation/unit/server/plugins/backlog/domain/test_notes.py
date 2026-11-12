from __future__ import annotations

import json
from pathlib import Path

import pytest
from backlog_fixtures import item
from viewer.plugins.backlog.domain.notes import (
    Entry,
    NotesParts,
    NotesWithoutEntries,
    Stamp,
    assemble,
    canonical,
    checksum,
    entry_text,
    has_state_section,
    hints,
    history_rewritten,
    replaced_by_text,
    split,
    split_lossless,
    stamp_line,
    stamped,
    state_of,
    title_of,
)

VECTORS = json.loads(
    (Path(__file__).resolve().parents[6] / "fixtures" / "notes-state" / "checksum.json").read_text(encoding="utf-8")
)["vectors"]

TITLE = "STORY-001 — Login"

PLAIN = """# STORY-001 — Login

## 2026-10-01 — Erstes Thema

### Discussed

- a

## 2026-10-02 — Zweites Thema

### Decided

- b
"""

WITH_STATE = """# STORY-001 — Login

## State

- Goal/Status: läuft
- Open:
  - x (2026-10-02)

State confirmed after entry 2026-10-02 — Zweites Thema (0123456789ab)

## 2026-10-01 — Erstes Thema

- a

## 2026-10-02 — Zweites Thema

- b
"""


def test_notes_without_state_split_into_preamble_and_entries() -> None:
    parts = split(PLAIN)

    assert parts.preamble == "\n"
    assert parts.state == ""
    assert parts.stamp is None
    assert [(e.day, e.topic) for e in parts.entries] == [
        ("2026-10-01", "Erstes Thema"),
        ("2026-10-02", "Zweites Thema"),
    ]
    assert parts.entries[0].body == "\n### Discussed\n\n- a\n\n"
    assert entry_text(parts.entries[1]) == "## 2026-10-02 — Zweites Thema\n\n### Decided\n\n- b\n"


def test_notes_without_state_round_trip_unchanged() -> None:
    assert assemble(TITLE, split(PLAIN)) == PLAIN


def test_the_title_line_always_comes_from_the_item() -> None:
    assert assemble("TASK-020 — Neu", split(PLAIN)) == PLAIN.replace("# STORY-001 — Login", "# TASK-020 — Neu")
    assert title_of(item("s", label="STORY-001", title="Login")) == TITLE


def test_text_without_title_line_loses_nothing() -> None:
    body = PLAIN.split("\n", 1)[1]

    assert assemble(TITLE, split(body)) == PLAIN
    assert assemble(TITLE, split("## 2026-10-01 — A\n- a\n")) == f"# {TITLE}\n## 2026-10-01 — A\n- a\n"


def test_the_state_and_its_stamp_are_read() -> None:
    parts = split(WITH_STATE)

    assert parts.state == "- Goal/Status: läuft\n- Open:\n  - x (2026-10-02)"
    assert parts.stamp == Stamp("2026-10-02", "Zweites Thema", "0123456789ab")
    assert len(parts.entries) == 2
    assert parts.preamble == "\n"


def test_notes_with_state_are_written_in_the_fixed_layout() -> None:
    assert assemble(TITLE, split(WITH_STATE)) == WITH_STATE
    parts = NotesParts("", "- Goal/Status: neu", None, (Entry("2026-10-01", "A", "\n- a\n"),))
    text = assemble(TITLE, parts)

    assert text == f"# {TITLE}\n\n## State\n\n- Goal/Status: neu\n\n## 2026-10-01 — A\n\n- a\n"
    assert assemble(TITLE, split(text)) == text


def test_an_invalid_stamp_line_stays_part_of_the_state() -> None:
    text = WITH_STATE.replace("(0123456789ab)", "(xyz)")
    parts = split(text)

    assert parts.stamp is None
    assert parts.state.endswith("State confirmed after entry 2026-10-02 — Zweites Thema (xyz)")


def test_a_stamp_line_is_rendered_in_the_shared_format() -> None:
    assert stamp_line(Stamp("2026-10-02", "Zweites Thema", "0123456789ab")) == (
        "State confirmed after entry 2026-10-02 — Zweites Thema (0123456789ab)"
    )


def test_a_preamble_before_the_entries_is_kept() -> None:
    text = "# STORY-001 — Login\n\n## Summary\n\nAlte Kurzfassung.\n\n## 2026-10-01 — A\n\n- a\n"
    parts = split(text)

    assert parts.preamble == "\n## Summary\n\nAlte Kurzfassung.\n\n"
    assert assemble(TITLE, parts) == text


def test_a_preamble_comes_before_the_state() -> None:
    text = "# STORY-001 — Login\n\n## Summary\n\nAlt.\n\n## State\n\n- Goal/Status: x\n\n## 2026-10-01 — A\n\n- a\n"
    parts = split(text)

    assert parts.preamble == "\n## Summary\n\nAlt.\n\n"
    assert parts.state == "- Goal/Status: x"
    assert assemble(TITLE, parts) == text


def test_notes_without_dated_entries_are_all_preamble() -> None:
    text = "# STORY-001 — Login\n\n## Discussed (2026-09-25)\n\n- a\n"
    parts = split(text)

    assert parts.entries == ()
    assert parts.preamble == "\n## Discussed (2026-09-25)\n\n- a\n"
    assert assemble(TITLE, parts) == text


def test_a_state_heading_after_the_first_entry_belongs_to_that_entry() -> None:
    text = "# STORY-001 — Login\n\n## 2026-10-01 — A\n\n## State\n\n- nicht der Kopf\n"
    parts = split(text)

    assert parts.state == ""
    assert parts.entries[0].body == "\n## State\n\n- nicht der Kopf\n"
    assert assemble(TITLE, parts) == text


def test_entry_headings_need_the_exact_pattern() -> None:
    text = "# T\n\n## 2026-10-01 - Bindestrich\n\n## 2026-10-1 — kurz\n\n## 2026-10-01 — Richtig\n"
    parts = split(text)

    assert [e.topic for e in parts.entries] == ["Richtig"]


def test_text_without_final_newline_round_trips() -> None:
    text = "# STORY-001 — Login\n\n## 2026-10-01 — A\n\n- a"

    assert assemble(TITLE, split(text)) == text


def test_empty_text_has_no_parts() -> None:
    assert split("") == NotesParts("", "", None, ())


def test_split_lossless_keeps_text_that_does_not_round_trip_as_preamble() -> None:
    crlf = "# T\r\n\r\n## 2026-10-01 — A\r\n\r\n- a\r\n"

    assert split_lossless(PLAIN) == split(PLAIN)
    assert split_lossless(crlf) == NotesParts("\r\n## 2026-10-01 — A\r\n\r\n- a\r\n", "", None, ())
    assert split_lossless(WITH_STATE) == split(WITH_STATE)


def test_replacing_by_text_keeps_the_state_when_the_text_has_none() -> None:
    old = split(WITH_STATE)
    new = replaced_by_text(old, PLAIN)

    assert new.state == old.state and new.stamp == old.stamp
    assert [e.topic for e in new.entries] == ["Erstes Thema", "Zweites Thema"]


def test_replacing_by_text_takes_a_new_state_but_never_its_stamp_line() -> None:
    old = split(WITH_STATE)
    text = WITH_STATE.replace("läuft", "fertig").replace("0123456789ab", "ffffffffffff")
    new = replaced_by_text(old, text)

    assert "fertig" in new.state
    assert new.stamp == old.stamp
    assert has_state_section(text) and not has_state_section(PLAIN)


@pytest.mark.parametrize("vector", VECTORS, ids=[v["name"] for v in VECTORS])
def test_the_checksum_matches_the_shared_vectors(vector: dict[str, str]) -> None:
    entries = split(vector["protocol"]).entries

    assert canonical(entries) == vector["canonical"]
    assert checksum(entries) == vector["checksum"]


def _entries() -> tuple[Entry, ...]:
    return split(PLAIN).entries


def test_the_state_is_missing_stale_or_current() -> None:
    entries = _entries()
    current = Stamp("2026-10-02", "Zweites Thema", checksum(entries))

    assert state_of(NotesParts("\n", "", None, entries)) == "missing"
    assert state_of(NotesParts("\n", "  \n", current, entries)) == "missing"
    assert state_of(NotesParts("\n", "- Goal/Status: x", None, entries)) == "stale"
    assert state_of(NotesParts("\n", "- Goal/Status: x", current, entries[:1])) == "stale"
    assert state_of(NotesParts("\n", "- Goal/Status: x", current, entries)) == "current"


def test_stamping_names_the_last_entry_and_the_current_checksum() -> None:
    parts = stamped(NotesParts("\n", "- Goal/Status: x", None, _entries()))

    assert parts.stamp == Stamp("2026-10-02", "Zweites Thema", checksum(_entries()))
    assert state_of(parts) == "current"
    with pytest.raises(NotesWithoutEntries):
        stamped(NotesParts("\n", "- Goal/Status: x", None, ()))


def _decided(count: int) -> str:
    rows = "".join(f"  - Beschluss {n} (2026-10-01)\n" for n in range(count))
    return f"- Goal/Status: x\n- Next step: y\n- Open: -\n- Decided:\n{rows}- References: Spec\n  - nicht gezählt"


def test_a_long_state_gives_a_hint_from_16_decisions_on() -> None:
    codes = {
        count: [
            h.code for h in hints(None, stamped(NotesParts("\n", _decided(count), None, _entries())), rewritten=False)
        ]
        for count in (15, 16)
    }

    assert codes == {15: [], 16: ["notes_state_long"]}


def test_a_stale_or_missing_state_gives_a_hint() -> None:
    assert [h.code for h in hints(None, NotesParts("\n", "", None, _entries()), rewritten=False)] == [
        "notes_state_stale"
    ]
    assert [h.code for h in hints(None, NotesParts("\n", "- x", None, _entries()), rewritten=False)] == [
        "notes_state_stale",
        "notes_state_malformed",
    ]


def test_a_head_with_wrong_markers_is_kept_but_gets_a_hint_with_the_expected_form() -> None:
    def codes(state: str) -> list[str]:
        return [h.code for h in hints(None, stamped(NotesParts("\n", state, None, _entries())), rewritten=False)]

    valid = "- Goal/Status: a\n- Next step: b\n- Open: -\n- Decided:\n  - c (2026-10-01)\n- References: -"
    german = "- Ziel: a\n- Nächster Schritt: b\n- Offen: -\n- Beschlossen: -\n- Verweise: -"
    order = "- Next step: b\n- Goal/Status: a\n- Open: -\n- Decided: -\n- References: -"
    missing = "- Goal/Status: a\n- Next step: b\n- Open: -\n- Decided: -"
    unmarked = "Entschieden: a\nOffen: b"

    assert codes(valid) == []
    assert [codes(text) for text in (german, order, missing, unmarked)] == [["notes_state_malformed"]] * 4
    found = hints(None, stamped(NotesParts("\n", german, None, _entries())), rewritten=False)
    message = next(h.message for h in found if h.code == "notes_state_malformed")
    assert "'- Goal/Status:', '- Next step:', '- Open:', '- Decided:', '- References:'" in message


def test_rewriting_an_older_entry_is_noticed_but_appending_is_not() -> None:
    before = NotesParts("\n", "", None, _entries())
    appended = NotesParts("\n", "", None, (*_entries(), Entry("2026-10-03", "Neu", "\n- n\n")))
    changed = NotesParts("\n", "", None, (Entry("2026-10-01", "Erstes Thema", "\n- anders\n"), _entries()[1]))
    removed = NotesParts("\n", "", None, _entries()[1:])

    assert not history_rewritten(before, appended)
    assert history_rewritten(before, changed) and history_rewritten(before, removed)
    assert "notes_history_rewritten" in [h.code for h in hints(before, changed, rewritten=True)]
    assert "notes_history_rewritten" not in [h.code for h in hints(before, changed, rewritten=False)]


def test_line_endings_and_trailing_blank_lines_do_not_count_as_a_rewrite() -> None:
    before = NotesParts("\n", "", None, (Entry("2026-10-01", "A", "\n- a\n"),))
    crlf = NotesParts(
        "\n", "", None, (Entry("2026-10-01", "A", "\r\n- a\r\n\r\n"), Entry("2026-10-02", "B", "\n- b\n"))
    )

    assert not history_rewritten(before, crlf)


def test_the_german_state_heading_is_no_longer_recognised() -> None:
    parts = split("# STORY-001 — Login\n\n## Stand\n\n- Ziel/Status: x\n\n## 2026-10-01 — A\n\n- a\n")

    assert parts.state == "" and "## Stand" in parts.preamble

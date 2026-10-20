from __future__ import annotations

from backlog_fixtures import item
from viewer.plugins.backlog.domain.notes import (
    Entry,
    NotesParts,
    Stamp,
    assemble,
    entry_text,
    has_state_section,
    replaced_by_text,
    split,
    split_lossless,
    stamp_line,
    title_of,
)

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

## Stand

- Ziel/Status: läuft
- Offen:
  - x (2026-10-02)

Stand bestätigt nach Eintrag 2026-10-02 — Zweites Thema (0123456789ab)

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

    assert parts.state == "- Ziel/Status: läuft\n- Offen:\n  - x (2026-10-02)"
    assert parts.stamp == Stamp("2026-10-02", "Zweites Thema", "0123456789ab")
    assert len(parts.entries) == 2
    assert parts.preamble == "\n"


def test_notes_with_state_are_written_in_the_fixed_layout() -> None:
    assert assemble(TITLE, split(WITH_STATE)) == WITH_STATE
    parts = NotesParts("", "- Ziel/Status: neu", None, (Entry("2026-10-01", "A", "\n- a\n"),))
    text = assemble(TITLE, parts)

    assert text == f"# {TITLE}\n\n## Stand\n\n- Ziel/Status: neu\n\n## 2026-10-01 — A\n\n- a\n"
    assert assemble(TITLE, split(text)) == text


def test_an_invalid_stamp_line_stays_part_of_the_state() -> None:
    text = WITH_STATE.replace("(0123456789ab)", "(xyz)")
    parts = split(text)

    assert parts.stamp is None
    assert parts.state.endswith("Stand bestätigt nach Eintrag 2026-10-02 — Zweites Thema (xyz)")


def test_a_stamp_line_is_rendered_in_the_shared_format() -> None:
    assert stamp_line(Stamp("2026-10-02", "Zweites Thema", "0123456789ab")) == (
        "Stand bestätigt nach Eintrag 2026-10-02 — Zweites Thema (0123456789ab)"
    )


def test_a_preamble_before_the_entries_is_kept() -> None:
    text = "# STORY-001 — Login\n\n## Summary\n\nAlte Kurzfassung.\n\n## 2026-10-01 — A\n\n- a\n"
    parts = split(text)

    assert parts.preamble == "\n## Summary\n\nAlte Kurzfassung.\n\n"
    assert assemble(TITLE, parts) == text


def test_a_preamble_comes_before_the_state() -> None:
    text = "# STORY-001 — Login\n\n## Summary\n\nAlt.\n\n## Stand\n\n- Ziel/Status: x\n\n## 2026-10-01 — A\n\n- a\n"
    parts = split(text)

    assert parts.preamble == "\n## Summary\n\nAlt.\n\n"
    assert parts.state == "- Ziel/Status: x"
    assert assemble(TITLE, parts) == text


def test_notes_without_dated_entries_are_all_preamble() -> None:
    text = "# STORY-001 — Login\n\n## Discussed (2026-09-25)\n\n- a\n"
    parts = split(text)

    assert parts.entries == ()
    assert parts.preamble == "\n## Discussed (2026-09-25)\n\n- a\n"
    assert assemble(TITLE, parts) == text


def test_a_state_heading_after_the_first_entry_belongs_to_that_entry() -> None:
    text = "# STORY-001 — Login\n\n## 2026-10-01 — A\n\n## Stand\n\n- nicht der Kopf\n"
    parts = split(text)

    assert parts.state == ""
    assert parts.entries[0].body == "\n## Stand\n\n- nicht der Kopf\n"
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

"""Platzhalter im Fließtext: nur ganze IDs werden durch das vergebene Label ersetzt."""

from __future__ import annotations

from viewer.core.domain.sync import MirrorEntry, replace_ids, text_labels

LABELS = {"NEW-route": "STORY-021", "NEW-route-2": "STORY-022", "new-idea": "MEMO-005"}


def test_whole_ids_are_replaced() -> None:
    assert replace_ids("Siehe NEW-route und `NEW-route`.", LABELS) == "Siehe STORY-021 und `STORY-021`."
    assert replace_ids("note:new-idea (NEW-route)", LABELS) == "note:MEMO-005 (STORY-021)"


def test_longer_or_embedded_ids_stay_and_the_longest_key_wins() -> None:
    assert replace_ids("NEW-route-2 und NEW-route-3", LABELS) == "STORY-022 und NEW-route-3"
    assert replace_ids("XNEW-route, NEW-routes, STORY-021", LABELS) == "XNEW-route, NEW-routes, STORY-021"


def test_text_labels_leave_out_document_placeholders_and_identities() -> None:
    mapping = {"NEW-a": "STORY-001", "NEW-a/notes": "STORY-001_notes.md", "X": "X"}
    assert text_labels(mapping) == {"NEW-a": "STORY-001"}


def test_map_text_rewrites_nested_strings_and_keeps_untouched_entries() -> None:
    entry = MirrorEntry("item", None, {"goal": "Wie NEW-route", "list": ["NEW-route", 3], "n": 1}, placeholder="NEW-x")
    mapped = entry.map_text(LABELS)
    assert mapped.fields == {"goal": "Wie STORY-021", "list": ["STORY-021", 3], "n": 1}
    plain = MirrorEntry("item", None, {"goal": "nichts"})
    assert plain.map_text(LABELS) is plain

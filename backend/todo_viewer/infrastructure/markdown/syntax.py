"""Markdown syntax of the supported backlog formats.

1. Structured backlog format ("backlog format version N"):
     - `STORY-001` **Title**
       - Type: Story.
       - Parent: `EPIC-001`.
       - Status: Open.
       - Goal: ... (continuation lines indented by four spaces)
   A backlog folder holds `TODO.md` (active items) and `archive.md`
   (Completed/Rejected items); both use this syntax.
2. Fallback: plain nested markdown checklists ("- [ ] Task", "- [x] Done").
"""
from __future__ import annotations

import re

TODO_FILE = "TODO.md"
ARCHIVE_FILE = "archive.md"

ENTRY_HEADER_RE = re.compile(r"^- `([A-Za-z0-9_.\-]+)`\s+\*\*(.+?)\*\*\s*$", re.MULTILINE)
FIELD_RE = re.compile(r"^ {2}- ([A-Za-z][A-Za-z ]*?):\s?(.*)$")
CHECKBOX_RE = re.compile(r"^(\s*)-\s\[( |x|X)\]\s+(.*)$")
WORK_ITEMS_HEADER_RE = re.compile(r"^## Work items\s*$", re.MULTILINE)
NO_ENTRIES_LINE = "No entries."
# Any structured backlog format version ("... backlog format version 2",
# "Claude_Harness backlog format version 1", ...); the entry syntax is identical.
BACKLOG_MARKER_RE = re.compile(r"backlog\s+format\s+version\s+\d+", re.IGNORECASE)

# Labels used when a field has to be inserted into an entry.
FIELD_LABELS = {
    "status": "Status",
    "priority": "Priority",
    "required_for_parent": "Required for parent",
    "resolution": "Resolution",
}


def field_key(label: str) -> str:
    """'Required for parent' -> 'required_for_parent'."""
    return label.strip().lower().replace(" ", "_")

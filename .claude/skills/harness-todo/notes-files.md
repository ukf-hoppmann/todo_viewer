# Notes and topics as files

For `[todo].backend = "files"` (also the effective backend of a cloud session).
With `api` the notes live in the ToDo-Viewer instead: [notes.md](notes.md).
A note is a thought with a review date, not work (same meaning as in
[notes.md](notes.md), including note versus backlog item). Backlog work
belongs to [SKILL.md](SKILL.md). Alarms exist only in the ToDo-Viewer
(`api`): in this mode say so when the user asks to be reminded at a fixed time,
and offer a note with a review date instead.

## Before you start

1. Read `.claude-harness/config.toml` of the project the work belongs to (with
   subprojects, the session start lists each project and its folder; paths
   below are relative to that folder). If `[modules].todo` is not `true`, these
   rules do not apply — say so and stop.
2. The notes live in `notes/` below the backlog folder (`[todo].path`, default
   `docs/todo/notes/`). Write note texts (summary, long text) in
   `[docs].language`; field names, status values, and roles stay English.
3. The notes are Markdown files in the repository. They are **not private**:
   whoever can read the repository can read them, and in a cloud session they
   reach GitHub with the next push. Say so once before you create the first
   note of a session, and keep secrets and personal data out of them.
4. The ToDo-Viewer reads the folder when it syncs. It assigns the labels and
   `Uid`s and decides what is due by its triggers; you only write files.

## Reading order

1. Get the index first:
   `python3 ".claude-harness/runtime/scripts/notes_files.py" <backlog folder> --index`
   lists `File | Status | Review | Topic | Summary` of every active note. It
   leaves out notes in the trash or archive, the documents of notes, and
   `topics.md`.
2. Pick the notes that fit by their summaries. Only then read a file, and only
   those. Never read all of them.
3. Before creating a note, look at the index for an equivalent one; extend or
   revise it instead of adding a duplicate.

## Due notes

You do not check for due notes on your own and do not announce them. When the
user asks what is due, run `notes_files.py <backlog folder> --due`: it lists
the open notes (`waiting`, `due`, `snoozed`) whose `Review` day or whose
topic's `due` day is today or earlier, with the reason. Without the viewer
nothing else is evaluated: triggers on events (`event` lines) are only known to
the viewer, so say that this list may be incomplete. Read a note's long text
only on request. Afterwards the user decides: look again later (set a new
`Review`), finish it (`Status: done` or `dropped`), or turn it into backlog
work.

## File format (version 2)

The format is the ToDo-Viewer's (its techdoc `interfaces.md`, section file
format version 2, notes and topics). This is what you need to write:

```
# NEW
Summary: <one line>
Status: waiting
Topic: <TOPIC-001 | new:<Name> | empty>
Review: 2026-11-07T08:00:00Z
Mode: any
Triggers:
- event <Project>:<ID> <Status>
- topic_due
Links:
- reference <Project>:<ID>

<long text in Markdown>
```

- **New note:** `notes/new-<short-name>.md` (lowercase letters, digits, `-`),
  first line `# NEW`, no `Uid`, no `Created`/`Updated`. The viewer gives it a
  label on import and renames the file; references to `note:new-…` follow.
- **Existing note** (`NOTE-001.md`, with `Uid`): you may change `Summary`,
  `Review`, `Topic`, `Triggers`, `Links`, `Status` (see below) and the long
  text. Leave the first line, `Uid`, `Created`, `Updated`, `Archived`, and
  `Deleted` alone, and keep the other lines as they are.
- **Status:** `waiting`, `snoozed`, `done`, `dropped`, `promoted`. You set
  `waiting`, `snoozed`, `done`, and `dropped`; `promoted` comes from the
  viewer. `due` is derived by the viewer and never stands in a file; a file
  with `Status: due` is a format error.
- **Topics:** `Topic:` names a label (`TOPIC-001`) or a new topic as
  `new:<Name>`. A new topic needs a line `- NEW | <Name>` in `notes/topics.md`
  (create the file if needed); a child is indented by two spaces below its
  parent. In names, `|` is written `\|`, `\` as `\\`, and a line break as
  `\n`. Existing lines of `topics.md` stay as they are. Put a note into an
  existing topic when one fits and keep the tree shallow.
- **Times** are UTC with a trailing `Z` (`2026-11-07T08:00:00Z`). Turn
  relative dates ("tomorrow morning") into a fixed time with the machine's
  local time zone first, convert to UTC, and name the result with weekday,
  date, and local time in your answer. When the wording is ambiguous ("early"
  can mean 6 or 9 o'clock), ask before creating. The viewer's default review
  period is not known here: ask when the user names none, or leave `Review`
  empty.
- **Triggers:** only `event` (a status of an item) and `topic_due`. A `time`
  line is a format error and makes the viewer refuse the whole sync; reminders
  at a fixed time are alarms and do not exist here. Never write the state
  `[fired …]` or `[already_met]`; it belongs to the viewer.
- **Links** point to items, topics, or other notes as `reference` or `origin`;
  a `trigger` link exists only together with its `event` line. Use labels, not
  uids.
- **Documents** of a note (`new-<name>_notes.md`, `…_spec.md`) hold text
  unchanged; create them only when the user asks for more than the long text.
- **Never** create or edit `counters.md` (it does not exist in version 2),
  assign labels, copy a `Uid`, or rename a note file with a label.

A broken file makes the viewer abort the whole sync (backlog and notes) with
the file and line in the message. The format is checked for you: after a
change below `notes/`, the check at the end of your turn blocks with
`notes/<file>:<line>: <code>: <text>` until the folder is valid, and you can
run it yourself with
`python3 ".claude-harness/runtime/scripts/notes_files.py" <backlog folder> --check`
(exit 1 on errors). Codes are the viewer's: `invalid_value`, `unknown_field`,
`missing_field`, `file_label_mismatch`, `invalid_placeholder`,
`unknown_trigger`, `duplicate_uid`, `duplicate_label`; plus `merge_markers` and
`unreadable`. A notice (`ignored_file`, `document_without_note`) does not
block; it points to a file the viewer does not read, usually a typo in its
name. Fix the file the message names; do not work around the check.

## Back to the viewer

The notes travel with the branch of the session. How they get into the
viewer's database (pull request, pull, sync, conflicts) is described in
[sync-flow.md](sync-flow.md).

## Authority

Without asking: create and revise notes and topics, set links with role
`reference` or `origin`, set triggers the user described, set a new `Review`,
`Status: done`.

Ask first: `Status: dropped`; deleting a note (no question when the request
clearly asks for it): set the `Deleted:` line of its head to the current time
in UTC, never remove the file; deleting a topic (the user also chooses what
happens to its notes). Turning a note into a backlog item or an item into a
note is possible only in the viewer: say so.

Never: remove anything for good, change another project's notes, or touch the
viewer's settings.

## Commit

Notes are files in the repository: commit them with the change they belong to,
or on their own with a message starting `Notes: …` when they stand alone.

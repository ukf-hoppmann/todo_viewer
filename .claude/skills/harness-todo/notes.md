# Notes and topics

A note is a thought with a review date, not work: it has no completion
criteria, only a trigger or a time to look at it again. Backlog work belongs
to [SKILL.md](SKILL.md).

## Before you start

1. Read `.claude-harness/config.toml` of the project the work belongs to (with
   subprojects, the session start lists each project and its folder; paths
   below are relative to that folder). If `[modules].todo` is not `true`,
   these rules do not apply — say so and stop. If the backend is not `api`
   (for example in a cloud session), the notes are files: follow
   [notes-files.md](notes-files.md) instead and ignore the rest of this file.
2. Write note texts (summary, body) in `[docs].language`; field names, status
   values, and roles stay English.
3. Work only through
   `python3 ".claude-harness/runtime/scripts/notes_api.py" [--project <name>] <command>`.
   Commands and inputs: [notes-api.md](notes-api.md); read it before the first call. Notes
   live in the ToDo-Viewer's database, and you never write note files
   yourself; nothing falls back to files. If the project's backlog has a
   mirror in the viewer, the viewer writes the notes into `notes/` below the
   backlog folder: commit that folder with the rest of the backlog (message
   `Backlog: …`) as [SKILL.md](SKILL.md) says. How the mirror travels between
   a cloud session and the viewer: [sync-flow.md](sync-flow.md).
   Notes of another project (`--source <name>`) follow the approval rule of
   the rules of [SKILL.md](SKILL.md) for other projects' backlogs, including `sources`.
4. If the helper exits with code 3 (server not reachable), tell the user and
   ask whether to start the server or stop. Exit code 4 (project not
   registered in the viewer) is handled as in [SKILL.md](SKILL.md).
5. With `api` and no mirror, notes are private as long as they live only in
   the database. With a mirror they are files in the repository, and in a cloud
   session on GitHub: they are then not private (see
   [notes-files.md](notes-files.md)); tell the owner once when you create the
   first note in a project with a mirror. In both cases do not treat them as
   team knowledge and do not copy their content into other checked-in files
   (backlog, daily reports, documentation, commit messages).

## Note, backlog item, or alarm

- **Backlog item:** work with a completion definition. Use [SKILL.md](SKILL.md).
- **Alarm:** a reminder at a fixed time ("at 3 pm", "Thursday at 10"),
  ringing in the ToDo-Viewer. Rules and helper: [alarms.md](alarms.md).
- **Note:** a longer horizon, a reminder for later, an open question to
  someone else, an observation ("check the performance when the database
  fills up"), or an idea without an assignment.
- The time horizon is the main marker. When the case is clear, act. When it
  is doubtful, ask once and briefly which of the three is meant.
- "Note" here means the ToDo-Viewer object. A backlog item's notes entries
  (`<ID>_notes.md`) are something else. When unclear which is meant, ask.

## Reading order

1. Read the lean index first (`index`, optionally filtered). It carries label,
   status, due state, topic, and a one-line summary.
2. Pick the notes that fit by their summaries. Only then load a note (`show`)
   or its documents, and only those. Never load every note.
3. Before creating a note, look at the index for an equivalent one; extend or
   revise it instead of adding a duplicate.

## Due notes

The viewer decides what is due (time, events, topic dates, review date) and
marks it in its interface. Do not check for due notes and do not announce
them on your own. When the user asks what is due, read `index --due` or
`due`, list label, reason, and summary, and load a body only on request.

A due note means "look at it". Afterwards the user decides: wait again
(`snooze`, a new date or event), `finish` as done or dropped, keep it
(`keep`), or promote it to backlog work.

## Creating and changing

- The summary is one line and says enough to judge relevance without reading
  the rest. Details go into the body. For an observation without a trigger,
  put the hint what to check into the body.
- Put a note into an existing topic when one fits. Topics only sort; create
  one only when none fits, and keep the tree shallow.
- The viewer's default review period applies. Set `review_at` only when the
  user asks for another date. Never change the settings.
- Triggers are events only: a status of a linked item or the date of the
  note's topic. A reminder at a fixed time is an alarm, bound to the note
  ([alarms.md](alarms.md)). Resolve relative dates for `review_at` or a topic
  date ("tomorrow morning", "Thursday at 10") into a fixed time with the
  machine's local time zone as ISO 8601 with offset
  (`2026-10-09T09:00:00+02:00`), and name the result with weekday, date, and
  time in your answer. When the wording is ambiguous ("early" can mean 6 or 9
  o'clock), ask before creating.
- Links point to items, topics, or other notes, also in other registered
  projects. A link with role `trigger` exists only together with its event
  trigger.

## Authority

Without asking: create and revise notes, their documents, and topics; set
links with role `reference` or `origin`; set and remove triggers the user
described; `keep`; `snooze`; `finish` as `done`; `restore`; decide notices
with `keep`, `detach`, or `acknowledge`.

Ask first: `finish` as `dropped`; deleting a note or topic (no question when
the request clearly asks for it; for a topic with content the user also
chooses what happens to its notes, see `topic-delete` in [notes-api.md](notes-api.md));
notice decisions `drop` and `promote`; `promote` and `demote`; `move` to
another project.

Never: remove anything for good (the HTTP API offers no way, and you do not
look for another), or change the viewer's settings.

## Sprint reminders

"Remember this for the next sprint" becomes a note in the topic that carries
the sprint date, with a trigger of kind `topic_date`. If no such topic exists,
ask for its name and date.

When the date has passed, the notes fire and the topic has no new date. Ask
the user for the next date, then set it (`topic-update`) and `snooze` each
affected note with a new `topic_date` trigger.

## Converting

- **Note to backlog item:** ask, propose parent, area, goal, and completion
  criteria as [SKILL.md](SKILL.md) requires, then `promote`. The note becomes
  `promoted` and keeps an `origin` link. If the server answers `parent_closed`,
  follow [SKILL.md](SKILL.md) (ask once about reopening).
- **Backlog item to note:** `demote`, only after asking. It works only for an
  open item without children that no other item refers to; the item is closed
  as "downgraded to a note".

## Changes on the other side of a link

When a linked item is completed, rejected, deleted, or retyped, the viewer
leaves a notice on the note until someone decides. When the user asks about a
note or you work on it, read its open notices (`notices <NOTE>`) and
offer the options keep, detach, drop, or promote. The reverse also exists: an
item gets a notice when a note that points to it is dropped or promoted.

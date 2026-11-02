# Notes through the ToDo-Viewer API

The ToDo-Viewer server stores topics, notes, links, and triggers, decides what
is due, creates notices when linked items change, and checks all rules. It
does not know what the user approved: the authority in [notes.md](notes.md)
applies. The server's own description is its `docs/techdocs/neubau-server.md`
(plugin `notes`); this file covers what you need to call the helper.

## Calling the helper

```
python3 ".claude-harness/runtime/scripts/notes_api.py" [--project <name>] <command> [arguments]
```

Run it in the session's project. It takes the server URL (`[todo].api_url`) and
the project from the harness config (the root project by default, a subproject
with `--project <name>`); notes belong to the viewer project of that backlog
folder. There is no path argument. `--source <name>` (instead of `--project`)
addresses another project's notes by the exact name from `sources`; it needs
the owner's approval (rules in [SKILL.md](SKILL.md)). Without arguments it
prints the command list. JSON input goes to stdin; use a quoted heredoc:

```
python3 ".claude-harness/runtime/scripts/notes_api.py" snooze NOTE-004 3 <<'EOF'
{"review_at": "2026-11-02T09:00:00+01:00"}
EOF
```

## Objects

- **Label:** `NOTE-001`, `TOPIC-001`, counted per project and type, never
  reused. Address everything by label; the helper turns labels into the
  server's internal ids where it needs them.
- **Status of a note** (derived by the server): `waiting`, `due`, `snoozed`,
  `done`, `dropped`, `promoted`. `due` only means "look at it". `done`,
  `dropped`, and `promoted` notes are archived, and so are open notes of an
  archived topic; deleted ones are in the trash. Archived and deleted notes
  cannot be changed, only read or restored.
- **`reason`** of a due note: `trigger`, `notice`, `topic_due`, or
  `review_expired`.
- **Version:** every note and topic has a `version`, a number. Changing
  commands need the one you read last, else `version_conflict`. A document
  write or a notes entry changes it too: read the note again afterwards.
- **Times:** ISO 8601, preferably with offset (`2026-10-09T09:00:00+02:00`);
  without one the server takes UTC. It answers in UTC.
- **Triggers** (`trigger-add`, or `trigger` in `snooze`):
  - `{"kind": "event", "target": "STORY-002", "status": "Completed"}` plus
    optional `target_project` (another project's name from `sources`).
    Statuses: `In progress`, `Awaiting confirmation`, `Completed`,
    `Rejected`. If the item has the status already, the trigger fires at once.
    The matching `trigger` link is created with it.
  - `{"kind": "topic_date"}`: the date of the note's topic; the topic needs a
    date.
  - There are no time triggers: a reminder at a fixed time is an alarm
    (`alarms_api.py`, see [alarms.md](alarms.md)).
  - `trigger_mode` `any` (default) fires on the first trigger, `all` when all
    have arrived. A new `trigger` in `snooze` replaces all old triggers.
- **Links** (`link-add`): a `target` label (item, topic, or note), optional
  `target_project` (another project's name), `role` `reference` (default) or
  `origin`. The same link twice is `link_exists`.

## Commands

| Command | Use |
|---|---|
| `health` | Server reachable? |
| `sources` | `Project \| Folder` of every project the viewer knows; the names `--source` accepts |
| `index [--status S] [--due] [--archived] [--query Q] [--all-projects]` | The lean index: topics (`Label \| Name \| Due at \| Due \| Notes`) and notes (`Label \| Status \| Reason \| Review at \| Topic \| Summary`). Default: open notes of this project. `--status` takes comma-separated statuses; `--archived` reads the archive; `--all-projects` covers every project |
| `due` | All due notes of all projects with reason, topic path, triggers, notices, and `due_since` (JSON) |
| `show <NOTE>` | One note: body, topic path, triggers, open notices, documents, version |
| `topics`, `topic <TOPIC>` | Topics of the project as JSON; one topic with its sub-topics and notes |
| `links <NOTE>`, `backlinks <NOTE>` | Links of a note, and the elements pointing to it (each with `link_uid`, `role`, label, kind) |
| `notes-of-item <ID>` | Notes pointing to a backlog item |
| `docs <NOTE>`, `doc <NOTE> <name>`, `put-doc <NOTE> <name> <version\|new>`, `note-entry <NOTE>` | Long-form documents of a note: names `<LABEL>_notes.md`, `<LABEL>_spec.md`, `<LABEL>_spec_<topic>.md`. `doc` prints `version: <v>`, a blank line, the text; `put-doc` replaces or (with `new`) creates it from stdin; `note-entry` appends a dated entry (`{topic, discussed?, decided?, open?}`) |
| `notices <NOTE>`, `notices <ID> --side item` | Open notices of one note, or of one backlog item |
| `create` | New note. stdin: `summary`, optional `body`, `topic`, `review_at`, `trigger_mode` |
| `update <NOTE> <version>` | stdin: any of `summary`, `body`, `topic`, `review_at`, `trigger_mode`; `null` clears `body`, `topic`, `review_at` |
| `keep <NOTE> <version>` | The review date moves on, nothing else changes |
| `snooze <NOTE> <version>` | Wait again with the standard review date; stdin optional: `review_at` and/or `trigger`. Fired triggers are reset |
| `finish <NOTE> <version> <done\|dropped>` | Close into the archive |
| `move <NOTE> <version> <project> [--topic L]` | Move to another project (name from `sources`): a new note with a new label, the old one goes to the trash |
| `delete <NOTE> <version>` | To the trash |
| `restore <NOTE> <version>` | Back from the trash, or from the archive to waiting with a new review date |
| `trigger-add <NOTE>`, `trigger-remove <trigger-uid>` | See triggers above; the trigger uid is in `show` |
| `link-add <NOTE>`, `link-remove <link-uid>` | See links above; the link uid is `link_uid` in `links` |
| `decide <notice-uid>` | stdin: `{"decision": "keep\|detach\|drop\|promote\|acknowledge", "version"?, "type"?, "fields"?}`. Notes: `keep` (review date moves on), `detach` (remove the reference link), `drop`, `promote` (with `type` and `fields` as for `promote`). Items: only `acknowledge`. The notice uid is in `show` or `notices` |
| `promote <NOTE>` | stdin: `{"version", "type": "Task\|Story\|Epic", "fields": {"area", "goal", "completion_criteria", "title"?, "summary"?, "parent"?, "required_for_parent"?, "priority"?, "dependencies"?}}`. Creates the item in the note's project by the normal rules (IDs in `parent` and `dependencies`); body, notes, and specs move along, the note is `promoted` and keeps an `origin` link. An interrupted call can be repeated |
| `demote <ITEM-ID>` | stdin: `{"version": <item version>, "topic"?}`. Item to note; see [notes.md](notes.md) for when it works |
| `topic-create` | stdin: `{name, parent?, due_at?}`; the tree has a maximum depth (`topic_too_deep`) |
| `topic-update <TOPIC> <version>`, `topic-move <TOPIC> <version>` | stdin: `{name?, due_at?}` (`due_at: null` removes the date); `{parent}` (`null` = top level) |
| `topic-archive <TOPIC> <version>`, `topic-reactivate <TOPIC> <version>` | Archive a topic with its sub-topics, or bring it back. A topic with content needs a choice on stdin: `keep_archived` (true: its archived notes move to the topic "Archiviert"), `active_notes` `move` (to `move_to`, a topic label or `null` = none) or `archive` |
| `topic-delete <TOPIC> <version>` | To the trash; a topic with content needs the same choice, with `active_notes` `move` or `delete` (`topic_has_content` or `choice_missing` names what is there) |
| `topic-restore <TOPIC>` | Back from the trash, with what was deleted with it |
| `trash` | Topics and notes of the project in the trash |
| `settings` | `max_topic_depth` and `review_days` (read only) |

The helper has no command to remove anything for good and none to change the
settings.

## Errors

- Exit 1: the server refused; stderr shows `HTTP <status> <code>: <message>`
  and `details`. Frequent codes:
  - `version_conflict`: the note changed since you read it. Read it again,
    check whether your change still fits, then decide — never repeat the call
    blindly.
  - `note_archived`, `note_deleted`: archived or deleted notes cannot be
    changed; `restore` first, if that is wanted.
  - `topic_too_deep`, `topic_loop`, `topic_has_content`, `choice_missing`,
    `topic_archived`, `topic_in_trash`, `trigger_needs_topic_date`,
    `link_exists`, `same_project`, `not_found`, `invalid_input`.
  - For `promote` and `demote` the backlog rules apply: `parent_closed`
    (`todo` skill: ask once about reopening), `demote_not_open`,
    `demote_has_children`, `demote_referenced` (`details` names the items in
    the way).
- Exit 2: wrong call, invalid JSON on stdin, a version that is not a number,
  a time trigger, or the module is off.
- Exit 3: server not reachable; see step 4 in [notes.md](notes.md).
- Exit 4: the project is not registered in the viewer; see step 4 in
  [SKILL.md](SKILL.md).

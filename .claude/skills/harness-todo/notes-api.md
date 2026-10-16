# Notes through the ToDo-Viewer API

The ToDo-Viewer server stores topics, notes, links, and triggers, decides what
is due, creates notices when linked items change, and checks all rules. It
does not know what the user approved: the authority in [notes.md](notes.md)
applies. The server's own description is its `interfaces.md` ("HTTP API v2:
Topics, Notes und Links"); this file covers what you need to call the helper.

## Calling the helper

```
python3 ".claude-harness/runtime/scripts/notes_api.py" [--project <name>] <command> [arguments]
```

Run it in the session's project. It takes the server URL (`[todo].api_url`) and
the project from the harness config (the root project by default, a subproject
with `--project <name>`); notes belong to that project. There is no path
argument. `--source <name>` (instead of `--project`) addresses another
project's notes by the exact name from `sources`; it needs the owner's approval
(rules in [SKILL.md](SKILL.md)). Without arguments it prints the command list. JSON input goes to
stdin; use a quoted heredoc:

```
python3 ".claude-harness/runtime/scripts/notes_api.py" snooze NOTE-004 3f9a... <<'EOF'
{"review_at": "2026-11-02T09:00:00+01:00"}
EOF
```

## Objects

- **Label:** `NOTE-001`, `TOPIC-001`, counted per project and type, never
  reused. Address everything by label.
- **Status of a note** (derived by the server): `waiting`, `due`, `snoozed`,
  `done`, `dropped`, `promoted`. `due` only means "look at it". `done`,
  `dropped`, and `promoted` notes are archived; deleted ones are in the trash.
  Closed and deleted notes cannot be changed, only read or restored.
- **`reason`** of a due note: `trigger`, `notice`, `topic_due`, or
  `review_expired`.
- **Version:** every note has a `version`. `update`, `keep`, `snooze`,
  `finish`, `move`, `promote`, and `demote` need the one you read last, else
  `version_conflict`. Topics, triggers, and links have none.
- **Times:** ISO 8601 **with** offset (`2026-10-09T09:00:00+02:00`), else 400.
  The server answers in UTC.
- **Triggers** (`trigger-add`, or `trigger` in `snooze`):
  - `{"kind": "time", "at": "..."}`.
  - `{"kind": "event", "target": "STORY-002", "target_status": "Completed"}`
    plus optional `target_project`. Statuses: `In progress`,
    `Awaiting confirmation`, `Completed`, `Rejected`. If the item has the
    status already, the trigger fires at once. The matching `trigger` link is
    created with it.
  - `{"kind": "topic_due"}`: needs a topic with a date on the note.
  - `trigger_mode` `any` (default) fires on the first trigger, `all` when all
    have arrived. A new `trigger` in `snooze` replaces all old triggers.
- **Links** (`link-add`): `kind` `item`, `topic`, or `note`, a `target` label,
  optional `target_project` (another registered project), `role` `reference`
  (default) or `origin`. The same link twice is `link_exists`.

## Commands

| Command | Use |
|---|---|
| `health` | Server reachable? |
| `sources` | `Project \| Folder` of every project the viewer knows; the names `--source` accepts |
| `index [--topic L] [--status S] [--due] [--archived] [--linked-item ID] [--all-projects]` | The lean index: topics (`Label \| Path \| Due at \| Due \| Notes`) and notes (`Label \| Status \| Reason \| Review at \| Topic \| Summary`). Default: open notes of this project. `--topic` includes sub-topics; `--archived` reads the archive; `--linked-item` finds notes linked or triggered by that item; `--all-projects` adds the project in front of each label |
| `due` | All due notes of all projects with reason, topic path, arrived triggers, and possible actions (JSON) |
| `show <NOTE>` | One note: body, triggers, open notices, version |
| `topics [--deleted]`, `topic <TOPIC>` | Topics as JSON |
| `links <NOTE>`, `backlinks <NOTE>` | Links of a note (with `reachable`), and the notes pointing to it |
| `notes-of-item <ID>`, `notes-of-topic <TOPIC>` | Notes (all projects) pointing to a backlog item, or sitting in a topic |
| `docs <NOTE>`, `doc <NOTE> <name>`, `put-doc <NOTE> <name> <version\|new>`, `note-entry <NOTE>` | Long-form documents of a note: names `<LABEL>_notes.md`, `<LABEL>_spec.md`, `<LABEL>_spec_<topic>.md`. `doc` prints `version: <v>`, a blank line, the text; `put-doc` replaces or (with `new`) creates it from stdin; `note-entry` appends a dated entry (`{topic, discussed?, decided?, open?}`) |
| `notices <NOTE\|ITEM-ID> [--side note\|item] [--open]` | Notices about changed links of one note (default) or one item (`--side item`) |
| `create` | New note. stdin: `summary`, optional `body`, `topic`, `review_at`, `trigger_mode` |
| `update <NOTE> <version>` | stdin: any of `summary`, `body`, `topic`, `review_at`, `trigger_mode`; `null` clears `body`, `topic`, `review_at` |
| `keep <NOTE> <version>` | The review date moves on, nothing else changes |
| `snooze <NOTE> <version>` | Wait again with the standard review date; stdin optional: `review_at` and/or `trigger`. Fired triggers are reset |
| `finish <NOTE> <version> <done\|dropped>` | Close into the archive |
| `move <NOTE> <version> <project> [--topic L]` | Move to another project: a new note with a new label, the old one goes to the trash |
| `delete <NOTE>`, `restore <NOTE>` | To the trash; back to waiting with a new review date, also from the archive |
| `trigger-add <NOTE>`, `trigger-remove <NOTE> <id>` | See triggers above; the answer is the note |
| `link-add <NOTE>`, `link-remove <NOTE> <id>` | See links above |
| `decide <notice-id>` | stdin: `{"decision": "keep\|detach\|drop\|promote\|acknowledge", "version"?, "promotion"?}`. Notes: `keep` (review date moves on), `detach` (remove the reference link), `drop`, `promote` (with `promotion`: the fields of `promote` below). Items: only `acknowledge` |
| `promote <NOTE>` | stdin: `version`, `item_type` (`Task`\|`Story`\|`Epic`), `area`, `goal`, `completion_criteria`, optional `title`, `summary` (default: the note's summary), `parent`, `required_for_parent`, `priority`, `dependencies`. Creates the item in the note's project by the normal rules; the note's body becomes the first notes entry, the note is `promoted` and keeps an `origin` link. An interrupted call can be repeated with the same version |
| `demote <ITEM-ID>` | stdin: `{"version": <item version>, "topic"?}`. Item to note; see the skill for when it works |
| `topic-create`, `topic-update <TOPIC>`, `topic-move <TOPIC>`, `topic-delete <TOPIC> [--cascade]`, `topic-restore <TOPIC>` | Topics: `{name, parent?, due_at?}`; `{name?, due_at?}` (`due_at: null` removes the date); `{parent}`; the tree has a maximum depth (`topic_too_deep`) |
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
  - `note_closed`, `note_deleted`: closed or deleted notes cannot be changed;
    `restore` first, if that is wanted.
  - `topic_too_deep`, `topic_loop`, `topic_has_content`, `link_exists`,
    `link_target_not_found`, `link_project_unknown`, `invalid_value`.
  - For `promote` and `demote` the backlog rules apply: `parent_closed`
    (`todo` skill: ask once about reopening), `demote_not_open`,
    `demote_has_children`, `demote_referenced` (`details.items` names the
    items in the way).
- Exit 2: wrong call or invalid JSON on stdin, or the module is off.
- Exit 3: server not reachable; see step 4 in [notes.md](notes.md).

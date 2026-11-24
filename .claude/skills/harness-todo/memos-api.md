# Memos through the ToDo-Viewer API

The ToDo-Viewer server stores topics, memos, links, and triggers, decides what
is due, creates hints when linked items change, and checks all rules. It
does not know what the user approved: the authority in [memos.md](memos.md)
applies. The server's own description is its `docs/techdocs/neubau-server.md`
(plugin `memos`); this file covers what you need to call the helper.

## Calling the helper

```
python3 ".claude-harness/runtime/scripts/memos_api.py" [--project <name>] <command> [arguments]
```

Run it in the session's project. It takes the server URL (`[todo].api_url`) and
the project from the harness config (the root project by default, a subproject
with `--project <name>`); memos belong to the viewer project of that backlog
folder. There is no path argument. `--source <name>` (instead of `--project`)
addresses another project's memos by the exact name from `sources`; it needs
the owner's approval (rules in [SKILL.md](SKILL.md)). Without arguments it
prints the command list. JSON input goes to stdin; use a quoted heredoc:

```
python3 ".claude-harness/runtime/scripts/memos_api.py" snooze MEMO-004 3 <<'EOF'
{"review_at": "2026-11-02T09:00:00+01:00"}
EOF
```

## Objects

- **Label:** `MEMO-001`, `TOPIC-001`, counted per project and type, never
  reused. Address everything by label; the helper turns labels into the
  server's internal ids where it needs them.
- **Status of a memo** (derived by the server): `waiting`, `due`, `snoozed`,
  `done`, `dropped`, `promoted`. `due` only means "look at it". `done`,
  `dropped`, and `promoted` memos are archived, and so are open memos of an
  archived topic; deleted ones are in the trash. Archived and deleted memos
  cannot be changed, only read or restored.
- **`reason`** of a due memo: `trigger`, `hint`, `topic_due`, or
  `review_expired`.
- **Version:** every memo and topic has a `version`, a number. Changing
  commands need the one you read last, else `version_conflict`. A document
  write or a memos entry changes it too: read the memo again afterwards.
- **Times:** ISO 8601, preferably with offset (`2026-10-09T09:00:00+02:00`);
  without one the server takes UTC. It answers in UTC.
- **Triggers** (`trigger-add`, or `trigger` in `snooze`):
  - `{"kind": "event", "target": "STORY-002", "status": "Completed"}` plus
    optional `target_project` (another project's name from `sources`).
    Statuses: `In progress`, `Awaiting confirmation`, `Completed`,
    `Rejected`. If the item has the status already, the trigger fires at once.
    The matching `trigger` link is created with it.
  - `{"kind": "topic_date"}`: the date of the memo's topic; the topic needs a
    date.
  - There are no time triggers: a reminder at a fixed time is an alarm
    (`alarms_api.py`, see [alarms.md](alarms.md)).
  - `trigger_mode` `any` (default) fires on the first trigger, `all` when all
    have arrived. A new `trigger` in `snooze` replaces all old triggers.
- **Links** (`link-add`): a `target` label (item, topic, or memo), optional
  `target_project` (another project's name), `role` `reference` (default) or
  `origin`. The same link twice is `link_exists`.

## Commands

| Command | Use |
|---|---|
| `health` | Server reachable? |
| `sources` | `Project \| Folder` of every project the viewer knows; the names `--source` accepts |
| `index [--status S] [--due] [--archived] [--query Q] [--all-projects]` | The lean index: topics (`Label \| Name \| Due at \| Due \| Memos`) and memos (`Label \| Status \| Reason \| Review at \| Topic \| Summary`). Default: open memos of this project. `--status` takes comma-separated statuses; `--archived` reads the archive; `--all-projects` covers every project |
| `due` | All due memos of all projects with reason, topic path, triggers, hints, and `due_since` (JSON) |
| `show <MEMO>` | One memo: body, topic path, triggers, open hints, documents, version |
| `topics`, `topic <TOPIC>` | Topics of the project as JSON; one topic with its sub-topics and memos |
| `links <MEMO>`, `backlinks <MEMO>` | Links of a memo, and the elements pointing to it (each with `link_uid`, `role`, label, kind) |
| `memos-of-item <ID>` | Memos pointing to a backlog item |
| `docs <MEMO>`, `doc <MEMO> <name>`, `put-doc <MEMO> <name> <version\|new>`, `memo-entry <MEMO>` | Long-form documents of a memo: names `<LABEL>_notes.md`, `<LABEL>_spec.md`, `<LABEL>_spec_<topic>.md`. `doc` prints `version: <v>`, a blank line, the text; `put-doc` replaces or (with `new`) creates it from stdin; `memo-entry` appends a dated entry (`{topic, discussed?, decided?, open?}`) |
| `hints <MEMO>`, `hints <ID> --side item` | Open hints of one memo, or of one backlog item |
| `create` | New memo. stdin: `summary`, optional `body`, `topic`, `review_at`, `trigger_mode` |
| `update <MEMO> <version>` | stdin: any of `summary`, `body`, `topic`, `review_at`, `trigger_mode`; `null` clears `body`, `topic`, `review_at` |
| `keep <MEMO> <version>` | The review date moves on, nothing else changes |
| `snooze <MEMO> <version>` | Wait again with the standard review date; stdin optional: `review_at` and/or `trigger`. Fired triggers are reset |
| `finish <MEMO> <version> <done\|dropped>` | Close into the archive |
| `move <MEMO> <version> <project> [--topic L]` | Move to another project (name from `sources`): a new memo with a new label, the old one goes to the trash |
| `delete <MEMO> <version>` | To the trash |
| `restore <MEMO> <version>` | Back from the trash, or from the archive to waiting with a new review date |
| `trigger-add <MEMO>`, `trigger-remove <trigger-uid>` | See triggers above; the trigger uid is in `show` |
| `link-add <MEMO>`, `link-remove <link-uid>` | See links above; the link uid is `link_uid` in `links` |
| `decide <hint-uid>` | stdin: `{"decision": "keep\|detach\|drop\|promote\|acknowledge", "version"?, "type"?, "fields"?}`. Memos: `keep` (review date moves on), `detach` (remove the reference link), `drop`, `promote` (with `type` and `fields` as for `promote`). Items: only `acknowledge`. The hint uid is in `show` or `hints` |
| `promote <MEMO>` | stdin: `{"version", "type": "Task\|Story\|Epic", "fields": {"goal", "completion_criteria", "title"?, "summary"?, "parent"?, "required_for_parent"?, "priority"?, "dependencies"?}}`. Creates the item in the memo's project by the normal rules (IDs in `parent` and `dependencies`); body, memos, and specs move along, the memo is `promoted` and keeps an `origin` link. An interrupted call can be repeated |
| `demote <ITEM-ID>` | stdin: `{"version": <item version>, "topic"?}`. Item to memo; see [memos.md](memos.md) for when it works |
| `topic-create` | stdin: `{name, parent?, due_at?}`; the tree has a maximum depth (`topic_too_deep`) |
| `topic-update <TOPIC> <version>`, `topic-move <TOPIC> <version>` | stdin: `{name?, due_at?}` (`due_at: null` removes the date); `{parent}` (`null` = top level) |
| `topic-archive <TOPIC> <version>`, `topic-reactivate <TOPIC> <version>` | Archive a topic with its sub-topics, or bring it back. A topic with content needs a choice on stdin: `keep_archived` (true: its archived memos move to the topic "Archiviert"), `active_memos` `move` (to `move_to`, a topic label or `null` = none) or `archive` |
| `topic-delete <TOPIC> <version>` | To the trash; a topic with content needs the same choice, with `active_memos` `move` or `delete` (`topic_has_content` or `choice_missing` names what is there) |
| `topic-restore <TOPIC>` | Back from the trash, with what was deleted with it |
| `trash` | Topics and memos of the project in the trash |
| `settings` | `max_topic_depth` and `review_days` (read only) |

The helper has no command to remove anything for good and none to change the
settings.

## Errors

- Exit 1: the server refused; stderr shows `HTTP <status> <code>: <message>`
  and `details`. Frequent codes:
  - `version_conflict`: the memo changed since you read it. Read it again,
    check whether your change still fits, then decide — never repeat the call
    blindly.
  - `memo_archived`, `memo_deleted`: archived or deleted memos cannot be
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
- Exit 3: server not reachable; see step 4 in [memos.md](memos.md).
- Exit 4: the project is not registered in the viewer; see step 4 in
  [SKILL.md](SKILL.md).

# Backlog through the ToDo-Viewer API

Used when the backend is `api` (the default; see [SKILL.md](SKILL.md) for how it is chosen). The ToDo-Viewer server
checks the format and the parent rules, assigns IDs, writes notes entries in
the format, and detects concurrent changes through version numbers. It does
not know which changes the project owner approved: the change authority in
[SKILL.md](SKILL.md) still applies.

## Calling the helper

```
python3 ".claude-harness/runtime/scripts/backlog_api.py" [--project <name> | --source <name>] <command> [arguments]
```

Run it in the session's project. It takes the backlog folder and the URL from
the harness config: the root project by default, a subproject with
`--project <name>` (the names the session start lists). Pick the project the
work belongs to; there is no path argument. The helper finds the viewer
project whose mirror folder is that backlog folder in the main checkout (also
from inside a worktree). `--source <name>` instead addresses another
project's backlog by the exact name from `sources`; it needs the owner's
approval ([SKILL.md](SKILL.md)). Refer to items by their IDs (labels); the
helper turns the IDs in `parent` and `dependencies` into the server's
internal ids. JSON input goes to stdin; use a quoted heredoc so the shell
leaves the text alone:

```
python3 ".claude-harness/runtime/scripts/backlog_api.py" update STORY-017 3 <<'EOF'
{"fields": {"status": "In progress"}}
EOF
```

| Command | Use |
|---|---|
| `health` | Is the server reachable? |
| `sources` | `Project \| Folder` of every project the viewer knows; the names `--source` accepts |
| `register` | Register the session's backlog as a viewer project with a mirror. Only after the owner said yes (exit code 4 below) |
| `index [--with-trash]` | Overview: `ID \| Type \| Status \| Title \| Parent \| Notes` (`Notes`: state of the notes head, or `-`); items in the trash are left out, with `--with-trash` they are shown marked `(Papierkorb)` |
| `show <ID>` | One item as JSON with its `version`, archived items included; deleted children carry a `note` and do not count as open work (stderr names unclosed ones as a hint) |
| `create` | New item. stdin: `type`, `title`, `goal`, `completion_criteria` (numbered list, one criterion per line, `\n`-separated), optional `parent` (ID), `required_for_parent` (`"Yes"`/`"No"`), `priority`, `dependencies` (list of IDs), `summary`. Prints the item with its new ID |
| `update <ID> <version>` | stdin: `{"fields": {...}}` with any of `title`, `status`, `parent`, `required_for_parent`, `priority`, `dependencies`, `goal`, `completion_criteria`, `summary`; add `"resolution": "..."` when setting `Completed` or `Rejected` |
| `move <ID> <version> <parent\|-> [--position N]` | New parent (`-` = none) and position among its siblings |
| `reopen <ID>` | Set the item and its closed ancestors to `In progress`, from the top down |
| `note <ID>` | Append a dated notes entry. stdin: `{"topic": "...", "discussed": [...], "decided": [...], "open": [...]}`; add `"summary"` if the item has none yet, and `"state"` (the new head) with `"state_version"` (the head's version, once there is a head) to replace the head in the same call. After every notes write (`note`, `put-state`, `confirm-state`, `put-doc` on notes) the server's hints are printed on stderr, one `hint:` line each (stale or long head, rewritten log); they never reject the call. The same commands also print a line `[harness] notes-state <ID> <current|stale|missing>` on stderr (and `update` to `In progress`, `reopen`, and `doc <ID> <ID>_spec.md` print `[harness] active <ID>`): a hook reads them to check the head at the end of your turn and to remind you of the notes; they are not for you to act on. On an epic or story with a child `In progress` (also for `put-doc` on its notes) a hint on stderr asks whether the discussion belongs in that child's notes; the entry is written either way |
| `state <ID>` | The head (`## State`) of the item's notes without the log, as JSON: `content`, `stamp`, `state` (`current`/`stale`/`missing`), `checksum`, `last_entry`, `version` (of the head). Read it first when discussing an item |
| `put-state <ID> <version>` | Replace the head with the text from stdin (without heading and stamp), in the form of [format.md](format.md#notes) (markers `- Goal/Status:`, `- Next step:`, `- Open:`, `- Decided:`, `- References:`); the server stamps it against the last entry. Needs at least one log entry |
| `confirm-state <ID> <version>` | The head is still current: only the stamp is renewed |
| `entries <ID> [--last N]` | The log entries (all, or the last N) as `{position, day, topic, text}`; read them only when you need the reasons behind a decision |
| `doc <ID> <name>` | Print a notes or spec document: `version: <v>`, a blank line, the text. Names: `<ID>_notes.md`, `<ID>_spec.md`, `<ID>_spec_<topic>.md` |
| `put-doc <ID> <name> <version\|new> [--summary TEXT]` | Replace a document with the complete text from stdin, or create it with `new` (first notes need `--summary` if the item has none) |
| `delete-doc <ID> <name> <version>` | Move a notes or spec document to the trash, in the `version` that `doc` printed. With the notes go their head and the item's summary (a new first notes entry needs `summary` again); deleting a spec has no further effect. The answer names `trash_uid`. Refused for an item in the trash. The file leaves the mirror at once if it is unchanged there |
| `retype <ID> <version> <type>` | Change the type (`Epic`, `Story`, `Task`). The ID's prefix is the type, so the item gets the next free ID of the new type; references in the project's texts follow. Prints `old_label` and `new_label`; refused when the new type breaks a lifecycle rule |
| `delete <ID> <version> [--cascade]` | Move to the trash; an item with active children needs `--cascade` (the answer names `has_children` first and changes nothing) |
| `trash` | Backlog items and deleted documents in the trash. A document has `kind` `document`, its own `uid` (use that to restore it), the item's ID as `label` and its name as `title` |
| `restore <ID\|trash uid>` | Restore from the trash: an item with the descendants deleted together with it (by ID), or a deleted document (by the `uid` that `trash` shows; notes come back with head and summary). Refused with `document_exists` if the item has a document of that name again, and with `item_deleted` while the item is in the trash |

A `version` is a number: take it from the last `show` (or write answer) of
that item or document. A notes entry and every document write count as a
change of the item: read it again before the next `update`. The date of a
notes entry is set by the server. To revise notes or a spec, read it with
`doc`, change the text, and write it back with `put-doc` and the version you
read.

After `retype` the old ID is gone: use `new_label` from the answer, and read
the item again (new `version`). Changing the type changes the meaning of the
item, so ask the owner first (see [SKILL.md](SKILL.md)).

To reopen a closed item (only after the owner approved it), use `update`
with a status that is not final, e.g. `{"fields": {"status": "In progress"}}`,
or `reopen <ID>`, which also reopens its closed ancestors. This works for
archived items too: the server moves them back to `TODO.md` and drops
`Resolution`. Then record the reason with `note`.

The topic of an item is the node of the viewer's mindmap it hangs on (tools
`mindmap_…`, e.g. `mindmap_get_item_node`, `mindmap_assign_item`; or the
section "Knoten" in the item's detail). There is no filter and no column in the
index lines for it, and this helper does not offer it. The viewer has no `area`
field any more: a call with `area` in `fields` fails with `not_editable`, and
`show` returns no such field.

## Topic tree (MCP tools of the viewer)

Only the viewer's MCP server `todo-viewer` offers these (names as `tools/list`
prints them; HTTP paths below `/api/mindmap/…`); `backlog_api.py` has no
commands for them. The rule for using them is in [SKILL.md](SKILL.md)
(creating an item).

| Tool | Purpose | Main inputs |
|---|---|---|
| `mindmap_get_tree` | Read the topic tree: nodes (uid, title, parent, position, counts, state) and the items without a node (`unassigned`) | `project` |
| `mindmap_create_item_at_node` | Create an item and hang it on the node | `node`, `type` (Epic, Story, Task), `fields` (`completion_criteria` required; `title`, `goal` otherwise from the node) |
| `mindmap_assign_item` | Hang an existing item on a node | `node`, `item`, `replace` (only to replace another node) |
| `mindmap_create_node` | Create a node, only after the owner's yes | `project`, `title`, `text`, `parent` |
| `backlog_create_item` | Create an item without a node, when none fits or the owner declines | `project`, `type`, `fields` |

## Errors

- Exit 1: the server refused; stderr shows `HTTP <status> <code>: <message>`
  and `details`.
  - `version_conflict`: someone changed the item or document since you read
    it. Read it again, check whether your change still fits, then decide —
    never repeat the call blindly.
  - `parent_closed`: the item would stand under a closed parent. Ask the
    owner once whether to reopen the closed ancestors; if yes, run
    `reopen <parent ID>` and repeat the call. Never create the item without a
    parent instead.
  - `children_still_active`: a parent cannot be closed while children are
    active; close or reparent them first.
  - `not_found` for an ID: the ID does not exist in this project; check it
    in the `index` instead of guessing another one.
  - Other rule violations (`required_children_not_done`, `parent_cycle`,
    `dependency_cycle`, `unknown_reference`, `resolution_required`, …) name
    the blocking items in `details`. Resolve them as [format.md](format.md)
    describes, or ask the owner.
- Exit 2: wrong call, invalid JSON on stdin, or a version that is not a
  number.
- Exit 3: server not reachable; see step 4 in [SKILL.md](SKILL.md). The
  server usually runs permanently in a container; after changes to the
  ToDo-Viewer it must be rebuilt (`./todo.sh update` there).
- Exit 4: the backlog folder is not registered as a project in the viewer.
  Tell the owner and ask whether to register it. Only after a yes run
  `register` (with the same `--project`); never register on your own.

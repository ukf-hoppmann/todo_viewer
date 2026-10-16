# Backlog through the ToDo-Viewer API

Used when `[todo].backend` is `api` (the default). The ToDo-Viewer server
checks the format and the parent rules, assigns IDs, writes notes entries in
the format, and detects concurrent changes through version tokens. It does
not know which changes the project owner approved: the change authority in
[SKILL.md](SKILL.md) still applies.

## Calling the helper

```
python3 ".claude-harness/runtime/scripts/backlog_api.py" [--project <name> | --source <name>] <command> [arguments]
```

Run it in the session's project. It takes the backlog folder and the URL from
the harness config: the root project by default, a subproject with
`--project <name>` (the names the session start lists). Pick the project the
work belongs to; there is no path argument. `--source <name>` instead addresses
a backlog outside the session's project by the exact name from `sources`; it
needs the owner's approval ([SKILL.md](SKILL.md)) and never registers a source. The helper finds the ToDo-Viewer
source of that backlog (Markdown or database source) and registers it if
missing. No `TODO.md` is needed in the project for this. Inside a worktree it uses
the backlog of the main checkout. JSON input goes to stdin; use a quoted
heredoc so the shell leaves the text alone:

```
python3 ".claude-harness/runtime/scripts/backlog_api.py" update STORY-017 3f9a... <<'EOF'
{"fields": {"status": "In progress"}}
EOF
```

| Command | Use |
|---|---|
| `health` | Is the server reachable? |
| `sources` | `Project \| Folder` of every backlog the viewer knows; the names `--source` accepts |
| `index` | Overview: `ID \| Type \| Status \| Area \| Title \| Parent` |
| `show <ID>` | One item as JSON with its `version`, archived items included |
| `create` | New item. stdin: `type`, `title`, `area`, `goal`, `completion_criteria`, optional `parent`, `required_for_parent` (`"Yes"`/`"No"`), `priority`, `dependencies` (list of IDs), `summary`. Prints the item with its new ID |
| `update <ID> <version>` | stdin: `{"fields": {...}}` with any of `title`, `status`, `parent`, `required_for_parent`, `priority`, `dependencies`, `area`, `goal`, `completion_criteria`, `summary`; add `"resolution": "..."` when setting `Completed` or `Rejected` |
| `note <ID>` | Append a dated notes entry. stdin: `{"topic": "...", "discussed": [...], "decided": [...], "open": [...]}`; add `"summary"` if the item has none yet |
| `doc <ID> <name>` | Print a notes or spec document: `version: <v>`, a blank line, the text. Names: `<ID>_notes.md`, `<ID>_spec.md`, `<ID>_spec_<topic>.md` |
| `put-doc <ID> <name> <version\|new> [--summary TEXT]` | Replace a document with the complete text from stdin, or create it with `new` (first notes need `--summary` if the item has none) |
| `retype <ID> <version> <type>` | Change the type (`Epic`, `Story`, `Task`). The ID's prefix is the type, so the item gets the next free ID of the new type; every reference (parents, dependencies, texts, notes, specs, `items/<ID>/`) follows. Prints the item under its new ID; refused when the new type breaks a lifecycle rule |
| `delete <ID> <version> [--cascade]` | Move to the trash; an item with children needs `--cascade` (the server answers `has_children` first) |
| `trash` | Items in the trash |
| `restore <ID> <version>` | Restore from the trash |

The date of a notes entry is set by the server. To revise notes or a spec,
read it with `doc`, change the text, and write it back with `put-doc` and the
version you read.

After `retype` the old ID is gone: use the new one from the answer, and read
the item again (new `version`). Changing the type changes the meaning of the
item, so ask the owner first (see [SKILL.md](SKILL.md)).

To reopen a closed item (only after the owner approved it), use `update`
with a status that is not final, e.g. `{"fields": {"status": "In progress"}}`.
This works for archived items too: the server moves them back to `TODO.md`
and drops `Resolution`. Then record the reason with `note`.

## Errors

- Exit 1: the server refused; stderr shows `HTTP <status> <code>: <message>`
  and `details`.
  - `version_conflict`: someone changed the item or document since you read
    it. Read it again, check whether your change still fits, then decide —
    never repeat the call blindly.
  - `parent_closed`: the item would stand under a closed parent.
    `details.items` lists the closed ancestors to reopen, from the top down.
    Ask the owner once whether to reopen all of them; if yes, reopen them in
    that order and repeat the call. Never create the item without a parent
    instead.
  - `children_still_active`: a parent cannot be closed while children are
    active; close or reparent them first.
  - Other rule violations name the blocking items in `details.items`. Resolve
    them as [format.md](format.md) describes, or ask the owner.
- Exit 2: wrong call or invalid JSON on stdin.
- Exit 3: server not reachable; see step 4 in [SKILL.md](SKILL.md). The
  server usually runs permanently in a container; after changes to the
  ToDo-Viewer it must be rebuilt (`./todo.sh update` there).

# Alarms

An alarm is a reminder at a fixed time: it rings in the ToDo-Viewer at `at`,
as long as the viewer runs. It is not work and not a note: no review date, no
completion criteria. Only with the `api` backend.

## When an alarm

- "Remind me at 3 pm", "on Thursday at 10 about STORY-012": an alarm, bound to
  the items or notes it is about (`targets`) or free with a `text`.
- A thought for later without a fixed time, or a reminder tied to an event:
  a note ([notes.md](notes.md)).
- Something you yourself should do later in this session: the scheduling
  tools of Claude Code, not an alarm.
- When it is doubtful which one is meant, ask once and briefly.

## Calling the helper

```
python3 ".claude-harness/runtime/scripts/alarms_api.py" [--project <name> | --source <name>] <command> [arguments]
```

Same project rules, exit codes 1–4, and approval for other projects
(`--source`) as for the backlog ([api.md](api.md), [SKILL.md](SKILL.md)).
Without arguments it prints the command list.

| Command | Use |
|---|---|
| `list [--due] [--all-projects]` | Alarms of the project (`--due`: only those ringing now) |
| `show <ALARM>` | One alarm: `at`, `status`, `targets` (each with label, title, `open`), `version` |
| `create` | stdin: `{"at": "...", "targets": ["STORY-012", "other:NOTE-003"]}` or `{"at": "...", "text": "..."}`; `text` is required only without targets. A target of another project is written `project:LABEL` (name from `sources`) |
| `update <ALARM> <version>` | stdin: any of `at`, `text`, `targets` (`[]` detaches all); a new `at` makes it wait again |
| `snooze <ALARM> <version> [--until T]` | Ring again later; default in one hour |
| `finish <ALARM> <version>`, `reopen <ALARM> <version>` | Done, or undo that |
| `delete <ALARM> <version>`, `restore <ALARM>` | To the trash and back |

## Rules

- Resolve relative times ("tomorrow morning", "in two hours") into a fixed
  time with the machine's local time zone as ISO 8601 with offset
  (`2026-10-20T09:00:00+02:00`), and name the result with weekday, date, and
  time in your answer. When the wording is ambiguous, ask before creating.
- Status: `Pending`, `Due` (ringing), `Snoozed`, `Done`, `Expired`. An alarm
  with targets expires on its own when none of them is open any more, and
  comes back when one is reopened. Done and expired alarms are removed by the
  viewer after 24 hours; there is nothing to clean up.
- Without asking: create, change, snooze, finish, and reopen alarms the user
  asked for. Deleting needs a clear request. Never remove anything for good.
- Do not check for ringing alarms on your own; the viewer shows them. When the
  user asks, read `list --due`.

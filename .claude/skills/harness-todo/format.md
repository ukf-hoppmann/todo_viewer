# Claude_Harness backlog format, version 2

The backlog lives in the folder configured as `[todo].path` below `[docs].root` in
`.claude-harness/config.toml` (default `docs/todo`). With the
`api` backend the ToDo-Viewer server writes this format and enforces its rules
(see [api.md](api.md)); with `files` the AI writes it directly. The files
are required only in `"files"` mode; in `"api"` mode the AI does not touch
them and the server may keep the backlog in a database instead.

```
<todo path>/
 ├─ TODO.md          active items (Open, In progress, Awaiting confirmation)
 ├─ archive.md       Completed and Rejected items, and the trash
 └─ items/<ID>/      optional notes and spec per item
```

Both files contain a paragraph before `## Work items` that starts with
`Format:` and contains `backlog format version 2`, e.g.

```
Format: Claude_Harness backlog format version 2. The rules are defined in the
`todo` skill of the claude-harness plugin (`skills/todo/format.md`).
```

Version 2 is the only valid format; it matches the ToDo-Viewer's Markdown
mirror. A backlog with another or no format line (e.g. version 1, which had
`Notes`/`Spec` fields and no `Uid`) is outdated and fails the check: ask the
owner how to convert it to version 2 (e.g. through the ToDo-Viewer) before
working with it.

Both files contain exactly one `## Work items` section. An empty section
contains the line `No entries.` (always in English, like the format line). `TODO.md` and `archive.md` form one backlog:
identifiers are unique across both, and references may cross between them.
Position and ordering do not determine status or hierarchy.

## Language

Field names, types, statuses, priorities, and section headings are English so
the format is usable without knowing the project's working language. Content
(titles, goals, criteria, summaries, notes, specs) is written in the project's
working language.

## Entry syntax

```markdown
- `STORY-001` **Concise title**
  - Uid: 3f0c2a9e-6b1d-4c57-9a8e-2d4b7c1e5f60.
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: YYYY-MM-DD.
  - Area: Project area.
  - Priority: Important.
  - Dependencies: None.
  - Goal: Describe the result. Continuation lines are indented
    by four spaces.
  - Completion criteria: State how the result is verified.
    One numbered criterion per line (`1. …`).
  - Summary: Short summary for the project owner.
```

Fields, in this order: `Uid`, `Type`, `Parent`, `Required for parent`,
`Status`, `Created`, `Area`, `Priority`, `Dependencies`, `Goal`,
`Completion criteria`, `Summary`, `Resolution`, `Deleted`. Other fields are
errors. The order is how the ToDo-Viewer writes entries; any order is read.

`Completion criteria` is a numbered list, one criterion per line (`1. …`,
`2. …`), never running text, so the ToDo-Viewer can show it as a list.

`Uid` is the item's permanent internal identity, assigned by the ToDo-Viewer.
Never create, change, or copy a `Uid`, and never invent a label; new entries
use a [placeholder](#new-entries) instead.

Identifiers use the pattern `PREFIX-NNN` (`EPIC-001`, `STORY-001`,
`TASK-001`), counted per type. They never change — not when an item changes
status, priority, parent, or scope. The one exception is a type change through
the API (`retype`): the prefix is the type, so the item gets a new ID and all
references follow; in files mode an item keeps its ID. References are written in backticks,
always with the label (never the `Uid`); several references are
comma-separated; no reference is `None`.

## Status model

- `Open`: Accepted backlog work that has not started.
- `In progress`: Work whose implementation or investigation has begun.
- `Awaiting confirmation`: Implementation and verification are complete, but
  project-owner confirmation is still pending.
- `Completed`: Explicitly confirmed as complete by the project owner.
- `Rejected`: Explicitly rejected by the project owner.

Passing tests, commits, merges, silence, and agent assessment do not constitute
completion confirmation.

## Work-item types

- `Epic`: A larger outcome containing multiple independently verifiable
  results.
- `Story`: An independently deliverable and observable result for a user,
  operator, or consuming system: a coherent capability, possibly delivered
  through several tasks.
- `Task`: Supporting work that does not by itself deliver an independent
  stakeholder-visible result.

An epic has no parent. A story may belong to one epic. A task may belong to one
story or directly to one epic when it enables multiple stories. Stories and
tasks may also be standalone (`Parent: None`).

`Parent` records outcome membership. `Dependencies` record prerequisites or
execution ordering. These relationships are independent. Neither graph may
contain cycles.

## Required fields

Every entry contains `Uid`, `Type`, `Status`, `Created`, `Area`, `Priority`,
`Dependencies`, `Goal`, and `Completion criteria`. A [new entry](#new-entries)
has no `Uid` and may omit `Created`.

A story or task additionally contains `Parent`. A parented story or task
contains `Required for parent` (`Yes` or `No`). Optional children never block
their parent.

A completed or rejected entry contains `Resolution`, recording the explicit
project-owner decision; active entries never contain it. Missing historical
evidence remains visible and is never invented.

Priorities are `Urgent`, `Important`, `Normal`, and `Prospective`. `Urgent`
and `Important` mark work that must proceed promptly; `Prospective` marks
work that can wait. `Normal` is the neutral default: use it whenever an item
is neither urgent/important nor explicitly deferred.

Areas are free text. An existing area is reused whenever it plausibly fits; a
new area is introduced only when no existing one fits.

## Parent lifecycle

- An epic needs at least one required child before it leaves `Open`, except
  to `Rejected`: an epic without children may be rejected.
- A parent cannot be `Awaiting confirmation` until every required child is
  `Awaiting confirmation` or `Completed`, and cannot be `Completed` until
  every required child is `Completed`.
- A required child that is `Rejected` therefore blocks its parent. When a
  required child is to be rejected, the agent asks the owner in the same step
  which of two options applies, and records the decision in the parent's
  notes:
  - the child becomes `Required for parent: No`; if the parent's `Goal` or
    `Completion criteria` name the child's content, they are adjusted in the
    same step. Adjusting the parent alone never lifts the block;
  - the parent is rejected as well. If a rejected required child remains
  anyway (e.g. after a status change outside the agent), the backlog check
  reports it and the agent asks the same question.
- A parent cannot be `Completed` or `Rejected` while any child — required or
  optional — is still active. Each child is closed (`Completed`/`Rejected`) or
  reparented first.
- Once all required children are `Completed`, the agent checks the parent's
  own completion criteria. If they are met, it sets the parent to
  `Awaiting confirmation` and tells the project owner; otherwise it reports
  what is missing. The owner confirms `Completed`.
- No active item stands under a closed (`Completed`/`Rejected`) parent,
  required or optional. This blocks creating an item under it, moving an
  item there, reopening a child of it, and restoring a child of it from the
  [trash](#trash). To place work there, reopen every closed ancestor first,
  from the top down, with the project owner's approval. Never fall back to
  creating the item without a parent.

## Optional fields

- `Summary`: Short, non-technical summary for the project owner. Give an
  item one as soon as it has notes.
- `Deleted`: Date (`YYYY-MM-DD`) the item was moved to the trash; see
  [Trash](#trash).

Notes and specs are not referenced from the entry; they are found through the
item's folder (see [Item files](#item-files)).

## New entries

Without the ToDo-Viewer (files mode), a new entry gets a placeholder instead
of a label and no `Uid`:

```markdown
- `NEW-login-dialog` **Simplify the login dialog**
  - Type: Task.
  - Parent: `STORY-012`.
  - …
```

- A placeholder is `NEW-` followed by a short name of `a-z`, `0-9`, and `-`,
  unique in the backlog.
- `Parent`, `Dependencies`, and other entries may reference placeholders. Its
  documents go into `items/NEW-<name>/` (`NEW-<name>_notes.md`, …).
- The ToDo-Viewer's sync assigns `Uid` and the next free label, replaces the
  placeholder in all references, renames folder and documents, and sets
  `Created` if it is missing.

## Item files

Items that need discussion or planning get a folder `items/<ID>/` whose name is
exactly the item ID. Small items need no folder. The folder does not depend on
the parent, so reparenting never moves files.

A notes or spec file belongs to the item through its folder and file name
alone; the entry has no field for it.

- `<ID>_notes.md`: Discussions and decisions: a head with the current state
  above a log that grows over time (see [Notes](#notes)).
- `<ID>_spec.md`: Technical summary (what and why, constraints, interfaces,
  affected files, acceptance criteria). It is always the current state: update
  it whenever something is decided or changes, and check it once more when the
  discussion ends. It holds no decision history (that is in the notes) and no
  step-by-step plan; a new session must be able to plan the implementation
  from it without asking.

Additional files are created only when needed, with a topic suffix such as
`<ID>_spec_<topic>.md`; the first file is never renamed. Notes and specs may be
revised when plans change, but changes of direction are recorded in the notes
instead of being silently overwritten.

Daily development reports do not belong in the backlog folder.

### Notes

A notes file has a title line, a head (`## State`) with the current state of
the item, and below it the log of dated entries:

```markdown
# STORY-012 — Simplify the login dialog

## State

- Goal/Status: One dialog for password and SSO; design agreed, spec current.
- Next step: Implement TASK-031.
- Open:
  - Whether SSO users may still set a password (2026-09-30)
- Decided:
  - One dialog instead of two (2026-09-30)
  - Errors shown inline, details in the spec (2026-09-30)
- References: Spec STORY-012_spec.md; TASK-031, TASK-032

State confirmed after entry 2026-09-30 — Dialog structure (1ddbc455ee9d)

## 2026-09-30 — Dialog structure

### Discussed

- …

### Decided

- …

### Open

- …
```

The head:

- Has exactly these markers in this order: `- Goal/Status:`, `- Next step:`,
  `- Open:`, `- Decided:`, `- References:`. Markers and headings are English
  and fixed; their content is in the project's language (the ToDo-Viewer may
  show them translated).
- Is replaced, not extended. It holds only what applies now: a decision that
  was superseded leaves the head and stays in the log.
- One point per line, with the date of the log entry it comes from.
  Technical details get one sentence and a reference to the spec.
- Has no length limit. More than 15 points under `- Decided:` give a hint
  (write the spec or split the item?), never a rejection. The same holds for
  notes of an epic or story changed while one of its children is `In progress`
  (does the discussion belong in that child's notes?).
- Ends with the stamp line
  `State confirmed after entry <YYYY-MM-DD> — <topic> (<checksum>)`, naming
  the last log entry and the checksum of the log when the head was last
  updated or confirmed. Never write or edit the stamp line by hand; the
  ToDo-Viewer or the helper sets it.

After every change to the notes, update the head or deliberately confirm that
it is still current; both set the stamp. Files mode: edit the head in the
file, then run
`python3 ".claude-harness/runtime/scripts/backlog.py" <backlog folder> --confirm-state <ID>`;
the backlog check at the end of a turn blocks while a notes file changed in
the session has a head that is not `current`. The head's state is:

- `missing`: no `## State` section;
- `stale`: no stamp, or its checksum differs from the current log;
- `current`: otherwise.

Checksum (shared with the ToDo-Viewer): take the log from its first entry
line `## YYYY-MM-DD — ` to the end, use LF line endings, strip spaces and tabs
at the end of every line, and end it with exactly one line break. The
checksum is the first 12 hex characters of SHA-256 over this text in UTF-8.

The log:

- Entries are dated (`## YYYY-MM-DD — Topic`) and use the headings
  `### Discussed`, `### Decided`, and `### Open`.
- Entries are only appended. An open point of an earlier entry that is
  resolved is closed explicitly in the new entry ("Open from <date> (X)
  resolved: …"). Changing an earlier entry is a deliberate correction and
  gives a hint.

Notes without a head get one the next time they are changed.

## Archive

Once an item is `Completed` or `Rejected` and has its `Resolution`, it moves
unchanged from `TODO.md` to `archive.md`. Its item folder stays in `items/`.
References to archived IDs remain valid. `archive.md` never contains active
items, except deleted ones in the [trash](#trash). The check reports a
misplaced entry as a notice; the ToDo-Viewer's sync also moves it.

Reopening an archived item moves it back to `TODO.md` with status `Open` or
`In progress` and without `Resolution`. The reason is recorded in the item's
notes (create them, and a `Summary`, if the item has none).

## Trash

Deleting an item does not remove it: it gets `Deleted: <YYYY-MM-DD>.` and
moves to `archive.md` unchanged otherwise, whatever its status (an item with
children is deleted together with them). Deleted items keep their ID and
files, and references to them stay valid, but the parent rules and the
placement rule for `archive.md` ignore them. Restoring removes `Deleted` and
moves an active item back to `TODO.md`. Only the project owner removes an item
from the trash for good (entry and `items/<ID>/`).

## Overview index

API mode: `backlog_api.py [--project <name>] index`. Files mode: for an overview
across `TODO.md` and `archive.md` without reading either file in full, run:

```
python3 ".claude-harness/runtime/scripts/backlog.py" <backlog folder> --index
```

It prints one line per item: `ID | Type | Status | Area | Title | Parent`;
deleted items show `(deleted <date>)` after their status.

Then load only the items that matter. API mode: `show <ID>`. Files mode:

```
python3 ".claude-harness/runtime/scripts/backlog.py" <backlog folder> --show <ID> [<ID> ...]
```

It prints each entry exactly as written, after a line `Source: TODO.md` or
`Source: archive.md`, and exits with 1 if an ID is not found. Never read
`archive.md` in full.

## Change authority

The agent may change without asking:

- notes and spec files: add, revise, or restructure whatever is relevant;
- the `Summary` field;
- status transitions `Open` → `In progress`, `In progress` →
  `Awaiting confirmation`, and back to `In progress`;
- wording fixes that do not change meaning;
- moving confirmed or rejected items to `archive.md`.

The agent proposes and waits for project-owner approval before:

- creating items, or deleting them unless the request clearly asks for it
  (deleting moves an item to the [trash](#trash); only the project owner
  removes it for good);
- changing the meaning of `Goal` or `Completion criteria`, or changing
  `Parent`, `Required for parent`, `Dependencies`, or `Priority`;
- setting `Completed` or `Rejected`, or reopening a closed item.

Reopening a closed item requires a recorded reason.

## Proposing new items

Propose an item only for concrete, relevant project work that was discussed
but intentionally not done now. Questions, discarded alternatives, temporary
debugging steps, and vague ideas without a next action are not items. A
proposal states title, type, goal, completion criteria, area, and priority.

Before proposing, use the overview index to check both files:

- If equivalent work exists, extend or reopen it instead of adding a duplicate.
- Place new stories and tasks under an existing epic or story that fits, even
  an archived one. Prefer proposing to reopen a closed parent over creating a
  new epic or story; create a new parent only when nothing plausibly fits.
- Load an archived item (`show`/`--show`) only when the index suggests it
  fits.

Never copy credentials, personal data, or unnecessary conversation quotes into
the backlog.

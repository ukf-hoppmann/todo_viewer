---
name: harness-architecture
description: Rules for working with the project's binding architecture rules (development suite). Use before discussing, designing, or planning how modules, functions, or components are added or changed, before writing a spec or changing code, when adding or changing architecture rules or scopes, when a requirement seems to conflict with the architecture, or when the architecture hook blocks an action.
---

# Architecture rules

## Before you start

1. Read `.claude-harness/config.toml` of the project the work belongs to (with
   subprojects, the session start lists each project and its folder; paths
   below are relative to that folder). The rules apply only if
   `[modules].development` is `true` and `[development].architecture` is not
   `false`; otherwise say so and stop.
2. The rules live in `<docs.root>/<development.path>/architecture.md`
   (default `docs/development/architecture.md`). Scopes listed in its
   `## Scopes` table live in `architecture/<Scope>.md` next to it.
3. If the rules file does not exist, tell the user and ask before creating it
   from `.claude-harness/runtime/templates/development/architecture.md` (scope files:
   `scope.md` there).

## Working with the rules

- Before discussing or planning how code is structured (modules, functions,
  components, interfaces), read the rules file and every scope whose path
  patterns match the files you expect to change. A design that ignores the
  rules has to be redone later. Read them in full with
  the Read tool; the hook only counts complete reads.
- A scope applies in addition to the rules file, never instead of it.
- In a repository with subprojects, a project may list rules of another
  project under `## Inherited rules` (for example the core's rules for a
  plugin). Read them as well; the hook requires them. If an inherited rule
  contradicts a rule of the project itself, the project's own rule wins:
  name the conflict (skill `harness-conflicts`).
- Check your plan against the rules before you present it, and follow them
  while implementing.
- If a requirement or design does not fit the rules, load skill
  `harness-conflicts` and follow it.

## What belongs into the architecture

The architecture says *what belongs where* and *what is mandatory*; it never
says *how*. The how lives in the interface docs (skill
`harness-interfaces`) and is linked from the rules, not repeated.

- **Required reading** (scope column, `Required on use` tables) is what you
  must read before changing or using something; the hook enforces it. A link
  in a rule is for looking up when needed; nothing enforces it. Make a file
  required only when changing or using the code without it would go wrong.
- Keep required files short: each one is read in full before every first
  change. Split long files and require only the part that matters.
- At most two levels of scopes (area, part). The Scopes table is the only
  list of what is mandatory; do not repeat it in prose elsewhere.
- Per area, a scope file starts from `scope.md` of the templates: a table of
  responsibilities (who owns a concern, what others do and must not do, link
  to the details), then the rules.

## Writing and changing rules

- Change rules and scopes only with the project owner's approval.
- Write rules in English. MUST, SHOULD, and MAY have their RFC 2119 meaning.
- Keep the rules file short and project-wide. Rules for one area go into a
  scope with precise path patterns.
- When you add or change a rule that can be checked mechanically (dependency
  direction, naming, forbidden imports), propose an architecture test and let
  the rule name it: `Enforced by: <test path>`.
- Scope table format: one row per scope, `| Scope | Paths | Covers |`. Scope
  names consist of one or more segments of lowercase letters, digits, and
  `-`, separated by `/`; the file is `architecture/<Scope>.md`, so
  `plugins/patient` lives in `architecture/plugins/patient.md`. A scope and a
  folder of the same name may coexist (`plugins.md` next to `plugins/`). Use at
  most two levels (area, part). Paths are patterns relative to
  the project root in backticks, comma-separated; `*` stays within one path
  part, `**` spans any number of parts. The session start reports errors in
  the table.
- Optional column `Required reading` (recognized by its header, between or
  after `Paths`, e.g. `| Scope | Paths | Required reading | Covers |`): files
  that must also be read in full before changing a file of the scope, e.g. its
  interface docs. Paths relative to the project root in backticks,
  comma-separated, no patterns, no leading `/`, no `..`; the files must exist.
  The hook requires them like the scope file, also for inherited scopes. Keep
  the list short: every listed file is read in full before each first change.
- Optional section `## Required on use` with the table `| Uses | Read |`, in
  the rules file (all project files) or in a scope file (only the scope's
  paths): `Uses` are identifiers in backticks (letters, digits, `_`, `$`, `.`),
  `Read` are files relative to the project root in backticks. When new code
  contains an identifier as a whole word, the hook blocks until those files
  were read in full. Use it for solutions that must not be rebuilt (e.g. the
  one error-reporting function). Inherited rules bring their tables along. The
  session start reports errors in the tables.
- Inherited rules table format: `| Project | Rules |`. Project is a name from
  `[projects]` of the root config or `root`; Rules are `architecture.md` or
  scope names of that project, in backticks. An inherited scope applies
  regardless of its path patterns; nothing is inherited further. The session
  start reports errors in this table too.

## The hook

A hook blocks the following until the rules file was read in full in this
session:

- presenting a plan (leaving plan mode);
- writing a backlog spec (`<ID>_spec.md`, `<ID>_spec_<topic>.md`), because it
  is the input for an implementation plan;
- the first change to a project file; here the file of every scope matching
  that path must have been read as well;
- new code that contains an identifier from a `Required on use` table, until
  its `Read` files were read in full (checked on the new text of Write, Edit,
  MultiEdit, NotebookEdit).
 After the context is compacted or cleared, read them again.
Harness files (`README.md`, `.claude-harness/`, the document folders) are not
checked. The hook does not see changes made through Bash; the rules apply to
them all the same.

## Public API reminder

A Stop hook reminds you when a file listed in `[development].public_api` was
changed; the steps are in skill `harness-interfaces`.

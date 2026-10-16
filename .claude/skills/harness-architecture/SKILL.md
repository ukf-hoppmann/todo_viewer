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
   from `.claude-harness/runtime/templates/development/architecture.md`.

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

## Writing and changing rules

- Change rules and scopes only with the project owner's approval.
- Write rules in English. MUST, SHOULD, and MAY have their RFC 2119 meaning.
- Keep the rules file short and project-wide. Rules for one area go into a
  scope with precise path patterns.
- When you add or change a rule that can be checked mechanically (dependency
  direction, naming, forbidden imports), propose an architecture test and let
  the rule name it: `Enforced by: <test path>`.
- Scope table format: one row per scope, `| Scope | Paths | Covers |`. Scope
  names use lowercase letters, digits, and `-`. Paths are patterns relative to
  the project root in backticks, comma-separated; `*` stays within one path
  part, `**` spans any number of parts. The session start reports errors in
  the table.
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
  that path must have been read as well.
 After the context is compacted or cleared, read them again.
Harness files (`README.md`, `.claude-harness/`, the document folders) are not
checked. The hook does not see changes made through Bash; the rules apply to
them all the same.

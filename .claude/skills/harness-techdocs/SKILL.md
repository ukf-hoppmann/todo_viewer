---
name: harness-techdocs
description: Rules for the project's technical documentation (README, architecture, interfaces, configuration, operations) describing the current state. Use when a change affects usage, components, APIs/CLIs/file formats/hooks, settings, or operations, when the techdocs hook reminds you, or when creating these documents.
---

# Technical documentation

## Before you start

1. Read `.claude-harness/config.toml` of the project the work belongs to (with
   subprojects, the session start lists each project and its folder; paths
   below are relative to that folder). If `[modules].techdocs` is not `true`,
   these rules do not apply — say so and stop.
2. The documents are `README.md` in the project root plus
   `<docs.root>/<techdocs.path>/<document>.md` for each entry in
   `[techdocs].documents`. Write them in `[docs].language`.

## Which document a change affects

| Change | Document |
|---|---|
| Usage, installation, prerequisites | `README.md` |
| Component added/removed, data flow, new dependency, architecture decision | `architecture` |
| API, CLI, file format, hook, event | `interfaces` |
| Setting added, changed, removed | `configuration` |
| Deployment, operation, failure modes | `operations` |

One change can affect several documents.

Backlog changes (items, notes, specs) never need technical documentation;
the backlog documents itself. The same holds for daily reports.

No update is needed when nothing visible from outside changes: refactoring
without behavior change, tests only, typos, formatting, internal renames,
dependency updates without behavior change. When in doubt, read the affected
document and check.

## Rules

- Documents describe the current state only. No history or changelog (that is
  the daily report); decisions appear briefly, with a link to the backlog
  notes that hold the reasons.
- Correct or remove outdated statements instead of appending to them.
- Update the documentation in the same change as the code, also inside a
  worktree.
- If a change affects a document the project does not keep, say so and
  propose adding it; do not skip it silently.
- When reporting a finished change, name the documentation updates or say
  briefly why none were needed.
- Create missing documents only after approval, from
  `.claude-harness/runtime/templates/techdocs/<document>.md` (README:
  `readme.md`). Never overwrite existing documents.

---
name: harness-techdocs
description: Rules for the project's technical documentation for people (README, architecture, interfaces, configuration, operations) describing the current state. Use when a change affects usage, components, APIs/CLIs/file formats/hooks, settings, or operations, when the techdocs hook reminds you, or when creating these documents.
---

# Technical documentation

These documents are for people and are written in `docs.language`. The
binding documentation for the AI (architecture rules, interface docs, catalog)
is English, lives in the development folder, and follows skills
`harness-architecture` and `harness-interfaces`. A change can
affect both. The technical docs are an overview: they summarize and link what
the development docs describe, see "Summarize or describe in full".

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

## Summarize or describe in full

An element (interface, building block, area rule) that the development docs
describe gets one summarizing sentence in `docs.language` and a relative
Markdown link to the development file in the technical docs. The summary must
give an overview without following the link; links from `docs.language` docs
to English files are fine. If the development docs do not cover the element
(no development suite, or no file for it), the technical docs describe it in
full.

| Document | Role |
|---|---|
| `README.md` | In full (introduction, installation, use). Links to every existing technical doc, so e.g. the configuration can be found |
| `architecture` | Overview of components, data flow, decisions. For binding rules link `<development.path>/architecture.md` and the scopes |
| `interfaces` | Overview table, one row per interface or area: purpose plus a link to the development file. Details only without development docs |
| `configuration` | In full (people set the settings) |
| `operations` | In full |

Existing projects: nothing is forced. Whoever edits a section that duplicates
the development docs replaces it with a summary and a link.

A change below `<development.path>/interfaces.md` or `interfaces/**` counts as
documentation upkeep for the reminder while the architecture part is on;
changes to the architecture rules do not.

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

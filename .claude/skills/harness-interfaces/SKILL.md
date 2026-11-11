---
name: harness-interfaces
description: Rules for the project's interface docs and the catalog of reusable building blocks (development suite). Use when designing, using, or changing an interface or a shared building block, when maintaining the catalog, or when the public API reminder appears.
---

# Interface docs and catalog

## Before you start

1. Read `.claude-harness/config.toml` of the project the work belongs to (with
   subprojects, the session start lists each project and its folder; paths
   below are relative to that folder). The rules apply only if
   `[modules].development` is `true` and `[development].architecture` is not
   `false`; otherwise say so and stop.
2. The index is `<docs.root>/<development.path>/interfaces.md` (default
   `docs/development/interfaces.md`); the files are below `interfaces/` next
   to it. A file `X.md` may sit next to a folder `X/` with its parts. The
   index is optional: when it does not exist, nothing is reported.
3. Create the index, interface docs, and catalogs only after approval, from
   `.claude-harness/runtime/templates/development/` (`interfaces.md`,
   `interface.md`, `catalog.md`). Never overwrite existing files.

## Who is it for

These documents are for the AI and are always English, whatever `docs.language`
is. They say *how* (signatures, formats, usage). *What belongs where* and what
is mandatory is decided by the architecture rules (skill
`harness-architecture`); people read the technical docs (skill
`harness-techdocs`), which summarize these docs and link to them.

## Rules

- Describe the current state only, no history. Update the docs in the same
  change as the code.
- Keep the most specific file current: the interface doc of the building block
  first, then its catalog row, then the index line.
- The index has one line per file below `interfaces/`, each with a link. Add
  or remove the line together with the file.
- Catalog: one file per owner (layer or module), one row per reusable building
  block: `| Building block | Purpose | Use when | Details |`; Details is a
  link to the interface doc.
- Before building something new, search the catalogs. Use what exists; do not
  rebuild it.
- A building block that several owners need belongs to the shared layer named
  in the architecture rules.
- When a document must be read before certain code is changed or used, it
  does not go here but into the architecture's `Required reading` or
  `Required on use` tables, which link to it.

## Public API reminder

If `[development].public_api` lists patterns and a file matching one was
changed, a Stop hook reminds you once per session and project. Then check that
the responsibilities in the architecture scope, the catalog, the interface
docs, and their links still match the change; update what does not. If nothing
needs to change, say so briefly.

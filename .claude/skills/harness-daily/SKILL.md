---
name: harness-daily
description: Rules for daily development reports (one report per day about material changes, written on the branch they were merged into). Use when the daily hook reminds you, or when asked to write, update, or look up what happened on a day.
---

# Daily development reports

## Before you start

1. Read `.claude-harness/config.toml` of the project the work belongs to (with
   subprojects, the session start lists each project and its folder; paths
   below are relative to that folder). If `[modules].daily` is not `true`,
   these rules do not apply — say so and stop.
2. Reports live in `<docs.root>/<daily.path>/<YYYY-MM-DD>_daily.md`, written
   in `docs.language`.
3. Run `python3 ".claude-harness/runtime/scripts/daily.py" pending`. It prints
   today's report path and the unrecorded commits on the checked-out branch.
   With subprojects every project has its own reports: add `--project <name>`
   (the reminder names the projects) and handle each project separately. If it
   says reports are unavailable here, stop: a report is written only after a
   change is merged, on the branch it was merged into — the branch checked out
   in the main checkout, or the base branch a change's worktree merged back
   into (skill `claude-harness:worktree`).

## Workflow

1. Decide which pending commits are material (below). Use the commits and
   what you know from this session; read diffs only where needed.
2. Nothing material: write nothing.
3. Otherwise read today's report if it exists, else start from
   `.claude-harness/runtime/templates/daily/daily.md`. Update existing rows
   instead of adding duplicates; bundle related commits into one row.
4. Finally run `python3 ".claude-harness/runtime/scripts/daily.py" ack` (with
   the same `--project`), also when nothing was material. Commits that only change the report or backlog
   folders are ignored, so committing the report does not trigger a new
   reminder. Commits acknowledged on one branch are not reported again after
   a merge into another.

## Materiality

Material is judged by the outcome, not the amount of activity: new, changed,
or removed behavior; bug fixes; relevant technical, documentation, or
operational changes; decisions. Exploratory notes, intermediate drafts, small
wording or formatting edits, and repeated decisions are not material on their
own.

The backlog documents itself: changes to backlog items, their status, notes,
or specs (planning, decisions, restructuring, completions) are not reported.
Backlog IDs appear only as evidence for the reported changes.

## Format

- Follow the template; translate headings into `docs.language`. Drop
  sections that stay empty. The summary is short prose.
- Evidence column: short commit hash and backlog ID. If the `todo` module is
  on and `<todo path>/items/<ID>/` exists, link the ID relative to the report;
  otherwise write the ID only. Do not add clock times; Git has them.

## Truthfulness

- Never claim verification that did not happen; say "not run" instead.
- Keep measured facts apart from assumptions and estimates.
- A report written for an earlier day is marked as written afterwards; gaps
  stay visible, nothing is invented.
- Keep incomplete, rejected, and deferred work visible.
- The date is today's local system date (`date +%F`), never a guess.
- Change only today's report. Fix an earlier report only with a dated
  correction note; the original statement stays.
- Never put secrets, credentials, or raw logs into a report.

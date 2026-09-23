===== TODO.md =====
# Backlog

Example backlog format version 2 for the test suite.

- `NOT-AN-ENTRY` **Entries before the work items section are ignored**
  - Status: Open.

## Work items

- `EPIC-001` **Viewer foundation**
  - Type: Epic.
  - Status: In progress.
  - Created: 2026-01-10.
  - Area: Core.
  - Priority: Dringend.
  - Goal: Build the base of the viewer
    so that backlogs can be read.
  - Completion criteria: All stories done.

- `STORY-001` **Parse backlog files**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: Open.
  - Priority: Wichtig.
  - Dependencies: None.
  - Summary: Reads TODO.md and archive.md.

- `TASK-001` **Write the parser**
  - Type: Task.
  - Parent: `STORY-001`.
  - Required for parent: Yes.
  - Status: In progress.
  - Priority: Important.
  - Dependencies: `TASK-000`, `STORY-000`.
  - Implementation: Regex based,
    one pass over the lines.
  - Verification: Unit tests.

- `TASK-002` **Optional polish**
  - Type: Task.
  - Parent: `STORY-001`.
  - Required for parent: No.
  - Status: Awaiting confirmation.
  - Dependencies: `TASK-001`.
  - Notes: `items/TASK-002/notes.md`.
  - Spec: items/TASK-002/spec.md, items/TASK-002/extra.md.

- `TASK-003` **No priority yet**
  - Type: Task.
  - Parent: `STORY-001`.
  - Status: Open.
  - Resolution: Leftover resolution
    spanning two lines.

## Other section

Free text ends the last entry.
===== archive.md =====
# Archive

Example backlog format version 2 archive.

## Work items

- `TASK-000` **Set up repository**
  - Type: Task.
  - Parent: `STORY-001`.
  - Status: Completed.
  - Priority: Important.
  - Resolution: Done in the initial commit.

- `STORY-000` **Discarded idea**
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: No.
  - Status: Rejected.
  - Resolution: Not needed.

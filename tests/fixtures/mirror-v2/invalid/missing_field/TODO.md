# Project Backlog

Active project work: open, in progress, or awaiting a project-owner decision.
Completed and rejected items are moved to `archive.md`; per-item notes and
specs live in `items/<ID>/`.

Format: Claude_Harness backlog format version 2. The rules are defined in
`docs/techdocs/interfaces.md` of the ToDo Viewer.

## Work items

- `EPIC-001` **Beispiel-Epic mit allen Kinderarten**
  - Uid: 0b6f2c1e-4d3a-4e8b-9c7d-1a2b3c4d5e01.
  - Type: Epic.
  - Status: In progress.
  - Created: 2026-10-01.
  - Area: Backend-API.
  - Priority: Important.
  - Dependencies: None.
  - Goal: Ein Epic mit einer Pflicht-Story, einer optionalen Story und
    einer abgeschlossenen Story im Archiv.
  - Completion criteria: Alle Pflicht-Kinder sind abgeschlossen.
  - Summary: Beispiel für ein laufendes Epic.

- `STORY-001` **Pflicht-Story mit Dokumenten**
  - Uid: 0b6f2c1e-4d3a-4e8b-9c7d-1a2b3c4d5e02.
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: Yes.
  - Status: In progress.
  - Created: 2026-10-02.
  - Area: Backend-API.
  - Priority: Urgent.
  - Dependencies: None.
  - Goal: Eine Story mit Notizen und Spec in `items/STORY-001/`.
  - Completion criteria: Die Kinder sind abgeschlossen.
  - Summary: Hat Notizen und eine Spec.

- `TASK-001` **Task mit Abhängigkeit**
  - Uid: 0b6f2c1e-4d3a-4e8b-9c7d-1a2b3c4d5e03.
  - Type: Task.
  - Parent: `STORY-001`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-10-03.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-002`.
  - Goal: Ein Task, der von einer anderen Story abhängt.
  - Completion criteria: Die Abhängigkeit ist erfüllt.

- `STORY-002` **Optionale Story**
  - Uid: 0b6f2c1e-4d3a-4e8b-9c7d-1a2b3c4d5e04.
  - Type: Story.
  - Parent: `EPIC-001`.
  - Required for parent: No.
  - Status: Open.
  - Created: 2026-10-04.
  - Area: Web-UI.
  - Dependencies: None.
  - Goal: Eine optionale Story; sie blockiert ihr Epic nicht.
  - Completion criteria: Sie lässt sich ohne Folgen ablehnen.

- `TASK-002` **Task ohne Parent, abhängig von einem neuen Eintrag**
  - Uid: 0b6f2c1e-4d3a-4e8b-9c7d-1a2b3c4d5e05.
  - Type: Task.
  - Parent: None.
  - Status: Open.
  - Created: 2026-10-05.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `NEW-login-dialog`.
  - Goal: Ein bestehender Eintrag darf einen Platzhalter nennen.
  - Completion criteria: Nach dem Sync steht hier das vergebene Label.

- `NEW-login-dialog` **Neuer Task aus der Cloud**
  - Type: Task.
  - Parent: `STORY-001`.
  - Required for parent: Yes.
  - Status: Open.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-001`.
  - Goal: Ein Eintrag ohne Uid und ohne Created, mit Platzhalter statt
    Label und einer Notiz in `items/NEW-login-dialog/`.
  - Completion criteria: Der Sync vergibt Label und Uid.

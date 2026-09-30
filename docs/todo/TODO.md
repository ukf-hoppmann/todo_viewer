# Projekt-Backlog

Aktive Projektarbeit: offen, in Arbeit oder wartend auf eine Entscheidung des
Projektverantwortlichen. Erledigte und abgelehnte Einträge werden nach
`archive.md` verschoben; Notizen und Specs pro Eintrag liegen in `items/<ID>/`.

Format: Claude_Harness-Backlog-Format Version 1. Die Regeln sind im
`todo`-Skill des claude-harness-Plugins definiert (`skills/todo/format.md`).

## Work items

- `EPIC-002` **Backlog-Pflege in der UI**
  - Type: Epic.
  - Status: In progress.
  - Created: 2026-09-27.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: None.
  - Goal: In der UI lassen sich Items anlegen und löschen, ihre
    Freitext-Felder (Titel, Goal, Completion criteria, Summary, Area,
    Parent, Dependencies) bearbeiten sowie Notes-Einträge und Specs
    schreiben. Die UI nutzt dafür die Endpunkte aus `EPIC-001`.
  - Completion criteria: Alle Pflichtkinder sind abgeschlossen; jede
    genannte Funktion ist in der UI bedienbar, Fehlercodes der API
    werden übersetzt angezeigt, und der Projektverantwortliche hat die
    Bedienung geprüft.
  - Summary: Alles, was künftig ein Agent über die API am Backlog
    ändern kann, soll auch direkt in der Oberfläche möglich sein.
  - Notes: `items/EPIC-002/EPIC-002_notes.md`.

- `STORY-018` **Typ eines Items in der UI ändern**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-09-30.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `TASK-002`.
  - Goal: Im Detail-Panel lässt sich der Typ eines Items ändern. Die UI ruft
    den Typwechsel der API auf, wählt das Item danach unter seiner neuen ID
    aus und zeigt den Hinweis der API, dass Techdocs und andere Stellen
    außerhalb des Backlogs die alte ID noch nennen können.
  - Completion criteria: Ein Item lässt sich im Detail-Panel auf einen
    anderen Typ umstellen; danach ist es unter der neuen ID ausgewählt und
    die Ansichten zeigen es dort. Regelverstöße der API (z. B. Epic mit
    Parent) erscheinen als übersetzte Meldung ohne Änderung. Der Hinweis auf
    mögliche Verweise außerhalb des Backlogs ist sichtbar und enthält die
    alte und die neue ID. Texte sind in Deutsch und Englisch vorhanden;
    Typecheck, Lint und Web-Tests sind grün.
  - Summary: Den Typ eines Items direkt in der Oberfläche ändern, samt
    Hinweis auf Verweise außerhalb des Backlogs.
  - Notes: `items/STORY-018/STORY-018_notes.md`.

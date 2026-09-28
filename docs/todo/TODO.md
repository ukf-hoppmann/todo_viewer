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

- `STORY-012` **Felder im Bearbeiten-Modus ändern**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-09-28.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-006`.
  - Goal: Im Detail-Panel öffnet ein Knopf „Bearbeiten“ ein Formular für
    Titel, Goal, Completion criteria, Summary, Area, Parent und
    Dependencies. Speichern schreibt alle Änderungen in einem Schritt,
    Abbrechen verwirft sie. Bei einem Versionskonflikt bleiben die Eingaben
    erhalten und der aktuelle Stand wird angezeigt.
  - Completion criteria: Alle genannten Felder sind über den
    Bearbeiten-Modus änderbar; ohne Bearbeiten-Modus ist nichts
    versehentlich änderbar; Regelverstöße und Versionskonflikte werden
    verständlich angezeigt; Komponententests decken Speichern, Abbrechen und
    Konflikt ab.
  - Summary: Einträge lassen sich über einen eigenen Bearbeiten-Modus
    ändern, nicht durch versehentliches Klicken.
  - Notes: `items/STORY-012/STORY-012_notes.md`.

- `STORY-013` **Items in der UI anlegen**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-09-28.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-007`.
  - Goal: Ein Knopf „Neu“ oben legt ein Epic, eine Story oder einen Task
    ohne Parent an; „Kind anlegen“ im Detail-Panel belegt den Parent vor.
    Der Dialog fragt Typ und Pflichtfelder ab und wählt das neue Item danach
    aus.
  - Completion criteria: Anlegen funktioniert über beide Einstiege;
    Pflichtfelder und Regelverstöße werden im Dialog gemeldet;
    Komponententests vorhanden.
  - Summary: Neue Einträge lassen sich direkt in der Oberfläche anlegen.
  - Notes: `items/STORY-013/STORY-013_notes.md`.

- `STORY-014` **Löschen und Papierkorb-Ansicht**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: Yes.
  - Status: Awaiting confirmation.
  - Created: 2026-09-28.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-011`.
  - Goal: Im Detail-Panel verschiebt „Löschen“ ein Item in den Papierkorb;
    hat es Kinder, zeigt die UI sie als Warnung und löscht sie erst nach
    Bestätigung mit. Eine eigene Ansicht „Papierkorb“ neben Baum,
    Abhängigkeiten und Kanban listet gelöschte Items und bietet
    Wiederherstellen und endgültiges Löschen.
  - Completion criteria: Löschen, Wiederherstellen und endgültiges Löschen
    sind in der UI bedienbar, jeweils samt Kindern; endgültiges Löschen
    verlangt eine Bestätigung; Komponententests vorhanden.
  - Summary: Gelöschte Einträge landen in einer eigenen Papierkorb-Ansicht
    und lassen sich zurückholen oder endgültig entfernen.
  - Notes: `items/STORY-014/STORY-014_notes.md`.

- `STORY-015` **Notes-Einträge und Specs in der UI schreiben**
  - Type: Story.
  - Parent: `EPIC-002`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-09-28.
  - Area: Web-UI.
  - Priority: Normal.
  - Dependencies: `STORY-009`.
  - Goal: Im Dokument-Dialog lässt sich ein Notes-Eintrag (Thema, Discussed,
    Decided, Open) anhängen und eine Spec in einem Textfeld mit
    Markdown-Vorschau bearbeiten oder neu anlegen. Beim ersten Notes-Eintrag
    fragt die UI nach einer Summary, falls keine vorhanden ist.
  - Completion criteria: Notes-Einträge und Specs lassen sich in der UI
    schreiben; Versionskonflikte bei Specs werden gemeldet, ohne die Eingabe
    zu verlieren; Komponententests vorhanden.
  - Summary: Notizen und Specs lassen sich direkt in der Oberfläche
    schreiben.

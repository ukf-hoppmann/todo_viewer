# `STORY-075` — Backlog im Markdown-Spiegel

Grundlage: `EPIC-007_spec.md`, Abschnitte 7.3, 10; Format aus `TASK-035`.

## Umfang

- `MirrorCodec` des Plugins `backlog` für `TODO.md`, `archive.md`,
  `items/**`: aktive Items nach `TODO.md`, geschlossene und gelöschte nach
  `archive.md`; Dokumente als eigene Einträge (`kind` `backlog.document`,
  `uid` = Item-`uid` + Name).
- Vorlage: Parser und Editoren des Altcodes
  (`backend/todo_viewer/infrastructure/markdown/`), angepasst kopiert; Edits
  ändern nur das betroffene Feld oder verschieben den betroffenen Eintrag.
- `SyncParticipant`: lädt und schreibt Items, Abhängigkeiten, Bereiche
  (fehlender Bereich wird angelegt), Dokumente; neue Items über
  `ElementRegistry.register`.
- Prüfungen nach Format Version 2 mit Fehlercodes aus `TASK-035`.

## Tests

Test zuerst: Golden-Files (Lesen und Schreiben), Platzhalter-Auflösung,
Prüfregeln; Integration mit dem Sync-Dienst.

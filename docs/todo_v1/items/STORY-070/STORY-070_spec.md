# `STORY-070` — Papierkorb

Grundlage: `EPIC-007_spec.md`, Abschnitt 9.

## Umfang

- Port `ChildrenProvider` je Elementtyp (Plugins melden an, welche Kinder ein
  Element hat und wie es dargestellt wird: Titel, Typ-Badge).
- Operationen: `delete_element(uid, version, cascade)` (antwortet
  `has_children` ohne `cascade`), `restore_element`, `list_trash(projects)`,
  `purge_element` (nur HTTP, `mcp=False`).
- Wiederherstellen prüft die Regeln des besitzenden Plugins (Port
  `RestoreGuard`, z. B. kein aktives Item unter geschlossenem Parent).
- Endgültig löschen entfernt Element, Plugin-Daten, Dokumente und
  Verknüpfungen (Plugins melden über Port `Purger`).
- Frontend: Hauptroute „Papierkorb“ mit Liste, Checkboxen, Sammelaktionen,
  Bestätigungen; Kinder im Detailpanel gestrichelt und durchgestrichen.

## Tests

Test zuerst: Kaskade, Vorfahren-Regel bei Sammelaktionen, Restore-Regel.

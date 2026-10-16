# `STORY-072` — Backlog bearbeiten

Grundlage: `EPIC-007_spec.md`, Abschnitte 6, 9; Regeln aus dem Backlog-Format (`format.md` des
Harness, Abschnitte Parent lifecycle, Status model, Archive).

## Umfang

- Domäne: Lebenszyklus- und Parent-Regeln (Vorlage
  `src_old/backend/todo_viewer/domain/lifecycle.py`, `editing.py`, `creation.py`,
  `retype.py`), angepasst an `uid`.
- Operationen: `create_item`, `update_item(uid|label, version, fields,
  resolution?)`, `retype_item`, `move_item(uid, version, parent, position)`,
  `reopen_ancestors`. Fehlercodes wie heute (`parent_closed`,
  `children_still_active`, `version_conflict`, …).
- Archiv: geschlossene Items sind ein Status, kein Umzug; „Archiv“ ist ein
  Filter. (Der Spiegel schreibt sie nach `archive.md`, `STORY-075`.)
- Bereiche: Auswahl je Projekt, „＋ Neuer Bereich…“ legt an (`STORY-060` Frage 9).
- Ereignisse: `backlog.item.changed` (public), `backlog.item.status_changed`
  (für `notes`).
- Frontend: Inline-Felder, Formular, Typ-ändern-Dialog mit Hinweis auf alte
  und neue ID, Neu-Typen Epic/Story/Task im Slot `workspace.create-types`,
  Drag & Drop im Baum (`STORY-060` Frage 10).

## Tests

Test zuerst für jede Regel (Tabellentests der Domäne); Operationen gegen
echte SQLite; UI-Tests für Formular, Konflikt, Drag & Drop.

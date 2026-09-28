# EPIC-001 — Notizen

## 2026-09-27 — Zuschnitt und Grundsatzentscheidungen

### Discussed

- Eine Liste benötigter Endpunkte aus einer anderen Session (Übersicht,
  Dokument lesen, Feld ändern, Quellen, Einzelabruf, Lean Index, Anlegen,
  Löschen, weitere Felder, Notes/Specs schreiben).
- Ob die Agent-Endpunkte eine eigene API werden oder in `/api/v2` gehören.

### Decided

- Die Endpunkte werden in `/api/v2` integriert, keine zweite API
  (Architekturregel 2 „One HTTP contract“). UI und Agent nutzen denselben
  Vertrag und dieselben Services.
- `TODO.md` kann später durch eine Datenbank ersetzt werden. Deshalb
  adressiert der Vertrag Items nur über `source_id` und ID; `location`,
  `line` und Dateipfade gehören nicht in die API. Konflikte werden über ein
  undurchsichtiges Versions-Token erkannt.
- Lean Index als eigener Endpunkt `GET /api/v2/index` mit festem Schema,
  kein Query-Parameter an `/backlog`.
- Notes: strukturierter Append-Endpunkt für datierte Einträge; Specs werden
  mit Versions-Token vollständig ersetzt. Beides über das Item adressiert.
- Parent-Lifecycle-Regeln werden serverseitig im Domain durchgesetzt, nicht
  mehr vom Skill.
- Löschen wird abgelehnt, solange Parent- oder Dependency-Verweise bestehen.
- Die Anpassung des todo-Skills selbst gehört ins Claude_Harness-Repo, nicht
  in dieses Backlog.

### Open

- Wie der Server für Agenten erreichbar ist (dauerhaft laufend, bei Bedarf
  gestartet, CLI-Adapter ohne Server) — wird in `STORY-010` entschieden.
- UI-Funktionen für Anlegen, Löschen und Freitext-Bearbeitung laufen im
  eigenen Epic `EPIC-002` (2026-09-27 angelegt).

## 2026-09-28 — Wiedereröffnet für Area im Index

### Discussed

- Claude_Harness TASK-015 lädt den Backlog zweistufig: erst die flache Liste, dann gezielt einzelne Items. Die Spalte Area hilft dabei, die Relevanz eines Items vor dem Laden einzuschätzen.

### Decided

- Auf Wunsch des Projektverantwortlichen wiedereröffnet; der Index bekommt das Feld area über einen Pflicht-Task unter STORY-004. Das Ziel von STORY-004 bleibt unverändert.

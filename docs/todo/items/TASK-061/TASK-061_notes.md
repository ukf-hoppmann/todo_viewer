# TASK-061 — Mindmap: Abhängigkeiten zwischen Themen ein- und ausblenden

## State

- Goal/Status: Vom Owner am 2026-11-18 bestätigt (`Completed`, archiviert). Umgesetzt (Server: Port, Domain `dependency_links`, `TreeOut.links`, OpenAPI-Typen; Client: `liftLinks`, Schalter `showDependencies`, gestrichelte Linien mit Pfeil und Anzahl); Tests grün, Techdocs und Daily nachgezogen; `Awaiting confirmation`.
- Next step: keiner, der Task ist abgeschlossen (2026-11-18); die Browserprüfung mit dem laufenden Viewer wurde nicht ausgeführt.
- Open:
- Decided:
  - Die Zusammenfassung der Linien liegt in der Server-Domain, weil dort der wirksame Knoten berechnet wird (2026-11-17)
  - Nur Abhängigkeiten innerhalb eines Projekts; auch in der Gesamtansicht keine Linien zwischen Projekten (2026-11-17)
  - `BacklogItem` liefert jetzt `dependencies`; Port und Adapter sind erweitert (2026-11-18)
  - Der Server lässt Linien zwischen Eltern- und Kindknoten stehen, nur Paare im selben Knoten entfallen; der Client kürzt sie bei gefalteten Ästen (`liftLinks`) (2026-11-18)
- References: Spec `TASK-061_spec.md`; Story-Spec `STORY-101_spec.md`; Commits 90194cb3 (Server) und d41ce0f8 (Client)

State confirmed after entry 2026-11-18 — Bestätigung (6442a27eee33)

## 2026-11-17 — Anlage aus der Planung der Story

### Discussed

- Planung der Story `STORY-101` mit dem Owner; Entscheidungen 2 und 3 der Planung betreffen diesen Task.
- Beim Lesen des Codes fiel auf: `BacklogItem` (`application/ports.py`) und der Adapter liefern keine Abhängigkeiten, der Task ist größer als das Ticket vermuten lässt.

### Decided

- Zusammenfassung in der Server-Domain
- Nur innerhalb eines Projekts

### Open

- Nichts offen.

## 2026-11-18 — Umsetzung

### Discussed

- Plan mit dem Owner abgestimmt (6 Abschnitte); offener Punkt war, ob der Server auch Linien zwischen Eltern- und Kindknoten entfernt. Entscheidung: nur Paare im selben Knoten entfallen, der Client kürzt über `liftLinks`.
- Server: `BacklogItem.dependencies`, `ItemFact.dependencies`, `dependency_links` (rein, `domain/assignment.py`), `TreeStats.links`, `TreeOut.links` (`LinkOut`), Schema `schema.d.ts` mit `scripts/gen-api.sh` neu erzeugt. Der Statusfilter gilt auf beiden Enden einer Abhängigkeit.
- Client: `liftLinks` (`domain/tree.ts`), UI-Zustand `showDependencies` (Standard aus), Schalter in `MapFilters`, Linien als React-Flow-Kanten unter den Baumkanten. In der Gesamtansicht werden die Links der Projektbäume zusammen gelegt; Knoten-UIDs sind projektübergreifend eindeutig.
- Tests: 6 Domain-Tests, 2 Integrationstests (Endpunkt), 6 `liftLinks`-Tests, 4 Seitentests und 1 Schaltertest; Mindmap-Client-Tests 210 grün, `tsc -b` sauber, Lint nur die 5 alten Fehler in `usePersistentState.ts`. Beim ersten Gesamtlauf schlug `startApp.test.tsx` einmal mit Zeitüberschreitung fehl, einzeln und danach grün (Last, nicht die Änderung).
- Nicht ausgeführt: Browserprüfung mit dem laufenden Viewer.

### Decided

- `TASK-061` steht auf `Awaiting confirmation`

### Open

- Der Owner bestätigt oder nennt Fehlendes

## 2026-11-18 — Bestätigung

### Discussed

- Der Owner hat `TASK-061` als abgeschlossen bestätigt.

### Decided

- `TASK-061` ist `Completed` und nach `archive.md` verschoben

### Open

- Open from 2026-11-18 (Der Owner bestätigt oder nennt Fehlendes) resolved: bestätigt

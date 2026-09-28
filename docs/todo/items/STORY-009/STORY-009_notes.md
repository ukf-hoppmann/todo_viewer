# STORY-009 — Notizen

## 2026-09-28 — Umsetzung

### Decided

- Dokumente werden über Item-ID und Namen (Dateiname, z. B.
  `STORY-003_spec.md`) adressiert; `ItemOut` liefert `documents` statt der
  Pfadlisten `notes`/`spec`. Der pfadbasierte Endpunkt
  `GET /sources/{id}/document` ist entfallen, die UI liest über das Item.
- Specs: `PUT` ersetzt mit Inhaltsversion; `version: null` legt eine neue Spec
  an. Neue Namen müssen `<ID>_spec.md` oder `<ID>_spec_<thema>.md` lauten.
- Notes: nur Anhängen über einen strukturierten Endpunkt; Datum vom Server.
  Die erste Notiz legt die Datei an, trägt `Notes` ein und verlangt eine
  Summary, falls keine vorhanden ist. Die Regel wird vor dem Schreiben der
  Datei geprüft, damit ein abgelehnter Eintrag nichts hinterlässt.
- Neue Notes-Dateien beginnen mit `# <ID> — <Titel>`, sprachneutral.
- Backlog-Dateien und Dokumente eines Ordners teilen sich einen Lock.

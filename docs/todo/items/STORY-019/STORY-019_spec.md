# STORY-019 Spec: Architekturregeln öffnen

Gemeinsame Festlegungen: siehe `EPIC-003_spec.md`.

## Was und warum

Die Regeln in `docs/development/architecture.md` verbieten heute jede andere Speicherung als Markdown (Regel 1). Bevor Code entsteht, müssen sie beide Backends erlauben. Änderungen werden erst nach Freigabe des Projekteigners verbindlich.

## Änderungen

- `docs/development/architecture.md`, Regel 1 neu: Backlog-Daten liegen hinter dem Port `BacklogRepository`/`DocumentStore`; je Projekt ist Markdown oder die zentrale Datenbank das Speicher-Backend. Es gibt keine App-eigene Kopie außerhalb des gewählten Backends. Die Markdown-Regeln (atomar, Zeilenenden, Konflikt statt Überschreiben, Golden-Tests) gelten weiter für den Markdown-Adapter. Regel 2 (eine HTTP-Schnittstelle) bleibt.
- `docs/development/architecture/backend.md`: neue Regeln
  - DB-Adapter leben in `infrastructure/database/`, keine SQL-Bibliothek in `domain`/`application` (import-linter-Vertrag in `pyproject.toml` ergänzen).
  - Schemaänderungen nur über versionierte Migrationen; Migrationen sind vorwärts-only und getestet.
  - Jeder Adapter besteht dieselbe Contract-Suite (STORY-020).
  - Sync zwischen Backends ist ein Use Case in `application`, keine Adapter-Logik.
- Verweise anpassen: `docs/techdocs/architecture.md`, Tests, die Regel 1 als „Markdown ist Wahrheit“ zitieren.

## Abnahme

Freigabe des Projekteigners; `scripts/check.sh` (inkl. import-linter) grün; keine Stelle in Doku oder Tests widerspricht den neuen Regeln.

## Nicht Teil dieser Story

Kein Code außer der import-linter-Konfiguration.

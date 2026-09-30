# STORY-023 Spec: Sync DB ⇄ Markdown

Gemeinsame Festlegungen: siehe `EPIC-003_spec.md`.

## Was und warum

Ein Use Case in `application` überträgt alle Daten eines Projekts zwischen der DB und einem Markdown-Ordner: `TODO.md`, `archive.md`, alle Items samt `items/<Label>/…`-Dokumenten und Papierkorb. Er arbeitet nur über die vorhandenen Ports, damit beide Seiten austauschbar bleiben.

## Ablauf

1. **Vorschau (Standard).** `POST /api/v2/sources/{source_id}/sync` mit `{"direction": "to_md"|"from_md", "confirm": false}` ändert nichts und liefert die Vorschau: `created`, `changed`, `unchanged` (Anzahl) und `missing` (Einträge, die auf der Zielseite stehen, auf der Quellseite aber fehlen), jeweils mit Label und Titel; für Dokumente ebenso.
2. **Ausführen.** `{"confirm": true}` führt aus. `missing` wird nur mit `"delete_missing": true` gelöscht, sonst bleibt es stehen und wird im Ergebnis als übersprungen gemeldet.
3. **Konflikte.** Vergleich je Item über `Item.version` und Dokumentversion; Änderungen auf beiden Seiten gelten als Überschreibung der Zielseite und stehen als `changed` in der Vorschau. Zwischen Vorschau und Ausführung wird die Zielseite erneut gelesen; hat sie sich verändert → `sync_stale` (Vorschau neu holen).

## Entscheidungen

- **`to_md`** rendert aus den DB-Daten über `EntryRenderer` und die Vorlagen (`EmptyBacklogTemplates`, Sprache aus der Projektsprache bzw. `[docs].language`), schreibt über den Markdown-Adapter am `sync_path`, legt fehlende Dateien/Ordner an. Die Ausgabe ist normalisiert, nicht byte-gleich zu früheren Dateien.
- **`from_md`** liest über den Markdown-Adapter (`load` am `sync_path`) und schreibt über den DB-Adapter (Transaktion). Nicht lesbare Backlogs (`parse_error`, `unsupported_format`) brechen vor jeder Änderung ab. Dateien im Item-Ordner, die nicht `_notes.md`/`_spec*.md` sind, werden in der Vorschau als `skipped` gemeldet.
- **Backend-Wechsel** ist kein eigener Endpunkt: `from_md` in ein `database`-Projekt, danach `PUT /sources/{id}` mit `backend=database`; zurück analog mit `to_md`. Die Reihenfolge (erst Sync, dann Umschalten) steht in der UI-Story.
- **Fehlercodes:** `sync_path_missing`, `sync_source_invalid`, `sync_stale`, `sync_same_backend` (Projekt hat kein zweites Ziel).
- Sync ist eine Operation pro Projekt und läuft unter dem Projekt-Lock (`KeyedLocks`).

## Dateien

Neu: `application/services/sync.py`, `domain/sync.py` (Vorschau-Datentypen, Vergleichslogik, keine I/O), `api/v2` Endpunkt + Schemas. Ports: keine neuen, ggf. `BacklogRepository.load` und `DocumentStore.read` für beide Adapter am jeweiligen Ort (der Sync bekommt zwei Repositories/Stores per Konstruktor).

## Abnahme

Tests: export → import → export identisch; Import gibt gleiche `Item.version`; Vorschau ändert nichts; `missing` wird nur mit `delete_missing` gelöscht; Abbruch bei kaputter Quelle lässt beide Seiten unverändert; `sync_stale`; Dokumente inklusive Themen-Specs; Papierkorb bleibt Papierkorb.

## Nicht Teil dieser Story

Automatische Spiegelung, UI (STORY-024).

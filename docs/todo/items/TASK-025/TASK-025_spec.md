# TASK-025 — Spec: Notes-Spiegel: Port und Datei-Adapter mit atomarem Schreiben

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-047), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Der Dateiweg zum Spiegel (STORY-047). Den Sync-Ablauf baut TASK-026.

## Schon vorhanden
- `domain/notes_markdown.py` (TASK-024): `render_note`, `parse_note`, `render_topics`, `parse_topics`.
- Muster für atomares Schreiben und Konflikt: `infrastructure/markdown/text_file.py`, Fingerprints und Sync-Status: `domain/sync.py`, `application/services/syncstatus.py`.
- `Source.sync_path`/`path`: wo der Spiegel-Ordner eines Projekts liegt (`domain/source.py`, `Source.markdown_path`-artige Hilfe).
- **Importlinter-Regel** in `pyproject.toml`: `todo_viewer.infrastructure.markdown` darf `todo_viewer.domain.notes` und `application.services.notes` **nicht** importieren (Architektur §3).

## Festgelegte Entscheidung
Der Notes-Datei-Adapter lebt **nicht** in `infrastructure/markdown/`, sondern in einem neuen Paket `infrastructure/notes_files/`, damit die Regel „der Markdown-Adapter weiß nichts von Notes“ unangetastet bleibt. Zusätzliche Importlinter-Verträge: `notes_files` importiert weder `infrastructure.markdown` noch `infrastructure.database`.

## Zu tun
1. Port `NotesMirror` in `application/ports.py` (Typen in `domain/`): `read(source) -> MirrorSnapshot` (Topics, Notes mit Triggers/Links, Dokumente als Text, alle als geparste Werte), `write(source, snapshot, expected_fingerprint | None)`, `fingerprint(source) -> str` (ohne Schreiben; Hash über Namen und Inhalte der Dateien in `notes/`), `delete(source, labels)` (nur auf ausdrücklichen Aufruf).
2. Adapter `infrastructure/notes_files/mirror.py`: Ordner `<Spiegel-Ordner>/notes/`, Dateien `NOTE-001.md`, `NOTE-001_notes.md`, `NOTE-001_spec.md`, `NOTE-001_spec_<topic>.md`, `topics.md`. Schreiben jeder Datei: temporäre Datei im selben Ordner + Umbenennen; vor dem Schreiben prüfen, ob die Datei seit `read` unverändert ist, sonst Konfliktfehler (`mirror_conflict`, `ConflictError`); Zeilenenden der vorhandenen Datei bleiben erhalten.
3. Nur Notes im Zustand „in Gebrauch“ und archivierte (nicht der Papierkorb) werden gespiegelt.
4. Bootstrap-Verdrahtung des Adapters (`bootstrap.py`), kein Aufruf aus einem normalen Request.
5. Importlinter-Verträge in `pyproject.toml` ergänzen.

## Dateien
`application/ports.py`, `domain/notes_markdown.py` (nur falls Typen fehlen), `infrastructure/notes_files/__init__.py`, `mirror.py` (neu), `bootstrap.py`, `pyproject.toml`, Tests `backend/tests/unit/infrastructure/test_notes_mirror.py` (neu), `tests/contract/` falls ein Port-Vertrag für Spiegel sinnvoll ist (sonst eigener Test).

## Nicht anfassen
`infrastructure/markdown/*`, `infrastructure/database/*`, den Backlog-Sync, `domain/sync.py` (außer neuen, getrennten Typen).

## Tests (zuerst)
Schreiben legt Ordner und Dateien an; Lesen gibt denselben Snapshot zurück (Round-Trip über die Dateien); Datei von außen geändert → Konflikt, nichts überschrieben; kein halb geschriebener Zustand bei Abbruch (Fehler beim Umbenennen simulieren); `fingerprint` ändert sich bei jeder Änderung und verändert nichts; fehlender Ordner → leerer Snapshot; Importlinter hält.

## Stoppen und fragen
Wenn `Source` keinen Spiegel-Ordner für Datenbank-Projekte ohne Sync-Pfad hat (dann gibt es kein Ziel), oder wenn der Spiegel-Ordner eines Markdown-Projekts (Primärquelle = Dateien) für `notes/` anders heißen soll.

## Abnahme
Adapter-Tests grün, Importlinter hält, `scripts/check.sh` grün.

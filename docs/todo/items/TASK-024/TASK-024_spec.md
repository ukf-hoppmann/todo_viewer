# TASK-024 — Spec: Notes-Dateiformat: Serialisieren und Parsen mit Golden-Files

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-047), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Nur die Umwandlung (reine Funktionen, keine Dateien, kein Port). Adapter in TASK-025, Sync in TASK-026, UI in TASK-027.

## Schon vorhanden
- Modelle in `domain/notes.py` (`Note`, `Topic`, `Link`, `Trigger`, `LinkTarget`, Enums). Dokumente einer Note sind eigene Dateien (`<LABEL>_notes.md`, `<LABEL>_spec.md`) und gehören in TASK-025, nicht in diese Funktionen.
- Vorbild für Golden-Files: `backend/tests/golden/` und die Tests in `tests/characterization/`.

## Festgelegtes Format
Feldnamen sind **englisch** (wie in `TODO.md`), Inhalte in der Sprache des Nutzers.

Datei `NOTE-001.md`:
```
# NOTE-001
Summary: <eine Zeile>
Status: waiting
Topic: Projekte / Umbau            # Pfad aus Topic-Namen, leer wenn keins
Review: 2026-11-07T08:00:00Z
Mode: any
Archived: false
Triggers:
- time 2026-10-12T08:00:00Z [fired 2026-10-12T08:00:00Z]
- event MeinProjekt:STORY-003 Completed [already_met]
- topic_due
Links:
- reference MeinProjekt:STORY-004
- reference topic:NOTE-007
- origin MeinProjekt:STORY-009

<Langtext, Markdown, unverändert>
```
- Zeitpunkte als UTC mit `Z`. Labels, nie `uid`. Link-Ziel `Projekt:Label` (Item), `topic:TOPIC-001`, `note:NOTE-007` (gleiches Projekt).
- Die Zeile `Links:` enthält die Links ohne die der Rolle `trigger` (sie sind durch `event`-Auslöser dargestellt).
- Leerer Langtext: nach der Kopfzeile endet die Datei.
Datei `topics.md`: eingerückte Liste, ein Eintrag je Topic: `- TOPIC-001 | <Name> | due=<Zeitpunkt oder leer>`; zwei Leerzeichen Einrückung je Ebene.

## Zu tun
1. Neues Modul `domain/notes_markdown.py` (nur Standardbibliothek): `render_note(note, triggers, links, topic_path) -> str`, `parse_note(text) -> ParsedNote` (Note-Felder, Trigger-Beschreibungen, Link-Beschreibungen **ohne** `uid`/`id`), `render_topics(topics) -> str`, `parse_topics(text) -> list[ParsedTopic]`. Zeilenenden bleiben erhalten (`\n`; ein Aufruf mit `\r\n` bleibt `\r\n`).
2. Strenge Fehler: unbekannte Kopfzeile, ungültiger Status, kaputter Zeitpunkt → `InvalidValueError`/eigener `NoteFormatError` mit Zeilennummer (kein stilles Überspringen).
3. Namen mit `|` oder Zeilenumbruch im Topic-Namen: Format maskiert sie (`\|`) und der Parser macht es rückgängig; im Test abgedeckt.

## Dateien
`domain/notes_markdown.py` (neu), Tests `backend/tests/unit/domain/test_notes_markdown.py` (neu), Golden-Files `backend/tests/golden/notes/` (`note_full.md`, `note_minimal.md`, `topics.md`).

## Nicht anfassen
Ports, Adapter, Sync, Datenbank, die Dokumente der Note.

## Tests (zuerst)
Round-Trip je Golden-File: voll (alle Felder, drei Auslöser, drei Linkarten, Langtext mit Markdown, Umlauten und Leerzeilen), minimal (nur Summary), leerer Langtext, `\r\n`, Topic mit `|` im Namen, Topic-Tiefe 3; Format-Fehler mit Zeilennummer.

## Stoppen und fragen
Wenn eine Eigenschaft der Note im Format fehlt (z. B. `Deleted`, `Created`/`Updated`): sie gehören **nicht** hinein (Papierkorb wird nicht gespiegelt); sonst fragen.

## Abnahme
Golden-Files pinnen das Format; Round-Trip-Tests grün; `scripts/check.sh` grün.

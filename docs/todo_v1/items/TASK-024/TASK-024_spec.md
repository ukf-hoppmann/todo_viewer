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

## Festgelegtes Format (Stand 2026-10-14)
Feldnamen sind **englisch** (wie in `TODO.md`), Inhalte in der Sprache des Nutzers. Ein Eintrag je Zeile (Auslöser, Links), damit Git sauber zusammenführt. Änderungen gegenüber dem ersten Entwurf: Topic als Label statt Pfad; `Created`, `Updated`, `Archived`, `Deleted` gehören dazu (Papierkorb und Archiv werden mitgespiegelt); Notes ohne Label; Zähler.

Datei `NOTE-001.md`:
```
# NOTE-001
Summary: <eine Zeile>
Status: waiting
Topic: TOPIC-001                  # Label; leer, wenn keins; new:<Name> = label-loser Eintrag in topics.md
Review: 2026-11-07T08:00:00Z      # leer, wenn keins
Mode: any
Created: 2026-10-01T09:30:00Z
Updated: 2026-10-12T08:00:00Z
Archived: false
Deleted:                          # Zeitpunkt, wenn im Papierkorb; sonst leer
Triggers:
- time 2026-10-12T08:00:00Z [fired 2026-10-12T08:00:00Z]
- event MeinProjekt:STORY-003 Completed [fired 2026-10-12T08:00:00Z] [already_met]
- topic_due
Links:
- reference MeinProjekt:STORY-004
- reference topic:TOPIC-002
- reference note:NOTE-007
- origin MeinProjekt:STORY-009

<Langtext, Markdown, unverändert>
```
- Zeitpunkte als UTC mit `Z`. Labels, nie `uid`. Link-Ziel `Projekt:Label` (Item), `topic:TOPIC-001`, `note:NOTE-007` (gleiches Projekt).
- Die Zeile `Links:` enthält die Links ohne die der Rolle `trigger` (sie sind durch `event`-Auslöser dargestellt; der Import legt sie wieder an).
- **Note ohne Label** (in der Cloud angelegt): Datei `new-<kurzname>.md`, erste Zeile `# NEW`, sonst gleich. `Created` und `Updated` dürfen dann fehlen (der Import setzt den Zeitpunkt des Imports). Verweise auf sie: `note:new-<kurzname>`.
- Leerer Langtext: nach der Kopfzeile endet die Datei.
- Änderungshinweise (`note_notices`) gehören nicht ins Format.

Datei `topics.md`: eingerückte Liste, ein Eintrag je Topic, zwei Leerzeichen Einrückung je Ebene: `- TOPIC-001 | <Name> | due=<Zeitpunkt oder leer> | created=<Zeitpunkt> | deleted=<Zeitpunkt oder leer>`. Ein Topic ohne Label: `- NEW | <Name> | due=…` (`created` und `deleted` dürfen fehlen).

Datei `counters.md`: je Typ die höchste je vergebene Nummer, eine Zeile je Typ: `NOTE: 15`, `TOPIC: 7`. Sie sorgt dafür, dass Labels auch nach einem Neuaufbau aus den Dateien nie wiederverwendet werden.

## Zu tun
1. Neues Modul `domain/notes_markdown.py` (nur Standardbibliothek): `render_note(note, triggers, links, topic_label) -> str`, `parse_note(text) -> ParsedNote` (Note-Felder, Trigger-Beschreibungen, Link-Beschreibungen **ohne** `uid`/`id`), `render_topics(topics) -> str`, `parse_topics(text) -> list[ParsedTopic]`, `render_counters(counters) -> str`, `parse_counters(text) -> dict`. Zeilenenden bleiben erhalten (`\n`; ein Aufruf mit `\r\n` bleibt `\r\n`).
2. Strenge Fehler: unbekannte Kopfzeile, ungültiger Status, kaputter Zeitpunkt → `InvalidValueError`/eigener `NoteFormatError` mit Zeilennummer (kein stilles Überspringen).
3. Namen mit `|` oder Zeilenumbruch im Topic-Namen: Format maskiert sie (`\|`) und der Parser macht es rückgängig; im Test abgedeckt.

## Dateien
`domain/notes_markdown.py` (neu), Tests `backend/tests/unit/domain/test_notes_markdown.py` (neu), Golden-Files `backend/tests/golden/notes/` (`note_full.md`, `note_minimal.md`, `note_new.md`, `note_trashed_archived.md`, `topics.md`, `counters.md`).

## Nicht anfassen
Ports, Adapter, Sync, Datenbank, die Dokumente der Note.

## Tests (zuerst)
Round-Trip je Golden-File: voll (alle Felder, drei Auslöserarten mit `fired` und `already_met`, vier Linkarten, Langtext mit Markdown, Umlauten und Leerzeilen), minimal (nur Summary), Note ohne Label, Note im Papierkorb und archiviert, leerer Langtext, `\r\n`, Topic mit `|` im Namen, Topic-Tiefe 3, Topic ohne Label, Zähler; Format-Fehler mit Zeilennummer.

## Stoppen und fragen
Wenn eine Eigenschaft der Note oder des Topics im Format fehlt, die in der Datenbank steht und hier nicht aufgeführt ist, oder wenn ein Wert nicht verlustfrei abbildbar ist. (Änderungshinweise sind ausdrücklich nicht Teil des Formats.)

## Abnahme
Golden-Files pinnen das Format; Round-Trip-Tests grün; `scripts/check.sh` grün.

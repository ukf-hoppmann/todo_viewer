# EPIC-001 — Auswirkungen auf den Claude_Harness

Stand: 2026-09-28. Übergabe an eine eigene Session, die den Harness
(`/Users/hoppmann/Documents/GitHub/Claude_Harness`) anpasst. Der ToDo-Viewer
selbst wurde für den Harness **nicht** verändert. Maßgeblich für die API ist
`docs/techdocs/interfaces.md` im ToDo-Viewer (Abschnitt „Nutzung durch
Agenten“) und das OpenAPI-Schema `web/src/api/openapi.json`.

## Was sich grundsätzlich ändert

Agenten pflegen Backlogs über die HTTP-API des ToDo-Viewers
(`http://localhost:5411/api/v2`) statt `TODO.md`, `archive.md` und
`items/<ID>/` direkt zu lesen und zu schreiben. Der Server prüft Format und
Parent-Regeln, vergibt IDs, schreibt Notes-Einträge im Format und erkennt
konkurrierende Änderungen über Versions-Tokens.

## Probleme und nötige Anpassungen im Harness

### 1. todo-Skill arbeitet direkt auf den Dateien

- `skills/todo/SKILL.md` und `format.md` beschreiben Lesen und Schreiben der
  Markdown-Dateien. Die Mechanik muss auf API-Aufrufe umgestellt werden
  (z. B. per `curl`); die Regeln zur Entscheidungsbefugnis (was der Agent
  ohne Rückfrage darf, was der Projektverantwortliche bestätigt) bleiben im
  Skill. Der Server kennt keine Freigaben: Er prüft Regeln, aber nicht, ob
  der Projektverantwortliche zugestimmt hat.
- Zuordnung Projekt → Quelle: Der Agent sucht in `GET /sources` den Eintrag,
  dessen `path` der Backlog-Ordner ist; fehlt er, `POST /sources` mit
  `{path}`. Bei Subprojekten ist jeder Backlog eine eigene Quelle.
- `backlog.py --index` wird durch `GET /index?source_id=…` ersetzt.
- Einzelne Items, auch archivierte: `GET /items/{source_id}/{id}` statt
  `archive.md` zu lesen.
- Ändern: `PATCH` mit `{version, fields}`; bei 409 `version_conflict` neu
  lesen und die Änderung prüfen, nicht blind wiederholen.
- Anlegen: `POST /items`; die ID vergibt der Server (nächste freie Nummer
  des Typs über aktiv und Archiv).
- Notes: `POST /items/{source_id}/{id}/notes` mit
  `{topic, discussed, decided, open, summary?}`; Datum setzt der Server. Der
  erste Eintrag legt `items/<ID>/<ID>_notes.md` an, trägt `Notes` ein und
  verlangt eine Summary. Freie Umstrukturierung einer Notes-Datei ist über
  die API nicht vorgesehen (nur Anhängen).
- Specs: `PUT /items/{source_id}/{id}/documents/<ID>_spec[_thema].md` mit
  `{content, version}` (`null` = neu). Andere Namen sind nicht erlaubt.
- Status Completed/Rejected braucht `resolution`; der Server archiviert und
  holt beim Zurücksetzen zurück.

### 2. Der automatische Backlog-Check greift nicht mehr

- `mark_backlog_dirty.py` (PostToolUse auf Write/Edit) markiert Backlogs nur,
  wenn der Agent die Dateien selbst bearbeitet. Über die API schreibt der
  Server; `check_backlog.py` am Turn-Ende läuft dann nie.
- Entscheidung nötig: Check entfallen lassen (der Server erzwingt die Regeln)
  oder nach API-Aufrufen (z. B. PostToolUse auf Bash mit `curl … /api/v2`)
  auslösen.

### 3. Formaterweiterungen des Viewers, die `backlog.py` als Fehler meldet

- Neues Feld `Deleted: <YYYY-MM-DD>.` für Items im Papierkorb
  (`STORY-011`). `backlog.py` meldet „unknown fields: Deleted“.
- Items im Papierkorb liegen in `archive.md`, auch mit nicht
  abgeschlossenem Status. `backlog.py` meldet „must be Completed or
  Rejected“.
- Nötig: `Deleted` in `KNOWN_FIELDS` und `format.md` aufnehmen; Einträge mit
  `Deleted` von der Archiv-Statusregel und von den Parent-Regeln ausnehmen
  (der Viewer zählt sie für die Regeln nicht mit); `--index` sollte sie
  ausblenden oder markieren.
- Löschen läuft über den Papierkorb: `DELETE /items/…` (bei Kindern 409
  `has_children`, mit `cascade=true` samt Nachfahren), `GET /trash`,
  `POST /trash/…/restore`, `DELETE /trash/…` (endgültig, samt
  `items/<ID>/`). `format.md` sollte die Bedeutung von `Deleted` und das
  Wiederherstellen beschreiben.

### 4. Format-Schlüssel sind lokalisiert

Vorgabe des Projektverantwortlichen: Schlüssel und Markierungen bleiben
englisch, nur echter Fließtext darf in der Projektsprache stehen; übersetzt
wird in der UI.

- `backlog.py` akzeptiert `Keine Einträge.` als Leer-Markierung
  (`_EMPTY_MARKERS`); im ToDo-Viewer-Backlog stand diese Zeile in
  `archive.md`. Der Viewer kennt nur `No entries.`. Harness-Vorlagen und
  -Regeln sollten nur `No entries.` schreiben und akzeptieren.
- Die Format-Kennung steht in `TODO.md` als deutscher Satz
  („Claude_Harness-Backlog-Format Version 1“). Der Viewer erkennt sie
  tolerant, verlangt aber irgendeine Kennung (sonst Quellenproblem
  `unsupported_format`). Sauber wäre eine englische Kennungszeile, z. B.
  „Claude_Harness backlog format version 1“.

### 5. Worktrees und Branches

- Die API ändert die Dateien am konfigurierten Pfad der Quelle, also im
  Haupt-Checkout, nicht im Worktree eines Agenten. Das widerspricht der
  Worktree-Regel „Backlog-Änderungen gehören in denselben Branch“.
- Optionen: Backlog-Änderungen bewusst im Haupt-Checkout committen; oder
  den Worktree-Backlog als eigene Quelle registrieren (dann zwei Quellen für
  ein Projekt).
- Die API committet nicht. Wer die geänderten Dateien committet, regelt der
  Harness (bisher: Agent im selben Change).

### 6. Erreichbarkeit

- Der Container läuft dauerhaft (`restart: unless-stopped`), nur an
  `127.0.0.1:5411`. `GET /api/v2/health` liefert `{status: "ok", api: "2"}`.
- Wie ein Agent reagiert, wenn der Server nicht läuft, regelt der Harness
  (Entscheidung in `STORY-010`): z. B. Hinweis an den Projektverantwortlichen
  oder Rückfall auf direkten Dateizugriff.
- Der Container muss nach Änderungen am Viewer neu gebaut werden
  (`./todo.sh update`), sonst spricht er noch die alte API.

### 7. Regeln doppelt vorhanden

- Die Parent-Regeln stehen jetzt im Viewer-Domain (`lifecycle.py`) und in
  `backlog.py`. Unterschiede heute:
  - Der Viewer lehnt nur neue Verstöße ab; Altlasten blockieren nicht.
  - „Epic braucht Pflichtkind vor Verlassen von Open“ gilt im Viewer nicht
    für `Rejected` (ein leeres Epic bleibt ablehnbar).
  - Zusätzlich im Viewer: unbekannte Verweise, Summary-Pflicht bei Notes,
    Verweis-Schutz beim Löschen.
- Entscheidung nötig, welche Seite maßgeblich ist, damit sie nicht
  auseinanderlaufen.

### 8. Kleinigkeiten

- Neue Notes-Dateien beginnen mit `# <ID> — <Titel>` (sprachneutral).
- Der Viewer bricht lange Feldwerte bei 76 Zeichen mit vier Leerzeichen
  Einzug um und schreibt IDs und Pfade in Backticks.
- Neue Felder werden am Ende eines Eintrags eingefügt, nicht in
  Format-Reihenfolge; neu angelegte Einträge stehen in Format-Reihenfolge.
- Ein aus dem Archiv zurückgeholter Eintrag landet am Dateiende von
  `TODO.md` (bestehendes Verhalten).
- `SessionStart` meldet „Backlog: docs/todo/TODO.md“; der Hinweis sollte auf
  die API verweisen.

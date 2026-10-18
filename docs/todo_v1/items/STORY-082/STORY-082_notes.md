# STORY-082 — Datenübernahme aus dem alten Viewer

## 2026-10-16 — Entscheidungen

### Decided

- Altprioritäten: High → Urgent (Dringend), Medium → Important (Wichtig), Low → Normal.
- Keine freien Zusatzfelder im neuen Schema.
- Harter Schnitt, kein Parallelbetrieb; nur der Projektinhaber nutzt den Viewer.

## 2026-10-17 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- **Zuschnitt.** Paket `viewer/app/import_legacy/` (Schicht `app`, darf alle Plugins kennen, nie den Altcode): `legacy_schema.py` (eigene SQLAlchemy-Tabellen als Kopie der Spalten, nur lesend), `mapping.py` (reine Regeln: Priorität, Label-Zerlegung, Zusatzfeld-Eintrag, Bereichs-`uid`s), `reader.py` (alte DB → Datensätze, in der Reihenfolge der alten `position`/`id`), `writer.py` (Datensätze → neue Datenbank, ein Transaktion mit SQL auf den Tabellen der Plugins), `report.py` (Zahlen je Typ, Abweichungen), `command.py` und `__main__.py` (`--legacy-db`, `--target`, `--dry-run`, `--backup-dir`, `--log-dir`).
- **Ablauf.** Altes Schema prüfen → Projekte prüfen (Markdown-primäres Projekt: Abbruch mit Name, `STORY-060` Frage 1) → alle Werte prüfen (Priorität, Status, Typ: bei einem unbekannten Wert Abbruch mit der ganzen Liste, nichts wird geschrieben) → Ziel prüfen (muss leer sein: nur das eingebaute Projekt, keine Elemente) → Backup, wenn die Zieldatei schon besteht → in einer Transaktion schreiben. `--dry-run` läuft vollständig gegen eine Kopie in einem Wegwerf-Ordner und lässt Ziel, Backups und Logs unberührt.
- **Abbildungen.** Wie in der Spec; dazu festgelegt:
  - Projekt: `id` → `uid`; `backend = database` mit `sync_path` → Spiegel-Ordner, `mirror_enabled` = nicht `mirror_disabled`, `auto_sync` übernommen, Richtung `both`; ein Projekt namens „Allgemein“ wird das eingebaute; Reihenfolge nach der alten `position`.
  - Elemente: `uid` und Label bleiben (Typ `epic`/`story`/`task`/`note`/`topic`); `deleted` → `deleted_at`; Label-Verlauf und Zähler (`max` aus Labels und `note_counters`) werden gesetzt. Erzeugte `uid`s (Bereiche, Wecker, Verknüpfungen, Auslöser, Hinweise) sind `uuid5` aus stabilen alten Schlüsseln, damit ein zweiter Lauf dasselbe ergibt.
  - Items: Priorität/Status/Typ geprüft; Bereich → `backlog_areas` je Projekt; `location` entfällt (das Archiv ist der Endstatus); Abhängigkeiten ohne Ziel werden gemeldet und weggelassen; Zusatzfelder → ein Eintrag „Übernommene Zusatzfelder“ in `<LABEL>_notes.md` (Datum = Tag des Imports; legt das Dokument an, falls keines da ist).
  - Notes: Status `due` (abgeleitet, falls je gespeichert) → `waiting`; Dokumente, Topics, `review_at`, `trigger_mode`, `archived` übernommen. Links → `workspace_links` über Projekt und Label des Ziels (unauflösbar: gemeldet und weggelassen). Auslöser: `event` → `notes_triggers` samt Verknüpfung `trigger`; `topic_due` → `topic_date`; `time` → Wecker mit Ziel Note (Text = Kurzfassung; `fired_at` gesetzt → Status `Due`, sonst `Pending`). Hinweise → `notes_notices` (`project_unreachable` entfällt, gemeldet).
  - Nicht übernommen und im Bericht genannt: `ui_state`, `sync_entries` (der neue Sync fängt ohne Stand an), `note_counters` ohne Treffer.
- **Frage 35** (Widerspruch in der Spec): Abschlusskriterium 1 sagt „liest die alte DB und Markdown-primäre Ordner“, der Umfang sagt „bricht ab, wenn ein Projekt noch Markdown-primär ist“. Annahme: der Umfang gilt (Frage 1: erst im alten Viewer in seine DB spiegeln). Steht in `STORY-060`.
- **Tests.** Zuerst eine synthetische alte Datenbank, die ein Test-Hilfsprogramm aus der Schema-Kopie erzeugt (`tests/helpers/server/legacy_db.py`, Inhalt als Python-Daten; keine echte Datenbank, keine Datei aus `configs/`), unter `tests/fixtures/legacy-db/` liegt die Beschreibung der Fälle (`README.md`) und ein JSON der erwarteten Zahlen. Die Fälle: Prioritäten (alle neuen, alle alten, deutsche, leer, unbekannt → Abbruch), Zusatzfelder, Zeit-Auslöser, Ereignis-Auslöser mit Verknüpfung, Links aller Arten, Hinweise, Papierkorb und Archiv, Markdown-primäres Projekt → Abbruch, Ziel nicht leer → Abbruch, Zähler, Dry-Run (Ziel unverändert), zweiter Lauf auf frische Datenbank = erster, und ein Rundlauf: die übernommene Datenbank startet im echten Viewer (alle Plugins) und liefert die Daten über die HTTP-Schnittstelle.

### Decided

1. Reine Regeln und Bericht (mit Tests). 2. Lesen der alten Datenbank. 3. Schreiben (Projekte, Elemente, Items, Dokumente). 4. Schreiben (Notes, Links, Auslöser, Wecker, Hinweise). 5. Befehl, Dry-Run, Backup, Log. 6. Integration: Rundlauf, Techdoku, Checks.

### Open

- Frage 35 steht in `STORY-060`.

## 2026-10-17 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Wie geplant umgesetzt (`viewer/app/import_legacy/`). Abweichungen vom Plan: die Hinweise stehen in der Reihenfolge nach den Wecker-Auslösern, weil Wecker eigene Elemente (Labels `ALARM-n`) brauchen und die Zähler erst am Ende aus allen Labels entstehen; `PRAGMA defer_foreign_keys` erlaubt Parents in beliebiger Reihenfolge.
- Die Zieldatenbank muss leer sein (nur das eingebaute Projekt): ein zweiter Lauf auf dieselbe Datenbank bricht ab, statt zu mischen. „Wiederholbar“ heißt hier: gleiche Eingabe, frische Datenbank, gleiches Ergebnis.
- Die Techdoku steht in `docs/techdocs/neubau-server.md`, „Datenübernahme aus dem alten Viewer“.

### Decided

- Abschlusskriterien geprüft: (1) Befehl liest die alte DB, bricht bei Markdown-primären Projekten ab, schreibt nach einem Backup (`test_import_legacy.py`: Abbruch, Backup, Befehl); (2) `uid`s und Labels bleiben (Items, Topics, Notes); (3) alle Prioritäten-Fälle, unbekannte brechen mit der ganzen Liste ab (`test_import_legacy_rules.py`, `test_import_legacy.py`); (4) Zusatzfelder und Zeit-Auslöser nach den Annahmen; (5) Bericht mit Zahlen und Abweichungen; (6) zweiter Lauf = erster. Dazu: Dry-Run ändert nichts; die übernommene Datenbank läuft im Viewer (HTTP-Rundlauf).
- `scripts/check-next.sh` und `scripts/check.sh` grün. Status: `Awaiting confirmation`.

### Open

- Nicht geprüft: eine echte alte Datenbank (kein Zugriff, Regel der Sitzung), also auch nicht ältere Schemastände des alten Viewers; Leistung bei sehr großen Datenbanken; Zeitzonen-lose Zeitstempel (werden unverändert übernommen).
- Der erste Sync nach der Übernahme startet ohne Stand (`sync_entries` wird nicht übernommen); ob er die Ordner ohne Konflikt angleicht, hängt vom Inhalt der Ordner ab und ist ungeprüft.
- Frage 35 steht in `STORY-060`.

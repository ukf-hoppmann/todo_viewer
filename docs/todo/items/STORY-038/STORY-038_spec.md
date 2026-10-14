# STORY-038 — Spec: Datenmodell für Topics, Notes und Links

## Was und warum
Das relationale Modell ist die Grundlage für alle weiteren Stories. Es folgt den Regeln aus STORY-037. Alle Namen in Code und API sind englisch, Texte stehen in der Sprache des Projekts.

## Modell (Vorschlag)
- **Topic:** `uid` (nur Adapter), `project`, `label` (`TOPIC-001`), `name`, `parent` (Topic), `due_at` (optional, Termin), Zeitstempel, `deleted`. Tiefe höchstens `notes.max_topic_depth` (Standard 3).
- **Note:** `uid`, `project`, `label` (`NOTE-001`), `summary` (Pflicht, eine Zeile), `body` (optional), `status` (`waiting`, `due`, `snoozed`, `done`, `dropped`, `promoted`), `topic`, `review_at`, `trigger_mode` (`any` Standard, `all`), Zeitstempel, `archived`, `deleted`.
- **Link:** Quelle ist eine Note; Ziel ist ein Item (Projekt plus Item-Label, siehe STORY-037), ein Topic oder eine Note; `role` (`reference`, `trigger`, `origin`). Eine Tabelle, in beide Richtungen abfragbar.
- **Trigger:** gehört zu einer Note; `kind` (`time`, `event`, `topic_due`); bei `time` ein Zeitpunkt, bei `event` ein Link mit Rolle `trigger` und ein Zielstatus (`In progress`, `Awaiting confirmation`, `Completed`, `Rejected`), bei `topic_due` das Topic der Note; `fired_at` (leer, solange nicht eingetroffen) und `already_met` (Kennzeichen „bei Anlage bereits erfüllt").
- **Dokumente einer Note:** Notizen und Specs wie bei Items, benannt `<LABEL>_notes.md`, `<LABEL>_spec.md`, `<LABEL>_spec_<topic>.md`; Speicherung angelehnt an `infrastructure/database/documents.py`.
- **Zähler:** pro Projekt und Typ (Topic, Note); vergebene Labels werden nie wiederverwendet, auch nicht nach Löschen.

## Regeln
- Labels ändern sich innerhalb eines Projekts nie.
- Projektwechsel einer Note: im Zielprojekt neu anlegen (neues Label, neues Topic nach Wahl des Aufrufers) und die alte Note löschen (Papierkorb). Links der alten Note werden dabei geprüft (siehe STORY-041).
- Gespeicherte Zeitpunkte sind eindeutig (UTC); Anzeige und Eingabe in der Zeitzone des Rechners.
- Der Eltern-Verweis eines Topics darf keine Schleife bilden; Verschieben prüft die Tiefe des ganzen Teilbaums.

## Konfiguration
`notes.max_topic_depth` (Standard 3) und `notes.review_days` (Standard 30) als globale Optionen in der Viewer-Konfiguration (`configs/config.json`).

## Betroffene Dateien
`domain/notes.py` (neu), `application/ports.py`, `infrastructure/database/schema.py`, `migrations.py`, `notes.py` (neu), `domain/retype.py` und `application/services/retype.py` (Links mitführen).

## Abnahme
- Migration vom bestehenden Stand auf einen Stand mit den neuen Tabellen läuft, auch auf einer leeren Datenbank (Test).
- Contract-Suite für `NoteRepository`: Label-Vergabe, Zähler pro Projekt und Typ, Tiefe, Link-Rollen, Auslöser-Modus, Dokumente.
- Ein Link auf ein Item übersteht `retype` des Items.
- Projektwechsel erzeugt im Zielprojekt eine Note mit neuem Label und löscht die alte.

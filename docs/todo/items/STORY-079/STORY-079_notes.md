# STORY-079 — Notes im Markdown-Spiegel

## 2026-10-17 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- **Zuschnitt.** `MirrorCodec` (`notes/*.md`: Notes `NOTE-<n>.md` und `new-<kurzname>.md`, ihre Dokumente `<LABEL>_notes.md`/`<LABEL>_spec[_<thema>].md`, `topics.md`; `counters.md` wird ignoriert und beim nächsten Schreiben gelöscht) und `SyncParticipant` im Plugin `notes` (`infrastructure/mirror/`). Eintragsarten `notes.topic`, `notes.note`, `notes.document` (Dokument wie im Backlog: `uid` = `<Note-uid>/<notes|spec|spec_<thema>>`, Platzhalter `<new-kurzname>/<endung>`).
- **Verweise.** In den Dateien stehen Ziele als `<Projektname>:<LABEL>` (Items, Notes anderer Rubrik), `topic:<LABEL>` und `note:<LABEL>`; in den Einträgen stehen sie als blanke Labels bzw. Platzhalter (`new-idee`, `NEW-login-dialog`, `new:<Topicname>`), damit der Sync die Platzhalter über alle Plugins hinweg ersetzen kann. Dazu muss der Codec den Projektnamen kennen: `MirrorConfig` bekommt `name`, und ein Codec darf `for_project(name)` anbieten (Kern, klein; Frage 32). Ein Ziel mit anderem Projektnamen bleibt als `Name:LABEL` stehen und wird über Projektname und Label aufgelöst.
- **Einträge.** Topic: `name`, `due_at`, `archived_at`, `deleted_at`, Verweis `parent`. Note: `summary`, `status` (nur gespeicherte Werte; `due` ist abgeleitet und kein gültiger Wert in Dateien), `review_at`, `mode`, `archived`, `deleted_at`, `body` (ohne Zeilenumbrüche am Ende), `triggers` (Art, Status, `fired_at`, `already_met`), Verweise `topic`, `reference`, `origin`, `trigger_targets` (die Ziele der Ereignis-Auslöser in Reihenfolge). `Created`/`Updated` stehen nicht im Vergleich (neues Feld `extra` am `MirrorEntry`, wie `source`, nicht im Hash): die Datenbank liefert die Zeiten des Registers, beim Schreiben der Datei stehen sie im Kopf.
- **Lesen.** Fehler mit Datei und Zeile: `unknown_field`, `missing_field`, `invalid_value` (auch `Status: due`), `unknown_trigger` (Zeit-Auslöser und alles außer `event`/`topic_due`), `duplicate_uid`, `duplicate_label`, `file_label_mismatch` (Dateiname ≠ Überschrift, `new-…` ohne `# NEW`), `invalid_placeholder` (`new-` und `a-z0-9-`, im Projekt eindeutig; Topic-Platzhalter eindeutig). Gegen die Golden-Files unter `tests/fixtures/mirror-v2/` (gültig und `file_label_mismatch`, `unknown_trigger`).
- **Schreiben.** Eine Note ist eine ganze Datei, die aus dem Eintrag entsteht (Kopf, Auslöser, Links, Langtext), `topics.md` wird aus den vorhandenen Zeilen und den Änderungen neu aufgebaut (Reihenfolge der Datei bleibt, neue Topics ans Ende ihres Parents). Ein Platzhalter-Eintrag ersetzt seine Datei unter dem neuen Label, Dokumente werden umbenannt.
- **Teilnehmer.** `load` (Topics, Notes mit Auslösern und Verknüpfungen der Rollen `reference`/`origin`, Dokumente; auch gelöschte), `resolve_labels` (Labels und frühere Labels, auch mit Projektname), `assign_labels` (Register: `reserve_label`, `note_labels`), `apply` (legt über `register_as` an, setzt Felder, Parent, Topic, Auslöser samt `trigger`-Verknüpfungen, Verknüpfungen, Papierkorb, Dokumente; ein unbekanntes Label ist `unknown_reference` mit Datei und Zeile). Auslöser schreibt der Teilnehmer direkt (ohne das Item zu prüfen, die Datei ist die Wahrheit). Gelöscht wird aus den Dateien nie endgültig, sondern in den Papierkorb.
- **Tests.** Golden-Files (Lesen, Schreiben, Runde), ungültige Beispiele, Platzhalter mit Verweisen über Notes, Topics und Items, Integration mit dem Sync-Dienst und echter Datenbank (hin und zurück, Konflikt, Platzhalter).

### Decided

1. **Kern**: `MirrorConfig.name`, `for_project`, `MirrorEntry.extra`.
2. **Codec** (Syntax, Lesen, Schreiben) mit Golden-Tests.
3. **Teilnehmer** und Einbindung (`mirror=` im Plugin), Integrationstests.
4. **Abschluss**: Techdoku (`interfaces.md` bleibt, `neubau-server.md`), `check-next.sh`, `check.sh`, Status.

### Open

- Frage 32 (Projektname im Codec; Verweise auf andere Projekte) steht in `STORY-060`.

## 2026-10-17 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Umsetzung wie geplant: Kern (`MirrorConfig.name`, `bound_codec`/`for_project`, `MirrorEntry.extra`), Codec `notes/infrastructure/mirror/{syntax,decode,encode,codec}.py`, Teilnehmer `participant.py`, Einbindung als `mirror=` im Plugin. Beschreibung in `neubau-server.md` (Abschnitt `notes` und Sync).
- Der Teilnehmer schreibt Auslöser und ihre `trigger`-Verknüpfungen direkt aus der Datei (keine Prüfung des Items): die Datei ist die Wahrheit, ein bereits eingetretener Auslöser bleibt eingetreten.
- Bekannte Grenze (wie beim Backlog): ändert sich das Label eines Ziels, zieht der Verweis in der Datei erst beim nächsten Schreiben der Note nach; ändern sich zugleich Datei und Datenbank derselben Note, ist es ein Konflikt.

### Decided

- Abschlusskriterien geprüft: (1) Codec liest und schreibt `notes/` nach Format Version 2 gegen die Golden-Files, auch ungültig (`file_label_mismatch`, `unknown_trigger`) (`test_notes_mirror_decode.py`, `test_notes_mirror_encode.py`); (2) neue Notes und Topics bekommen Label und Uid, Platzhalter (auch von Items derselben Runde) werden ersetzt, Dateien und Dokumente umbenannt (`test_note_mirror.py`); (3) Verknüpfungen und Auslöser über Labels in den Dateien und `uid`s in der Datenbank, auch zu anderen Projekten (`test_note_mirror.py`); (4) Tests grün.
- `scripts/check-next.sh` und `scripts/check.sh` grün. Status: `Awaiting confirmation`.

### Open

- Frage 32 steht in `STORY-060`.
- Nicht geprüft: sehr große Notes-Ordner (Leistung), Zeilenenden `\r\n` in Notes-Dateien (der Kern liest und schreibt sie, der Codec arbeitet mit LF; nur an Backlog-Dateien getestet).

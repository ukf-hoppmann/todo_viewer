# STORY-075 — Backlog im Markdown-Spiegel

## 2026-10-16 — Entscheidungen

### Decided

- Prioritäten: nur Urgent, Important, Normal, Prospective; der Sync prüft, dass Markdown nur diese Werte enthält.
- In der Cloud angelegte Items kommen über den Sync in der DB an.

## 2026-10-17 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- **Bestandteile.** Der `MirrorCodec` des Plugins `backlog` (Muster `TODO.md`, `archive.md`, `items/**`) und sein `SyncParticipant`, beide in `viewer/plugins/backlog/infrastructure/mirror/`. Der Codec ist von Hand geschrieben nach dem Muster des alten Parsers und der Editoren (`src_old/backend/todo_viewer/infrastructure/markdown/`): gleiche Syntax, gleiche Umbruchbreite, Änderungen ersetzen nur Felder, die sich ändern, und verschieben nur den betroffenen Eintrag; ein Platzhalter-Eintrag wird an seiner Stelle ersetzt.
- **Einträge.** Ein Item ist ein `MirrorEntry` mit `kind` `epic`/`story`/`task`, den Feldern `title`, `status`, `priority`, `area`, `created`, `goal`, `completion_criteria`, `summary`, `resolution`, `required_for_parent`, `deleted` (Tag) und den Verweisen `parent` und `dependencies` als Labels. Ein Dokument hat `kind` `backlog.document`, `label` = Name, `uid` = `<Item-uid>/<Name>`, `fields` `content` und `kind`, Verweis `item`. Ein Dokument eines neuen Items hat noch keine `uid` und als Platzhalter `<NEW-name>/<Name>`; `assign_labels` benennt es mit dem Item um. `created` gehört zum Hash.
- **Lage.** Aktive Items stehen in `TODO.md`, geschlossene (`Completed`/`Rejected`) und gelöschte in `archive.md`; die Lage ist keine Information, der Codec verschiebt beim Schreiben.
- **Fehler** nach `docs/techdocs/interfaces.md` mit Datei und Zeile: `format_version`, `unknown_field`, `missing_field`, `invalid_value` (auch Label-Präfix ≠ Typ), `duplicate_uid`, `duplicate_label`, `invalid_placeholder`, `file_label_mismatch`, `rule_violation` (Lebenszyklusregeln über die Einträge der Dateien, auch `summary_required_with_notes` über die Dokumente). `unknown_reference` kann nur die Datenbank entscheiden (frühere Labels): der Teilnehmer wirft ihn beim Schreiben mit der Zeile des Eintrags (dazu bekommt `MirrorEntry` das Feld `source`, das nicht zum Vergleich gehört; Frage 28); er bricht den Sync vor jeder Änderung ab. `merge_markers` und `.git`-Sperren erkennt der Datei-Port.
- **Teilnehmer.** `load` liefert alle Items des Projekts (auch gelöschte) und alle Dokumente; `assign_labels` reserviert Labels im Register (`ElementRegistry.reserve_label`); `apply` legt Elemente mit der vergebenen `uid` und dem Label an (`register_as`; der Label-Zähler zieht nach), schreibt Felder, Verweise, Papierkorb-Zustand und Dokumente und prüft die Lebenszyklusregeln über das Projekt. Eine Löschung aus den Dateien legt das Item in den Papierkorb (nicht endgültig).
- **Tests.** Golden-Files aus `tests/fixtures/mirror-v2/` (Lesen: `valid/` und je Fehlercode `invalid/<code>/` mit Datei und Zeile), Schreib-Tests mit minimalen Änderungen, Platzhalter-Auflösung, Teilnehmer gegen echtes SQLite, Sync-Dienst mit echtem Ordner.

### Decided

1. **Core und Register**: `MirrorEntry.source`; `reserve_label` und `register_as` im Register.
2. **Codec lesen**: Syntax, Parser, Prüfungen; Golden-Tests zuerst.
3. **Codec schreiben**: Feld-Edits, Verschieben, Platzhalter, Dokumente; Tests.
4. **Teilnehmer** und Verdrahtung (`mirror` im Plugin); Integrationstests mit dem Sync-Dienst.
5. **Integration**: `check-next.sh`, `check.sh`, Techdoku.

### Open

- Frage 28 in `STORY-060`.

## 2026-10-17 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Umsetzung wie geplant: Codec (`syntax.py`, `decode.py`, `encode.py`, `codec.py`) und Teilnehmer (`participant.py`) in `viewer/plugins/backlog/infrastructure/mirror/`. Beschreibung in `docs/techdocs/neubau-server.md`.
- Abweichungen und Folgen:
  - Die `uid` eines Dokuments ist `<Item-uid>/<notes|spec|spec_<thema>>` statt `<Item-uid>/<Name>` (Spec): der Name enthält das Label, ein Typwechsel gäbe sonst eine neue Identität und einen Scheinkonflikt.
  - Das Beispiel `valid/` hat ein neues Item mit Notizen ohne Kurzfassung. Deshalb prüft der Spiegel `summary_required_with_notes` nicht (die Regel gilt für Änderungen in der Oberfläche; die Datenbank behandelt sie bei zurückkehrenden und neuen Items als vorhandenen Mangel).
  - Frage 28 (Zeile für `unknown_reference` über `MirrorEntry.source` und `source_lines`).
  - Core-Änderungen, die der Spiegel brauchte: Label-Abweichung allein lässt die Datei nachziehen; `assign_labels(…, taken)`; `_write_files` findet Einträge mit selbst gebildeter `uid` über das Label; der Datei-Port räumt leere Unterordner auf; Register: `reserve_label`, `register_as`, `note_labels`, `mark_deleted(…, at)`. Den Test `test_deleted_in_database_can_delete_the_file_entry_or_bring_it_back` habe ich in seinem Aufbau berichtigt (das Label der Datenbank-Seite stimmt jetzt mit der Datei überein; vorher widersprachen sich beide Seiten und die Datei zog nach).
  - Der Datei-Port liest `items/**` unter Python 3.11 nicht (`Path.glob` trifft mit `**` am Ende nur Ordner): das Muster ist `items/**/*.md`.
- Der Spiegel beachtet nur `TODO.md`, `archive.md` und `items/**/*.md`; `notes/` und `alarms.md` bleiben unberührt (`STORY-079`, `STORY-080`).

### Decided

- Abschlusskriterien geprüft: Lesen und Schreiben gegen die Golden-Files (`test_mirror_decode.py`: `valid/` und je Fehlercode mit Datei und Zeile; `test_mirror_encode.py`: nur geänderte Felder, Verschieben, Platzhalter, Dokumente, Vorlage); Platzhalter-Auflösung und Dokumente neuer Items, Typwechsel, altes Label, Papierkorb, Löschung nur mit Bestätigung (`test_item_mirror.py` mit dem echten Sync-Dienst, echter SQLite-Datei und echtem Ordner); Prüfregeln als `rule_violation`.
- `scripts/check-next.sh` und `scripts/check.sh` grün. Status: `Awaiting confirmation`.

### Open

- Frage 28 in `STORY-060` (Annahme gilt).
- Nicht geprüft: große Projekte (Laufzeit des Schreibens: der Codec liest die Blöcke nach jeder Änderung neu); Zeilenenden CRLF (die Dateien-Schicht erhält sie, der Codec arbeitet mit LF); Zusammenspiel mit den Codecs von Notes und Wecker.

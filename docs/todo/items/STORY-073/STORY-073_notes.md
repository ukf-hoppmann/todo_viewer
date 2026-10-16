# STORY-073 — Backlog-Dokumente: Notizen und Specs

## 2026-10-16 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- **Speicher.** Tabelle `backlog_documents(item_uid, name, kind, content, revision, updated_at)` mit Primärschlüssel (`item_uid`, `name`), Fremdschlüssel auf `backlog_items` mit `ON DELETE CASCADE` (endgültiges Löschen des Items nimmt die Dokumente mit); `kind` ist `notes` oder `spec`. Migration v2 des Plugins `backlog`.
- **Namen** folgen dem Label (Vorlage `src_old/backend/todo_viewer/domain/documents.py`): `<LABEL>_notes.md` (das erste Notiz-Dokument des Items), `<LABEL>_spec.md`, `<LABEL>_spec_<thema>.md` (Thema aus Buchstaben, Ziffern, `-`). Ein Typwechsel benennt die Dokumente des Items um (`STORY-008_notes.md` → `TASK-004_notes.md`); ein Name, der das alte Label nicht enthält, bleibt.
- **Version.** Je Dokument eine `revision` (Zähler, 1 beim Anlegen). `put_document` mit `version` ersetzt das Dokument in genau dieser Version (`version_conflict` sonst), ohne `version` legt es ein neues an (`document_exists`, wenn der Name schon vergeben ist).
- **Notiz-Eintrag.** `append_note(item, topic, discussed, decided, open, summary?)` hängt `## <Datum vom Server> — <Thema>` mit den Abschnitten `### Discussed`/`### Decided`/`### Open` (Stichpunkte, nur nicht leere) an `<LABEL>_notes.md` an; der erste Eintrag legt das Dokument mit der Kopfzeile `# <LABEL> — <Titel>` an. Thema und mindestens ein Abschnitt sind Pflicht.
- **Kurzfassung.** Regel `summary_required_with_notes` (Struktur, gilt für das Item allein): ein Item mit Notiz-Dokument braucht eine Kurzfassung. Die erste Notiz verlangt sie deshalb (als Angabe `summary` oder schon vorhanden); sie wird mit dem Dokument in einer Transaktion gesetzt. Die Regel prüft vor jedem Schreiben, ein vorhandener Mangel blockiert nichts anderes.
- **Operationen** `list_documents` (GET `/items/{ref}/documents`), `get_document` (GET `/items/{ref}/documents/{name}`), `put_document` (PUT, Body `content`, `version`, `summary`), `append_note` (POST `/items/{ref}/notes`); alle auch MCP. Ereignis `backlog.document.changed` (öffentlich: `uid`, `name`, `change`: `created`, `updated`).
- Das Item im Detail (`get_item`) nennt die Namen seiner Notizen und Specs (`notes`, `spec`).
- **Client:** Abschnitt „Dokumente“ im Detailpanel mit der Liste, Dokument-Dialog (Vorschau, Bearbeiten mit `MarkdownEditor`, Konflikt, großer Blick), „＋ Notiz-Eintrag“ (Thema, Besprochen/Entschieden/Offen je ein Stichpunkt pro Zeile, Kurzfassung wenn nötig) und „＋ Spec anlegen“ (Name mit dem Muster).

### Decided

1. **Domäne**: Namen, Notiz-Eintrag, Umbenennen, Regel `summary_required_with_notes`; Tests zuerst.
2. **Migration, Repository, Dienst, Operationen** mit Integrationstests (Versionskonflikt, erste Notiz, Typwechsel).
3. **Client**: API, Abschnitt, Dialoge; UI-Tests.
4. **Integration**: `check-next.sh`, `check.sh`, Techdoku.

### Open

- Keine neuen Fragen.

## 2026-10-16 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Umsetzung wie geplant: Server `domain/documents.py`, `application/documents.py`, `infrastructure/database/documents.py` (Migration v2), Client `DocumentsSection.tsx`. Beschreibung in `docs/techdocs/neubau-server.md` und `neubau-client.md`.
- Die Regel `summary_required_with_notes` (aus `STORY-072` ausgespart) ist jetzt Teil der Lebenszyklusregeln; das Item im Detail nennt die Namen seiner Dokumente.
- Mit der DB als Speicher entfallen die Schreibzugriffe auf Dateien und der Konflikt „Datei extern geändert“ des alten Viewers; die Version ist eine Revision je Dokument. Der Spiegel (`STORY-075`) schreibt die Dokumente später in die Ordner der Items.

### Decided

- Abschlusskriterien geprüft: (1) Dokumente `<LABEL>_notes.md`, `<LABEL>_spec.md`, `<LABEL>_spec_<thema>.md` je Item in der DB (`test_item_documents.py`, `test_documents.py`); (2) Notiz-Eintrag mit Thema, Besprochen, Entschieden, Offen und Datum vom Server (Format im Tabellentest und in der Integration); (3) ganzes Dokument bearbeiten mit Vorschau und Konflikterkennung (`DocumentsSection.test.tsx`, Server: `version_conflict`); (4) die erste Notiz verlangt eine Kurzfassung (Server-Regel und Feld im Dialog); (5) Tests grün.
- `scripts/check-next.sh` und `scripts/check.sh` grün. Status: `Awaiting confirmation`.

### Open

- Nicht geprüft: das Schreiben der Dokumente in die Ordner (`STORY-075`); die Übernahme vorhandener Dokumente (`STORY-082`).

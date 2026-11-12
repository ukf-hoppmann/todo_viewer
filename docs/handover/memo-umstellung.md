# Übergabe an den Harness: aus Note wird Memo (STORY-098)

Stand: 2026-11-12, Viewer ab Version 0.10.0. Verbindliche Einzelheiten: `docs/techdocs/interfaces.md`, Abschnitte „MCP-Tools für den Harness (Neubau)“ und „Dateiformat Version 2“.

## 1. Kurz

- Der Eintragstyp mit Wiedervorlage (bisher **Note**, `NOTE-001`) heißt jetzt **Memo** (`MEMO-001`). Der Hinweis zwischen Memo und Item (bisher **Notice**) heißt **Hint** (in der deutschen Oberfläche „Hinweis“).
- **Note** meint danach nur noch die **Notiz zu einem Backlog-Item** (`<ID>_notes.md`). Diese Dateien und alles, was sie betrifft (`backlog_*`-Tools, `notes_state`, Kopf „State“, `check_notes_state.py`, `mark_notes_state.py`, `remind_notes.py`, `notes_head.py`, `notes_hint.py`), bleiben unverändert.
- Die Umbenennung ist ein **harter Schnitt**: Der Viewer kennt `/api/notes/…` und die Tools `notes_…` nicht mehr. Der Harness muss zugleich mit dem Viewer umgestellt werden, sonst scheitern seine Memo-Aufrufe.
- Die Dokumentart `notes` (Datei `<LABEL>_notes.md`) bleibt auch bei Memos gleich: `MEMO-001_notes.md`.

## 2. Zuordnung alt → neu

### Namen und Werte

| Alt | Neu |
|---|---|
| Label `NOTE-001` | `MEMO-001` (Zähler und Verlauf übernommen: `MEMO-015` folgt auf `NOTE-014`) |
| Elementtyp (`kind`) `note` | `memo` (Suche, Papierkorb, Verknüpfungen; `topic` bleibt) |
| Plugin / Tool-Präfix `notes_` | `memos_` |
| Hinweis-Seite (`side`) `note` | `memo` (`item` bleibt) |
| Hinweis-Ursachen `note_dropped`, `note_promoted` | `memo_dropped`, `memo_promoted` (`item_completed`, `item_rejected`, `item_deleted`, `item_retyped` bleiben) |
| Fehlercodes `note_archived`, `note_deleted`, `note_not_archived`, `note_target_invalid`, `notice_decided` | `memo_archived`, `memo_deleted`, `memo_not_archived`, `memo_target_invalid`, `hint_decided` |
| Ereignisse `notes.note.changed`, `notes.topic.changed`, `notes.document.changed`, `notes.settings.changed`, `notes.due` | `memos.memo.changed`, `memos.topic.changed`, `memos.document.changed`, `memos.settings.changed`, `memos.due` |
| Grund „fällig wegen Hinweis“: `notice` | `hint` |

Unverändert: Status der Memos (`waiting`, `due`, `snoozed`, `done`, `dropped`, `promoted`), Auslöser-Arten (`event`, `topic_date`), Entscheidungen (`keep`, `detach`, `drop`, `promote`, `acknowledge`), Topics (`TOPIC-001`), Dokumentart `notes`/`spec`, alle Felder der Memos (`summary`, `body`, `topic`, `review_at`, `trigger_mode`, …).

### HTTP-Routen

Alle Routen unter `/api/notes/…` heißen jetzt `/api/memos/…`. Die Form bleibt, nur das Segment `notes` für den Typ wird `memos`:

| Alt | Neu |
|---|---|
| `/api/notes/notes`, `/api/notes/notes/{ref}` und `…/{ref}/keep`, `/move`, `/finish`, `/snooze`, `/restore`, `/promote`, `/triggers`, `/entries`, `/documents`, `/documents/{name}` | `/api/memos/memos`, `/api/memos/memos/{ref}` und dieselben Unterpfade |
| `/api/notes/index`, `/index/lines`, `/due`, `/settings` | `/api/memos/index`, `/index/lines`, `/due`, `/settings` |
| `/api/notes/topics`, `/topics/{ref}` und `…/archive`, `/content`, `/delete`, `/move`, `/reactivate` | `/api/memos/topics/…` |
| `/api/notes/triggers/{uid}` | `/api/memos/triggers/{uid}` |
| `/api/notes/items/{ref}/demote` | `/api/memos/items/{ref}/demote` |
| `/api/notes/items/{ref}/notices` | `/api/memos/items/{ref}/hints` |
| `/api/notes/notices/{uid}/decide` | `/api/memos/hints/{uid}/decide` |

Die Routen unter `/api/backlog/…` (auch `…/notes/state`, `…/notes/entries`) und `/api/workspace/…` bleiben.

### MCP-Tools

Die Tools heißen `memos_<operation>`; in der Operation wird `note` zu `memo` und `notice` zu `hint`:

`memos_index`, `memos_index_lines`, `memos_due_memos`, `memos_topic_content`, `memos_get_memo`, `memos_create_memo`, `memos_update_memo`, `memos_keep_memo`, `memos_snooze_memo`, `memos_finish_memo`, `memos_move_memo`, `memos_restore_memo`, `memos_promote_memo`, `memos_demote_item`, `memos_add_trigger`, `memos_remove_trigger`, `memos_list_item_hints`, `memos_decide_hint`, `memos_list_memo_documents`, `memos_get_memo_document`, `memos_put_memo_document`, `memos_append_memo_entry`, `memos_create_topic`, `memos_update_topic`, `memos_move_topic`, `memos_archive_topic`, `memos_delete_topic`, `memos_reactivate_topic`, `memos_get_memos_settings`, `memos_update_memos_settings` (nur HTTP).

Befehl für Befehl: Tabelle „`notes_api.py` → MCP“ in `docs/techdocs/interfaces.md`.

### JSON-Felder

| Antwort / Anfrage | Alt | Neu |
|---|---|---|
| `GET /index` | Liste `notes` | `memos` |
| Topics im Index | `open_notes`, `due_notes` | `open_memos`, `due_memos` |
| `GET /index/lines` | `note_count`, Text `notes` | `memo_count`, `memos` |
| `GET /due` | Liste `notes` | `memos` |
| Memo (`show`, Fällig-Liste) | Liste `notices` | `hints` |
| Topic archivieren / löschen (Wahl) | `active_notes` | `active_memos` |

### Spiegel (Markdown-Dateien)

| Alt | Neu |
|---|---|
| Ordner `notes/` im Backlog-Ordner | `memos/` |
| `notes/NOTE-001.md`, `notes/NOTE-001_notes.md`, `…_spec.md`, `…_spec_<thema>.md` | `memos/MEMO-001.md`, `memos/MEMO-001_notes.md`, `…_spec.md`, `…_spec_<thema>.md` |
| `notes/new-<kurzname>.md`, `notes/topics.md` | `memos/new-<kurzname>.md`, `memos/topics.md` |
| Verweise in Memo-Dateien und Weckern `note:NOTE-007`, `NOTE-004` | `memo:MEMO-007`, `MEMO-004` |

Der Dateiinhalt sonst (Kopfzeilen, `Triggers:`, `Links:`, Langtext) und das Format Version 2 bleiben.

## 3. Was im Harness anzufassen ist

Nur Memos betroffen:

| Datei | Änderung |
|---|---|
| `scripts/notes_api.py` (ggf. in `memos_api.py` umbenennen) | Routen, `NOTES_KINDS = ("memo", "topic")`, Labels `MEMO-`, Felder (`memos`, `memo_count`, `hints`, `active_memos`), Befehle `notices` → `hints`, Texte |
| `scripts/notes_files.py`, `scripts/notes_format.py` (nur Backend `files`) | Ordner `memos/`, Dateinamen `MEMO-…`, Verweise `memo:`; Fehlercodes folgen dem Decoder des Viewers (`server/src/viewer/plugins/memos/infrastructure/mirror/`) |
| `scripts/viewer_api.py` | Docstring (`notes_api.py`) |
| `scripts/session_start.py`, `scripts/harness_config.py` | Texte „Notes: via ToDo-Viewer API …“ und `viewer_notes_enabled`/`notes_enabled` (Namen und Meldungen), sofern sie Memos meinen |
| Skills `todo`: `notes.md`, `notes-api.md`, `notes-files.md`, Abschnitt „Notes“ in `SKILL.md`, `sync-flow.md` | Begriffe Memo und Hint; den Satz „Notes sind keine Item-Notizen“ umdrehen: Memo ist der Eintrag, Notiz die Datei am Item |
| Kopie des Harness in diesem Repository (`.claude-harness/runtime/`, `.claude/skills/harness-todo/`) | Nach der Änderung im Harness neu exportieren (`cloud_export.py`) |

Nicht anfassen: `backlog_api.py`, `backlog.py`, `check_notes_state.py`, `mark_notes_state.py`, `remind_notes.py`, `notes_head.py`, `notes_hint.py`, `mark_active_item.py`; sie handeln von den Item-Notizen.

## 4. Reihenfolge der Umstellung

1. Geprüftes Backup der Datenbank.
2. Container neu bauen und starten: Die Migration läuft beim Start (Plugin `notes` → `memos`) und legt vorher ein eigenes Backup an.
3. Sync mit dem Spiegel; die Memos erscheinen als `memos/MEMO-xxx.md`. Danach den alten Ordner `docs/todo/notes/` aus dem Repository entfernen.
4. Harness umstellen (Abschnitt 3) und neu exportieren.

Zwischen 2 und 4 funktionieren die Memo-Befehle des Harness nicht (Backlog-Befehle schon).

## 5. Offen

- Der Name „Hint“ für den Hinweis kann mit den weichen Warnungen des Backlogs (`hints`, `hint:`-Zeilen in den Antworten) verwechselt werden. Der Owner lässt es vorerst so und ändert es, wenn es stört (Vorschlag: „Advisory“).
- Verweise `NOTE-nnn` in Texten alter Backlog-Einträge sind nicht umgeschrieben.

# Übergabe an den Harness: was sich mit dem Neubau ändert

Stand: 2026-10-18. Grundlage: Neubau `EPIC-007` (Server `server/`, Client `client/`), Umstieg `STORY-084`
(noch offen). Verbindliche Details: `docs/techdocs/interfaces.md`, Abschnitte „MCP-Tools für den Harness (Neubau)“ und
„Dateiformat Version 2“. Dieses Dokument ist die Übergabe aus `STORY-084`, Abschlusskriterium 6 (Format und
Tool-Liste).

## 1. Kurz

- **Die HTTP-API v2 (`/api/v2`) und die Helfer `backlog_api.py` / `notes_api.py` entfallen.** An ihre Stelle tritt der
  **MCP-Server `todo-viewer`** des Neubaus.
- **Die Datenbank ist die Wahrheit**, die Markdown-Ordner (`docs/todo/`) sind ein Spiegel, den nur der Sync schreibt.
- **Neues Spiegel-Format Version 2** (`Uid`-Zeilen, Platzhalter `NEW-…`, Wecker in `alarms.md`); Version 1 wird nicht
  mehr gelesen.
- **Zeit-Auslöser an Notes gibt es nicht mehr**, sie werden Wecker (neues Plugin `alarms`).
- Der Umstieg ist ein **harter Schnitt** ohne Parallelbetrieb: danach läuft der Neubau auf Port 5411, der alte Viewer
  ist weg.

## 2. Der MCP-Server

| | |
|---|---|
| Name | `todo-viewer` (Server-Name im MCP-Handshake) |
| Transport | Streamable HTTP |
| Endpunkt heute (Parallelbetrieb) | `http://localhost:5412/mcp` (Container `todo-viewer-next`, `./todo.sh`) |
| Endpunkt nach dem Umstieg | `http://localhost:5411/mcp` |
| Authentifizierung | keine; der Port ist nur an `127.0.0.1` gebunden |
| Erlaubte Hosts (DNS-Rebinding-Schutz) | `127.0.0.1`, `localhost`, `[::1]`, `todo.localhost` (jeder Port) |
| Tool-Namen | `<plugin>_<operation>`, z. B. `backlog_get_item`; in Claude Code `mcp__todo-viewer__backlog_get_item` |
| Tool-Liste mit JSON-Schema | `tools/list`; lesende Tools tragen `readOnlyHint` |
| Ergebnisse | JSON als Text; Fehler als `isError` mit `{code, message, details}` (dieselben Codes wie über HTTP) |

Einbinden in Claude Code (nach dem Umstieg):

```bash
claude mcp add --transport http todo-viewer http://localhost:5411/mcp
```

Dieselben Operationen gibt es auch als HTTP unter `/api/<plugin>/…` (OpenAPI unter `/openapi.json`); beide werden aus
denselben Operationen erzeugt. Plugins und damit Tool-Präfixe: `core`, `workspace`, `backlog`, `notes`, `alarms`.

## 3. Grundregeln für Aufrufe

- **Projekt:** einmal `workspace_list_projects` (Name → `uid`, Spiegel-Ordner). Das ersetzt `sources`.
- **Adressieren:** `ref` ist die `uid` oder ein Label; ein Label braucht dazu `project` (die Projekt-`uid`). Labels anderer
  Projekte löst `workspace_resolve_label` auf. `workspace_delete_element` und andere `workspace_*`-Tools nehmen **nur
  `uid`** – beim Harness ein Schritt mehr (Label erst auflösen).
- **Version:** jede ändernde Operation verlangt die `version` aus der letzten Antwort, sonst `version_conflict` → neu
  lesen, prüfen, erneut versuchen. Auch `backlog_append_note` und jedes Schreiben eines Dokuments erhöhen die Version.
- **Zeiten:** ISO 8601, ohne Zone = UTC; der Server antwortet in UTC.
- **Kompakter Überblick:** `backlog_index_lines` (Tabelle `ID | Type | Status | Area | Title | Parent`) und
  `notes_index_lines`; ohne `projects` gelten alle Projekte (früher `--all-projects`).
- **Formatregeln prüft der Server** (Parent-Lebenszyklus, Pflichtfelder, Kurzfassungsregel …); der Harness muss sie über
  MCP nicht selbst durchsetzen.
- **Nicht über MCP** (Architekturregel, nur HTTP/Oberfläche): endgültiges Löschen (`workspace_purge_elements`),
  Einstellungen ändern (`notes_update_notes_settings`), Projekte anlegen/ändern/entfernen, UI-Zustand, Browser-Log.
  Einstellungen der Notes sind lesbar (`notes_get_notes_settings`).

## 4. Zuordnung alte Befehle → Tools (Auszug)

Vollständige Tabelle: `interfaces.md`, „`backlog_api.py` → MCP“ und „`notes_api.py` → MCP“.

| Alt | Neu |
|---|---|
| `health` | `core_health` |
| `sources` | `workspace_list_projects` |
| `index` / `show` | `backlog_index_lines`, `backlog_list_items` / `backlog_get_item` |
| `create` / `update` / `retype` | `backlog_create_item` / `backlog_update_item` / `backlog_retype_item` |
| `note` | `backlog_append_note` (`topic`, `discussed`, `decided`, `open`, `summary`) |
| `doc` / `put-doc` | `backlog_list_documents`, `backlog_get_document` / `backlog_put_document` |
| `delete` / `trash` / `restore` | `workspace_delete_element` / `workspace_list_trash` / `workspace_restore_elements` |
| Notes `index`, `due`, `show` | `notes_index_lines`, `notes_index`, `notes_due_notes`, `notes_get_note` |
| Notes `create`, `update`, `keep`, `snooze`, `finish` | `notes_create_note`, `notes_update_note`, `notes_keep_note`, `notes_snooze_note`, `notes_finish_note` |
| `trigger-add` mit `time` | **`alarms_create_alarm`** (Zeit-Auslöser gibt es nicht mehr) |
| `trigger-add` (`event`, `topic_due`) / `trigger-remove` | `notes_add_trigger` / `notes_remove_trigger` |
| `links`, `backlinks`, `notes-of-item`, `link-add/-remove` | `workspace_list_links`, `workspace_add_link`, `workspace_remove_link` |
| `decide`, `promote`, `demote` | `notes_decide_notice`, `notes_promote_note`, `notes_demote_item` |
| `move` (Note in anderes Projekt) | `notes_move_note` (Antwort ist die neue Note, die alte geht in den Papierkorb) |
| Topics | `notes_create_topic`, `notes_update_topic`, `notes_move_topic`, `notes_delete_topic`, `notes_archive_topic`, `notes_reactivate_topic`, `notes_topic_content` |

Neu, ohne Vorbild im alten Helfer: `backlog_move_item`, `backlog_list_areas`, `backlog_reopen_ancestors`,
`notes_list_item_notices`, `workspace_search_elements`, `alarms_*` (`list_alarms`, `get_alarm`, `create_alarm`,
`update_alarm`, `snooze_alarm`, `finish_alarm`, `reopen_alarm`), `core_sync_status`, `core_sync_preview`, `core_sync_execute`.

Geprüfter Ablauf eines Agenten: `tests/implementation/system/server/test_harness_flow.py` (echter Server, MCP-Client).

## 5. Fachliche Änderungen, die Skills betreffen

- **Wecker statt Zeit-Auslöser.** Erinnerung zu einem Zeitpunkt = `alarms_create_alarm` (`at`, `targets`: Liste aus
  Items, Notes oder Topics, auch in anderen Projekten; `text` nur ohne Elemente Pflicht). Labels `ALARM-001` … nur als
  Schlüssel, Status `Pending`, `Due`, `Snoozed`, `Done`, `Expired` (keins der Elemente mehr offen). 24 h nach Erledigt
  oder Erlöschen löscht der Viewer den Wecker endgültig. Notes behalten Prüfdatum, Ereignis-Auslöser und Topic-Termin. Beim Import werden alte Zeit-Auslöser zu Weckern.
- **Labels werden nie wiederverwendet**; die DB kennt jedes frühere Label eines Elements (nach einem Typwechsel findet
  `STORY-012` weiter dasselbe Element, das jetzt `TASK-040` heißt).
- **Hinweise gibt es an Notes und an Items** (`acknowledge` am Item); „Projekt nicht erreichbar“ entfällt (eine
  Datenbank für alle Projekte).
- **Papierkorb** für alle Elemente über `workspace_*`; beim Löschen eines Topics Wahl für aktive Notes (`move`/`delete`).
- **Prioritäten** nur noch `Urgent`, `Important`, `Normal`, `Prospective` (der Import bildet `High`/`Medium`/`Low` ab).
- **Altitems** EPIC-005, EPIC-006, STORY-041/048/054/055/056 werden nach dem Umstieg über MCP auf `Rejected` gesetzt
  (zugleich Test der Schnittstelle, `STORY-060` Frage 3).

## 6. Markdown-Spiegel (Format Version 2)

Relevant für den `files`-Modus des Harness und seinen Prüf-Hook; im MCP-Modus fasst die KI die Dateien nicht an.

- Kennung in `TODO.md`, `archive.md`, `alarms.md`: Absatz `Format: … backlog format version 2 …`; fehlt sie →
  `format_version`, der Sync bricht ab.
- Jeder Eintrag trägt `Uid: <uuid>` als erstes Feld; Verweise stehen immer als Label.
- Feste Felder: `Uid`, `Type`, `Parent`, `Required for parent`, `Status`, `Created`, `Area`, `Priority`, `Dependencies`,
  `Goal`, `Completion criteria`, `Summary`, `Resolution`, `Deleted`. **`Notes` und `Spec` entfallen** (Dokumente liegen
  weiter in `items/<LABEL>/`); andere Felder sind `unknown_field`.
- **Neue Einträge ohne API:** Platzhalter `NEW-<kurzname>` statt Label, keine `Uid`; der Sync vergibt beides und
  benennt Ordner um. Eine KI erzeugt nie selbst eine `Uid` oder ein Label.
- Notes: `Uid:` im Kopf, `topics.md` mit `uid=` und `archived=`, **`counters.md` entfällt**, `time`-Auslöser sind
  `unknown_trigger`.
- Neue Datei `alarms.md` (Liste unter `## Alarms`).
- Fehlercodes des Sync: `interfaces.md`, „Fehler im Sync“; Golden-Files in `tests/fixtures/mirror-v2/`.

**Sync:** je Projekt Richtung `both`, `to_database` oder `to_files`. Auto-Sync ist je Projekt einschaltbar (Standard aus,
Takt 30 s, überträgt nur konfliktfreie Änderungen, löscht nie). Manuell: `core_sync_preview` → `core_sync_execute` mit
dem Token aus der Vorschau. Committen der Spiegel bleibt Sache des jeweiligen Repositorys.

## 7. Was im Harness anzupassen ist (Vorschlag für die Planung)

1. **Konfiguration** `[todo]`: `api_url = ".../api/v2"` ersetzen, z. B. durch ein MCP-Backend (`backend = "mcp"`,
   Server-Name `todo-viewer`, URL `http://localhost:5411/mcp`).
2. **SessionStart-Hook:** Health-Check und Hinweistext von `/api/v2` auf `core_health` bzw. `GET /api/core/health`
   umstellen.
3. **Skill `todo`** (Backlog, Notes, Topics): Befehle der Helfer durch Tools ersetzen (Abschnitt 4), Regeln zu
   `uid`/Label, `version` und Neu-Lesen nach Notiz/Dokument aufnehmen; `notes-api.md` ersetzen.
4. **Wecker** in den Skill aufnehmen (Erinnern zu einer Zeit = Wecker), Zeit-Auslöser streichen.
5. **Helfer entfernen:** `backlog_api.py`, `notes_api.py`.
6. **`files`-Modus:** Prüf-Hook und Formatbeschreibung auf Version 2 heben (oder `files` für Projekte mit Viewer
   abschaffen).
7. **Test mit einem echten MCP-Client des Harness** – bisher nur mit dem MCP-Client der Python-Bibliothek geprüft.

## 8. Reihenfolge und Stand

- Erledigt im Neubau: MCP-Host (`STORY-062`), Tools für den Harness mit Gegenüberstellung und Systemtest (`STORY-081`),
  Datenübernahme (`STORY-082`), Betrieb (`STORY-083`).
- Offen: Umstieg `STORY-084` (Backup, Übernahme, Port 5411, erster Sync schreibt Version 2, Version `1.0.0`).
- Bis zum Umstieg bleibt der Harness am alten Viewer (`/api/v2` auf 5411); gegen den Neubau lässt er sich auf 5412
  testen. Nach dem Umstieg funktioniert die alte Anbindung nicht mehr – die Harness-Umstellung sollte also zusammen mit
  dem Umstieg ausgeliefert werden.

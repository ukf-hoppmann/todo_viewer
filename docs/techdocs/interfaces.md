# Schnittstellen

<!-- Nur öffentliche Schnittstellen: API, CLI, Dateiformate, Hooks, Ereignisse. -->

## HTTP-API

- Zweck: Lesen und Bearbeiten von Projekten, Backlog, Memos, Weckern und Mindmap, Sync, UI-Zustand.
- Aufruf / Endpunkt: `/api/<plugin>/…` je Operation eines Plugins (`workspace`, `backlog`, `memos`, `alarms`,
  `mindmap`) und `/api/core/…` für den Kern (Health, Ereignisse, UI-Zustand, Einstellungen, Sync). Der Viewer lauscht
  nur lokal auf Port 5411 (im Container über den Proxy auf 5413). Es gibt keinen Login. Dieselben Operationen stehen
  als MCP-Tools zur Verfügung (nächster Abschnitt).
- Eingabe: `{name}` im Pfad füllt das gleichnamige Feld; bei `GET`/`DELETE` kommen die übrigen Felder aus der Query,
  sonst aus dem JSON-Body. Schreibende Operationen verlangen das Versionstoken (`version`) des Elements, das sie
  ändern.
- Ausgabe: JSON. Das vollständige Schema liefert der laufende Server unter `/openapi.json`; die TypeScript-Typen des
  Clients werden daraus erzeugt (`client/src/shared/api/schema.d.ts`).
- Fehler: `{"code", "message", "details"}` mit stabilem `code` (`not_found` 404, `version_conflict` und
  `mirror_conflict` 409, `invalid_input` und `validation_error` 422, sonst 400/500); die Oberfläche übersetzt den
  `code`.
- `GET /api/core/health` antwortet `{"status": "ok"}`. `GET /api/core/events` ist ein Server-Sent-Events-Strom mit
  Benachrichtigungen; die Oberfläche lädt Daten danach selbst neu und fragt nie im Takt ab.
- Details je Plugin: [Neubau: Server](neubau-server.md); Regeln: [Architektur](../development/architecture.md).

## MCP-Tools für den Harness

Zweck: Der Harness (Skills `todo`, `notes`, `alarms`) arbeitet über den MCP-Server des Viewers statt über Dateien oder
Skripte; die HTTP-Routen unter `/api/<plugin>/…` bieten dasselbe. Der MCP-Server (`/mcp`, Streamable HTTP) hat je
Operation ein Tool `<plugin>_<operation>`; Eingabe und Ausgabe sind JSON, Fehler sind Tool-Ergebnisse mit `isError` und
`{code, message, details}` wie bei HTTP. Die Tool-Liste mit Schema liefert `tools/list`.

Grundregeln:

- **Adressieren:** `ref` ist die `uid` oder ein Label (dann mit `project`, der `uid` des Projekts aus
  `workspace_list_projects`). Der Harness braucht also einmal die Projekt-`uid` (Name → `uid` über `workspace_list_projects`,
  das ersetzt `sources`); ein Label eines anderen Projekts löst `workspace_resolve_label` auf.
- **Version:** jede ändernde Operation verlangt die `version` (Revision) aus der letzten Antwort, sonst
  `version_conflict`; `backlog_get_item` und `memos_get_memo` liefern sie, auch für Archiviertes. Eine Notiz an ein Item
  (`backlog_append_note`) und jedes Schreiben eines Dokuments zählen als Änderung: danach die Version neu lesen.
- **Zeiten:** ISO 8601, ohne Zone gilt UTC; der Server antwortet in UTC.
- **Kompakte Ausgabe:** `backlog_index_lines` → `{text, count}`, `text` mit der Kopfzeile
  `ID | Type | Status | Area | Title | Parent | Notes` (Zustand des Kopfs der Notes oder `-`) und einer Zeile je Item; `memos_index_lines` → `{topics, memos, …}` als Tabellen
  `Label | Name | Due at | Due | Notes` und `Label | Status | Reason | Review at | Topic | Summary`. Beide nehmen dieselben
  Filter wie `backlog_list_items` bzw. `memos_index` (`projects`, `statuses`, `query`, …; ohne `projects` alle Projekte, das
  ist `--all-projects`).
- Es gibt **kein Tool zum endgültigen Löschen** und keines, das Einstellungen ändert (`workspace_purge_elements`,
  `memos_update_memos_settings` und die Projekt-Verwaltung sind HTTP-only); Einstellungen sind nur lesbar
  (`memos_get_memos_settings`).

### `backlog_api.py` → MCP

| Befehl | Tool (Route) | Hinweis |
|---|---|---|
| `health` | `core_health` (GET `/api/core/health`) | |
| `sources` | `workspace_list_projects` | Name, Spiegel-Ordner (`mirror_folder`), `uid` |
| `index` | `backlog_index_lines` (GET `/api/backlog/index`); strukturiert `backlog_list_items` | |
| `show <ID>` | `backlog_get_item` | mit `version`, auch Archiviertes und Gelöschtes |
| `create` | `backlog_create_item` | `project`, `type`, `fields` |
| `update <ID> <version>` | `backlog_update_item` | `fields`, `resolution`; bei `parent_closed` danach `backlog_reopen_ancestors` |
| `note <ID>` | `backlog_append_note` | `topic`, `discussed`, `decided`, `open`, `summary`; optional `state` (neuer Kopf, danach gestempelt) mit `state_version`, wenn es schon einen Kopf gibt. Antwort mit `notes_state` und `hints` |
| `state <ID>` | `backlog_get_notes_state` (GET `/api/backlog/items/{ref}/notes/state`) | Kopf ohne Protokoll: `content`, `stamp`, `state`, `checksum`, `last_entry`, `version` (des Kopfs) |
| `put-state <ID> <version>` | `backlog_put_notes_state` (PUT …`/notes/state`) | `content`, `version`; ersetzt und stempelt |
| `confirm-state <ID> <version>` | `backlog_confirm_notes_state` (POST …`/notes/state/confirm`) | `version`; nur der Stempel zieht nach |
| (Einträge) | `backlog_list_notes_entries` (GET …`/notes/entries`) | optional `last`; `{position, day, topic, text}` |
| `doc <ID> <name>` | `backlog_get_document` (Liste: `backlog_list_documents`) | |
| `put-doc <ID> <name> <version\|new>` | `backlog_put_document` | `version` leer = neu |
| `delete-doc <ID> <name> <version>` | `backlog_delete_document` (DELETE `/api/backlog/items/{ref}/documents/{name}?version=`) | in den Papierkorb; mit der Notiz gehen Kopf und Kurzfassung. Antwort `name`, `trash_uid` |
| `retype <ID> <version> <type>` | `backlog_retype_item` | neues Label in der Antwort |
| `delete <ID> <version> [--cascade]` | `workspace_delete_element` | `uid`, `version`, `cascade` |
| `trash` | `workspace_list_trash` | auch gelöschte Dokumente: `kind` `document`, `uid`, `label` = Item, `title` = Dokumentname, `owner_uid` |
| `restore <ID\|trash uid> <version>` | `workspace_restore_elements` | `uids` (mit Nachkommen, die der Papierkorb mitbringt; ein gelöschtes Dokument über seine `uid`) |

Neu gegenüber dem alten Helfer: `backlog_move_item` (Parent/Position), `backlog_list_areas`.

### `notes_api.py` → MCP (die Befehle des Harness; die Tools heißen `memos_…`)

| Befehl | Tool | Hinweis |
|---|---|---|
| `health`, `sources` | wie oben | |
| `index` (`--status`, `--due`, `--archived`, `--all-projects`) | `memos_index_lines`; strukturiert `memos_index` | `statuses` komma-getrennt (`due` = fällig; `done,dropped,promoted` = Archiv), ohne `projects` alle Projekte |
| `index --topic L` / `notes-of-topic` | `memos_topic_content` | Unter-Topics und Memos |
| `index --linked-item ID` / `notes-of-item` / `backlinks` | `workspace_list_links` | `incoming` der Item-`uid` (Rolle `reference`/`origin`/`trigger`) |
| `due` | `memos_due_memos` | Grund, Topic-Pfad, Auslöser, Hinweise |
| `show <MEMO>` | `memos_get_memo` | Langtext, Auslöser, offene Hinweise, `version` |
| `topics [--deleted]`, `topic <T>` | `memos_index` (`topics`); gelöschte: `workspace_list_trash` | |
| `links <MEMO>` | `workspace_list_links` | `outgoing` |
| `docs`, `doc`, `put-doc`, `note-entry` | `memos_list_memo_documents`, `memos_get_memo_document`, `memos_put_memo_document`, `memos_append_memo_entry` | |
| `hints <MEMO>` | `memos_get_memo` (offene Hinweise des Memos) | |
| `hints <ID> --side item` | `memos_list_item_hints` | |
| `create` | `memos_create_memo` | |
| `update <MEMO> <version>` | `memos_update_memo` | |
| `keep` | `memos_keep_memo` | |
| `snooze` | `memos_snooze_memo` | optional `review_at` und `trigger` |
| `finish <MEMO> <version> <done\|dropped>` | `memos_finish_memo` | |
| `move <MEMO> <version> <project> [--topic L]` | `memos_move_memo` (POST `/api/memos/memos/{ref}/move`) | `target_project`, `topic`; Antwort ist das neue Memo |
| `delete <MEMO>` | `workspace_delete_element` | |
| `restore <MEMO>` | `workspace_restore_elements` (aus dem Papierkorb), `memos_restore_memo` (aus dem Archiv) | |
| `trigger-add` (`event`, `topic_due`) | `memos_add_trigger` | |
| `trigger-add` mit `kind: time` | `alarms_create_alarm` | Zeit-Auslöser gibt es im Neubau nicht; der Wecker ersetzt sie |
| `trigger-remove` | `memos_remove_trigger` | |
| `link-add`, `link-remove` | `workspace_add_link`, `workspace_remove_link` | `from_uid`, `to_uid`, `role`; Labels über `workspace_resolve_label` |
| `decide` | `memos_decide_hint` | `keep`, `detach`, `drop`, `promote`, `acknowledge` |
| `promote`, `demote` | `memos_promote_memo`, `memos_demote_item` | |
| `topic-create`, `topic-update`, `topic-move` | `memos_create_topic`, `memos_update_topic`, `memos_move_topic` | |
| `topic-delete [--cascade]` | `memos_delete_topic` (Wahl `active_memos`: `move`/`delete`); `memos_archive_topic` | |
| `topic-restore` | `workspace_restore_elements` (Papierkorb), `memos_reactivate_topic` (Archiv) | |
| `trash` | `workspace_list_trash` | |
| `settings` | `memos_get_memos_settings` | nur lesbar |

### Wecker und Sync (neu)

`alarms_list_alarms`, `alarms_get_alarm`, `alarms_create_alarm`, `alarms_update_alarm`, `alarms_snooze_alarm`,
`alarms_finish_alarm`, `alarms_reopen_alarm` (Löschen und Zurückholen über `workspace_*`);
Themenbaum: `mindmap_get_tree`, `mindmap_get_node`, `mindmap_create_node`, `mindmap_update_node`, `mindmap_move_node`, `mindmap_list_node_documents`, `mindmap_get_node_document`, `mindmap_put_node_document`, `mindmap_append_node_entry`, `mindmap_assign_item`, `mindmap_unassign_item`, `mindmap_link_memo`, `mindmap_unlink_memo`, `mindmap_get_node_content`, `mindmap_get_item_node`, `mindmap_list_memo_nodes` (Löschen und Zurückholen eines Knotens samt Ast über `workspace_*`); `core_sync_status`, `core_sync_preview`,
`core_sync_execute` für den Abgleich mit dem Markdown-Spiegel; Suche über alle Elemente: `workspace_search_elements`;
Verknüpfungen: `workspace_add_link`, `workspace_remove_link`, `workspace_list_links`.

### Ablauf eines Agenten (geprüft im Systemtest)

1. `core_health`, `workspace_list_projects` (Projekt-`uid`).
2. `backlog_index_lines` für den Überblick; `backlog_get_item` für ein Item samt `version`.
3. `backlog_create_item`; `backlog_update_item` mit `version` (bei `version_conflict` neu lesen und prüfen);
   `backlog_append_note` für den Notiz-Eintrag.
4. `memos_create_memo`, `memos_index_lines`, `workspace_add_link` (Memo → Item).
5. `alarms_create_alarm` (`at`, `targets` als Liste, `text` nur ohne Elemente Pflicht), später `alarms_finish_alarm`.
   Ein Wecker erlischt von selbst, wenn keins seiner Elemente mehr offen ist, und wird 24 h nach Erledigt oder
   Erlöschen endgültig gelöscht.
6. `workspace_delete_element` / `workspace_list_trash` / `workspace_restore_elements`.

Der Systemtest `tests/implementation/system/server/test_harness_flow.py` führt diesen Ablauf gegen den ganzen Viewer
(echter uvicorn-Server, alle Plugins) über einen MCP-Client aus.

## Dateiformat des Markdown-Spiegels (Version 2)

Grundsatz: so nah wie
möglich an Version 1 und am früheren Notes-Format, damit der Harness wenig
ändern muss. Neu sind die `Uid`, die Platzhalter für neue Backlog-Einträge
und die Wecker; `counters.md` und Zeit-Auslöser an Memos entfallen. Die Memos
(früher Notes) liegen im Ordner `memos/` und heißen `MEMO-xxx`.

### Ordner eines Projekts

| Pfad | Inhalt |
|---|---|
| `TODO.md` | aktive Items (nicht abgeschlossen, nicht im Papierkorb) |
| `archive.md` | Items mit `Completed`/`Rejected` und Items im Papierkorb |
| `items/<LABEL>/` | `<LABEL>_notes.md` (Aufbau unten), `<LABEL>_spec.md`, `<LABEL>_spec_<thema>.md` (Text unverändert) |
| `memos/` | Memos (`MEMO-001.md`), ihre Dokumente (`MEMO-001_notes.md`, `MEMO-001_spec.md`, …) und `topics.md`, ohne `counters.md` |
| `alarms.md` | alle Wecker |

Andere Dateien werden nicht gelesen. Feldnamen und Werte sind englisch,
Inhalte in der Sprache des Projekts. Zeitpunkte sind UTC mit `Z`, Tage
`YYYY-MM-DD`. Zeilenenden bleiben, wie sie in der Datei sind.

### Notes eines Items

Die Datenbank speichert die Notes eines Items in Teilen (`backlog_notes`:
Vorspann, Kopf, Stempel; `backlog_notes_entries`: Protokolleinträge). API
und Spiegel zeigen sie als eine Datei
([STORY-093](../todo/items/STORY-093/STORY-093_spec.md)):

```markdown
# <LABEL> — <Titel>
<Vorspann, falls vorhanden>
## State

<Kopf>

State confirmed after entry <YYYY-MM-DD> — <Thema> (<Prüfsumme>)

## <YYYY-MM-DD> — <Thema>
…
```

- **Titelzeile:** wird immer aus dem aktuellen Label und Titel des Items
  erzeugt und folgt Typ- und Titelwechsel. Der Sync vergleicht sie nicht: Eine
  abweichende Titelzeile in einer Datei ist keine Änderung und wird beim
  nächsten Schreiben der Datei erneuert.
- **Protokolleintrag:** ab einer Zeile `## YYYY-MM-DD — <Thema>` (Gedankenstrich
  U+2014) bis vor die nächste; der Text bleibt unverändert.
- **Kopf:** der Abschnitt `## State` vor dem ersten Eintrag. Die letzte
  Zeile darin ist der **Stempel**, wenn sie dem Muster oben folgt (Prüfsumme:
  12 Hex-Zeichen).
- **Vorspann:** Text zwischen Titelzeile und Kopf bzw. erstem Eintrag (z. B.
  ein altes `## Summary`), unverändert.
- Notes ohne Kopf kommen bis auf die Titelzeile byteweise so heraus, wie sie
  hineingingen. Notes mit Kopf werden in das Layout oben gebracht.
- `PUT …/documents/<LABEL>_notes.md` über die API: Vorspann und Protokoll kommen
  aus dem Text; der Kopf nur, wenn der Text `## State` enthält, sonst bleibt
  er. Eine Stempelzeile im Text wird ignoriert, den Stempel setzt nur der
  Server.
- Spiegel: Die Datei ist dort der ganze Stand. Der Stempel wird aus ihr
  übernommen, und ohne `## State` ist der Kopf leer.
- **Prüfsumme:** SHA-256 über die kanonische Form des Protokolls (alle
  Einträge ab der ersten Eintragszeile, LF, Leerzeichen und Tabs am
  Zeilenende entfernt, genau ein Zeilenumbruch am Ende), davon die ersten 12
  Hex-Zeichen. Gemeinsamer Vertrag mit `backlog.py` des Harness (`format.md`);
  Testvektoren in `tests/fixtures/notes-state/checksum.json`.
- **Zustand des Kopfs** (`notes_state` in `backlog_get_item`, `backlog_list_items`,
  Spalte `Notes` in `backlog_index_lines`): `missing` ohne Kopf, `stale` ohne
  Stempel oder mit abweichender Prüfsumme, sonst `current`; `null` bzw. `-`
  ohne Notes.
- **Kopf über die API:** `put_notes_state` und `confirm_notes_state` stempeln
  gegen den letzten Eintrag und brauchen die Version des Kopfs
  (`state_revision`); Anhängen ändert nur die Version der Datei. Ohne
  Protokolleintrag gibt es keinen Stempel (`notes_without_entries`); neue
  Notes mit Kopf entstehen mit `append_note` und `state`. Fehler:
  `notes_not_found` (Item ohne Notes), `notes_state_missing` (bestätigen ohne
  Kopf), `notes_without_entries`; HTTP 400.
- **Hinweise** (`hints: [{code, message}]` in schreibenden Antworten auf Notes,
  nie eine Ablehnung): `notes_state_stale` (Kopf danach `stale` oder
  `missing`), `notes_state_malformed` (der Kopf wird gespeichert, aber seine
  Marker sind nicht genau `- Goal/Status:`, `- Next step:`, `- Open:`,
  `- Decided:`, `- References:` in dieser Reihenfolge; der Text nennt die
  erwartete Form, damit der Aufrufer den Kopf korrigieren kann),
  `notes_state_long` (mehr als 15 Punkte unter `- Decided:`),
  `notes_history_rewritten` (`put_document` hat einen bisherigen Eintrag
  geändert oder entfernt).
  Die Texte der Hinweise und Fehler zu den Notes sind Englisch (sie liest
  meist eine KI), die Codes stabil; die Oberfläche übersetzt nach Code.
  Beim Vergleich der Einträge zählen Zeilenenden (CRLF) und Leerzeilen am
  Ende eines Eintrags nicht.
- **Marker im Kopf:** Der Viewer wertet nur `- Decided:` aus; die übrigen
  (`- Goal/Status:`, `- Next step:`, `- Open:`, `- References:`) gehören dem
  Harness. Die frühere deutsche Überschrift `## Stand` wird nicht mehr erkannt.

### Verweise

Verweise (`Parent`, `Dependencies`, `Topic`, `Links`, `Target`) stehen in
den Dateien immer als **Label**, nie als `Uid`. Die `Uid` steht nur am
Eintrag selbst, dort ordnet der Sync ihn zu.

- In der DB hängen alle Verweise an der `uid`. Der Codec schreibt immer das
  aktuelle Label des Ziels; nach einem Typwechsel ziehen alle Verweise in
  den Dateien beim nächsten Schreiben nach.
- Labels werden nie wiederverwendet, und die DB merkt sich jedes Label, das
  ein Element je hatte. Ein Verweis auf ein altes Label (z. B. `STORY-012`
  nach dem Typwechsel zu `TASK-040`) findet deshalb weiter dasselbe Element;
  der Codec schreibt danach das aktuelle Label zurück.
- Ein Label, das es im Projekt nie gab, ist `unknown_reference`.

### Kennung

`TODO.md`, `archive.md` und `alarms.md` enthalten einen Absatz, der mit
`Format:` beginnt und `backlog format version 2` enthält, z. B.

```
Format: Claude_Harness backlog format version 2. The rules are defined in
`docs/techdocs/interfaces.md` of the ToDo Viewer.
```

Fehlt die Kennung oder nennt sie eine andere Version, bricht der Sync mit
`format_version` ab. Version 1 wird nicht gelesen; die Datenübernahme
(`STORY-082`) und der erste Sync nach dem Umstieg schreiben Version 2.

### Backlog-Einträge

Aufbau wie Version 1, eine Liste unter `## Work items`:

```markdown
- `STORY-012` **Kurzer Titel**
  - Uid: 3f0c2a9e-6b1d-4c57-9a8e-2d4b7c1e5f60.
  - Type: Story.
  - Parent: `EPIC-003`.
  - Required for parent: Yes.
  - Status: Open.
  - Created: 2026-10-16.
  - Area: Backend-API.
  - Priority: Normal.
  - Dependencies: `TASK-004`, `STORY-010`.
  - Goal: Ergebnis. Folgezeilen sind
    vier Leerzeichen eingerückt.
  - Completion criteria: Wie das Ergebnis geprüft wird.
  - Summary: Kurzfassung für den Projektinhaber.
```

- **Felder und Reihenfolge** (fest; der Codec schreibt sie in dieser
  Reihenfolge, liest sie in jeder): `Uid`, `Type`, `Parent`,
  `Required for parent`, `Status`, `Created`, `Area`, `Priority`,
  `Dependencies`, `Goal`, `Completion criteria`, `Summary`, `Resolution`,
  `Deleted`. Andere Felder sind ein Fehler (`unknown_field`); `Notes` und
  `Spec` aus Version 1 entfallen, die Dokumente findet der Codec über
  `items/<LABEL>/`.
- **Pflicht:** `Uid` (außer bei neuen Einträgen), `Type`, `Status`, `Area`,
  `Priority`, `Dependencies`, `Goal`, `Completion criteria`; bei Story und
  Task `Parent`, bei vorhandenem Parent `Required for parent`; bei
  `Completed`/`Rejected` `Resolution`. `Created` darf bei neuen Einträgen
  fehlen (der Import setzt den Tag).
- **Werte:** `Type` `Epic`, `Story`, `Task`. `Status` `Open`,
  `In progress`, `Awaiting confirmation`, `Completed`, `Rejected`.
  `Priority` `Urgent`, `Important`, `Normal`, `Prospective`.
  `Required for parent` `Yes`, `No`. Verweise in Backticks, mehrere mit
  Komma, keiner als `None`.
- **Lage:** Welche Datei ein Eintrag hat und an welcher Stelle er steht, ist
  keine Information. Steht ein abgeschlossener Eintrag in `TODO.md`, liest
  der Codec ihn trotzdem und verschiebt ihn beim nächsten Schreiben nach
  `archive.md` (und umgekehrt). Neue Einträge hängt der Codec ans Ende.
- **Regeln** des Backlog-Formats (Parent-Lebenszyklus, keine Zyklen) gelten
  wie in der DB; ein Verstoß bricht den Sync ab (`rule_violation`, mit den
  blockierenden Einträgen).

### Neue Backlog-Einträge aus den Dateien

Eine LLM ohne API legt einen Eintrag **ohne `Uid`** an und gibt ihm einen
Platzhalter statt eines Labels:

```markdown
- `NEW-login-dialog` **Login-Dialog vereinfachen**
  - Type: Task.
  - Parent: `STORY-012`.
  - …
```

- Platzhalter: `NEW-` und ein Kurzname aus `a-z`, `0-9`, `-`, im Projekt
  eindeutig. Sonst `invalid_placeholder`.
- `Parent`, `Dependencies` und Verweise anderer Einträge dürfen
  Platzhalter nennen. Dokumente liegen in `items/NEW-<kurzname>/`
  (`NEW-<kurzname>_notes.md` …).
- Beim Sync vergibt die DB `Uid` und das nächste freie Label des Typs,
  ersetzt den Platzhalter in allen Verweisen und im Fließtext aller Einträge
  (Felder, Notizen, Specs; nur als ganze ID, `NEW-route-2` bleibt bei
  `NEW-route`), benennt Ordner und Dokumente um und schreibt den Eintrag mit
  beidem zurück; Dateien, in denen nur der Text geändert wurde, werden
  ebenfalls neu geschrieben. Bei einem Sync, der nur in die
  DB schreiben darf, werden neue Einträge nicht übernommen (wie heute bei
  Notes).
- Eine LLM erzeugt nie selbst eine `Uid` und nie ein Label.

### Memos und Topics

Wie im Abschnitt „Dateiformat: Notes-Ordner“ oben (dort heißen sie noch Notes: Ordner
`notes/`, Label `NOTE-001`), mit diesen Änderungen:

- Ordner `memos/`, Dateien `MEMO-001.md` und `MEMO-001_notes.md`, `MEMO-001_spec.md`,
  `MEMO-001_spec_<thema>.md`, Verweise `memo:MEMO-007`.
- Im Kopf jedes Memos steht nach der Überschrift `Uid: <uuid>`; ein neues
  Memo (`new-<kurzname>.md`, erste Zeile `# NEW`) hat keines.
- `topics.md`: jede Zeile trägt `uid=<uuid>` nach dem Namen und
  `archived=<Zeitpunkt>`, wenn das Topic archiviert ist:
  `- TOPIC-001 | <Name> | uid=<uuid> | due=… | created=… | archived=… | deleted=…`.
  Ein neues Topic bleibt `- NEW | <Name> | …` ohne `uid`.
- `counters.md` entfällt; eine vorhandene Datei wird ignoriert und beim
  nächsten Schreiben gelöscht.
- Auslöser `time` entfallen (sie werden Wecker); eine `time`-Zeile ist ein
  Fehler (`unknown_trigger`). Es bleiben `event` und `topic_due`.

### Wecker

`alarms.md` mit einer Liste unter `## Alarms`:

```markdown
# Alarms

Format: Claude_Harness backlog format version 2.

## Alarms

- `ALARM-001` **Release vorbereiten**
  - Uid: 9b2e4f7a-1c3d-4e5f-8a6b-7c8d9e0f1a2b.
  - At: 2026-10-20T07:00:00Z.
  - Target: `STORY-012`, `MEMO-004`.
  - Status: Pending.
  - Created: 2026-10-16.

- `ALARM-002`
  - Uid: 1f2e3d4c-5b6a-4978-8a6b-7c8d9e0f1a2b.
  - At: 2026-10-19T07:00:00Z.
  - Target: `MEMO-010`.
  - Status: Done.
  - Done at: 2026-10-18T09:00:00Z.
```

- Felder in dieser Reihenfolge: `Uid`, `At`, `Repeat`, `Series from`, `Target`,
  `Status`, `Snoozed until`, `Done at`, `Created`, `Deleted`. Der fett gesetzte
  Titel ist der Text des Weckers; ein Wecker, der nur an Elemente erinnert,
  hat keinen.
- `Repeat` und `Series from`: Ein Serienwecker hat `Repeat: Daily.`, `Weekly.`,
  `Monthly.` oder `Yearly.` und `Series from` (Startpunkt der Serie, UTC wie
  `At`); beide Felder stehen zusammen oder fehlen ganz. Fehlen sie, wiederholt
  sich der Wecker nicht; eine Datei ohne diese Felder bleibt gültig. Ein
  unbekannter Wert ist `invalid_value`, `Repeat` ohne `Series from`
  `missing_field`. Die Termine der Serie rechnet der Viewer in der Zeitzone
  des Rechners, auf dem er läuft (`TZ`); `At` ist der nächste Termin. Ein
  erledigter Serienwecker wird nie `Done`, er rückt in `At` auf den nächsten
  Termin vor.
- `Target`: komma-getrennte Verweise, je ein Label dieses Projekts oder
  `<projekt>:<LABEL>` für ein anderes Projekt, oder `None`. Die Art eines
  Elements ergibt sich aus dem Präfix (`EPIC`, `STORY`, `TASK`, `NOTE`,
  `TOPIC`). Ohne Text braucht ein Wecker mindestens ein Element.
- `Status`: `Pending`, `Due`, `Snoozed` (dann `Snoozed until`), `Done`
  (von Hand erledigt) oder `Expired` (keins seiner Elemente ist mehr offen);
  `Done at` gehört nur zu `Done` und `Expired`. 24 h danach löscht der
  Viewer den Wecker; der Sync entfernt ihn dann ohne Konflikt aus der Datei.
- Neue Wecker wie neue Backlog-Einträge: Platzhalter `NEW-<kurzname>`,
  ohne `Uid`.

### Fehler im Sync

Ein Formatfehler bricht den Sync vor jeder Änderung ab; die Meldung nennt
Datei und Zeile.

| Code | Bedeutung |
|---|---|
| `format_version` | Kennung fehlt oder ist nicht Version 2 |
| `unknown_field` | Feld, das das Format nicht kennt |
| `missing_field` | Pflichtfeld fehlt |
| `invalid_value` | unbekannter Typ, Status, Priorität oder Wecker-Status; ungültiger Tag, Zeitpunkt oder `Uid` |
| `duplicate_uid` | dieselbe `Uid` zweimal |
| `duplicate_label` | dasselbe Label oder derselbe Platzhalter zweimal |
| `unknown_reference` | `Parent`, `Dependencies`, `Topic` oder `Target` nennt ein Label, das es im selben Projekt nie gab (auch nicht als früheres Label); Verweise in andere Projekte bleiben ungeprüft erhalten |
| `invalid_placeholder` | Platzhalter mit ungültigem Namen |
| `file_label_mismatch` | Datei- oder Ordnername passt nicht zum Label |
| `unknown_trigger` | Auslöser-Art, die es nicht gibt (z. B. `time`) |
| `rule_violation` | Verstoß gegen die Regeln des Backlog-Formats |
| `merge_markers` | Datei mit Git-Merge-Markern |

### Beispiele

`tests/fixtures/mirror-v2/valid/` ist ein vollständiges Projekt mit allen
Feldern, neuen Einträgen mit Platzhaltern, Memos, Topics und Weckern.
`tests/fixtures/mirror-v2/invalid/<code>/` enthält je Fehlercode ein
Beispiel. Die Beispiele sind die Golden-Files der Codecs (`STORY-075`,
`STORY-079`, `STORY-080`).

## CLI: `todo.sh`

- Zweck: Steuerung des Docker-Containers.
- Aufruf / Endpunkt: `./todo.sh <start|stop|restart|down|update|logs|status|open>`.
- Eingabe: Befehlsname.
- Ausgabe: siehe [README](../../README.md#quickstart-docker).
- Fehler: unbekannter Befehl → Hilfetext, Exit-Code 1.

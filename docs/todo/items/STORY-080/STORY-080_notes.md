# STORY-080 — Wecker (Plugin alarms)

## 2026-10-16 — Entscheidungen

### Decided

- Eigene Wecker-Funktion statt der Krücke über Notes.
- Der Wecker meldet sich nur, solange der Viewer läuft.
- Das Backend löst den Wecker aus und meldet ihn per SSE; die UI hält dafür keinen eigenen Zustand.
- Ein Timer auf den nächsten fälligen Zeitpunkt statt Polling; die Fällig-Entscheidung bleibt eine reine Funktion mit der Uhr als Parameter.

## 2026-10-17 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- **Zuschnitt.** Neues Plugin `alarms` (Server und Client), braucht nur `workspace`. Elementtyp `alarm` (Präfix `ALARM`, Titel = Text). Tabelle `alarms_alarms(uid, at, text, target_uid, target_text, status, snoozed_until)`; `target_text` hält ein Ziel in einem anderen Projekt, das es hier nicht gibt (die Spec: „bleiben ungeprüft erhalten“), die Datenbank kann keine Verknüpfung ohne Ziel halten (Frage 33). Keine Wiederholung.
- **Domäne** (rein): `due_now(alarms, now)` (Status `Pending` mit `at` erreicht, `Snoozed` mit `snoozed_until` erreicht; nicht im Papierkorb) und `next_due(alarms, now)` (frühester Zeitpunkt der noch wartenden, auch ein vergangener). Übergänge: `snooze` (Status `Snoozed`, `snoozed_until` in der Zukunft, Standard eine Stunde), `finish` (`Done`), eine Änderung von `at` setzt wieder auf `Pending`.
- **Auslösen.** `AlarmService.fire()` setzt fällige Wecker auf `Due`, veröffentlicht `alarms.due` (public, `uids`) und `alarms.alarm.changed`, und setzt den Termin neu. `reschedule()` bestellt beim `Scheduler` genau einen Termin (`schedule("alarms", next_due, fire)`); er läuft nach jeder Änderung, beim Bau des Plugins (der Scheduler holt Vergangenes beim Start der Schleife sofort nach), nach Papierkorb-Ereignissen (`workspace.element.changed`) und nach einem Sync (`core.sync.state`). Ein Wecker, der `Due` ist, bleibt es über einen Neustart.
- **Operationen** (HTTP + MCP): `create_alarm`, `update_alarm`, `snooze_alarm`, `finish_alarm`, `list_alarms` (`due_only`, `projects`); Löschen und Wiederherstellen über `workspace`.
- **Spiegel** (`alarms.md`): `AlarmsCodec` und `AlarmsParticipant` wie beim Backlog (Kennung `format_version`, Felder `Uid`, `At`, `Target`, `Status`, `Snoozed until`, `Created`, `Deleted`; Platzhalter `NEW-<kurzname>`; `Created` steht nicht im Vergleich). Die Datei entsteht ganz aus den Einträgen, die Einleitung bleibt. Das Ziel ist `` `LABEL` `` im Projekt oder `` `Projekt:LABEL` ``; ein unbekanntes Label im eigenen Projekt ist `unknown_reference`, ein unbekanntes anderes Projekt oder Label bleibt Text.
- **Client.** Der Slot `workspace.detail-sections` kommt doch (Frage 24 bleibt gültig für Plugins ohne Hook): `workspace` exportiert `DetailSections` (Eigenschaften `uid`, `label`) und den Hook `useDetailElement()`; die Detailpanels von `backlog` und `notes` binden `DetailSections` ein, `alarms` hängt „Wecker stellen“ dort ein (Frage 34). Außerdem: Neu-Typ „Wecker“ im Neu-Dialog, Zähler in der Kopfzeile mit Liste (erledigen, zurückstellen), Banner und Browser-Benachrichtigung bei `alarms.due` (Notification API nur mit Erlaubnis; Schalter dafür in den Einstellungen), Hauptroute „Wecker“ mit der Liste aller Wecker.
- **Tests.** Domäne mit fester Uhr; Scheduler-Integration (Termin nach jeder Änderung, `fire` setzt `Due` und meldet das Ereignis, Neustart holt Verpasstes nach); Golden-Files von `alarms.md` (lesen, schreiben, Runde, ungültige Beispiele, Platzhalter, Sync mit echter Datenbank); UI-Tests.

### Decided

1. **Server**: Domäne und Tests → Tabellen, Dienst, Scheduler, Operationen → Codec und Teilnehmer.
2. **Client**: `workspace.DetailSections` → API, Neu-Typ, Zähler, Banner → Hauptroute und Einstellungen.
3. **Abschluss**: Techdoku, `check-next.sh`, `check.sh`, Status.

### Open

- Fragen 33 und 34 stehen in `STORY-060`.

## 2026-10-17 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Wie geplant umgesetzt: Server (Domäne, Dienst mit genau einem Scheduler-Termin, Operationen für HTTP und MCP, Codec und Teilnehmer für `alarms.md`), Client (Slot `workspace.detail-sections`, Neu-Typ, Zähler, Banner, Notification, Einstellungen, Hauptroute `alarms/main`). Techdoku in `neubau-server.md` und `neubau-client.md`.
- Das Zeitfeld des Formulars ist nicht `required`; der Code meldet „Ein Zeitpunkt fehlt.“ selbst.

### Decided

- Abschlusskriterien geprüft: (1) Anlegen über UI, API, MCP (`test_alarm_flow.py`, `AlarmsPage.test.tsx`, `Widgets.test.tsx`); (2) genau ein Termin, Nachholen beim Start (`test_alarm_flow.py`); (3) Banner, Zähler, Notification, Erledigen, Zurückstellen (`announce.test.ts`, `Widgets.test.tsx`, `AlarmsPage.test.tsx`); (4) Codec für `alarms.md` gegen Golden-Files samt Sync (`test_alarms_mirror_codec.py`, `test_alarm_mirror.py`); (5) Tests mit fester Uhr grün.
- `scripts/check-next.sh` und `scripts/check.sh` grün. Status: `Awaiting confirmation`.

### Open

- Nicht geprüft: die Wecker-Oberfläche im echten Browser (nur jsdom), echte Browser-Benachrichtigungen.
- Die Fragen 33 und 34 stehen in `STORY-060`.

## 2026-10-17 — Nachtrag: Prüfung im Browser (Cloud-Sitzung)

### Discussed

- Der gebaute Client (Chromium, Playwright) gegen den Server als Prozess mit synthetischen Daten: Hauptroute `alarms/main` listet einen gemeldeten (`Gemeldet`) und einen wartenden Wecker mit Zeit und Ziel, der Zähler `⏰1` in der Kopfzeile öffnet die Liste mit „Erledigt“ und „Zurückstellen“, das Detail eines Items zeigt „Wecker stellen“ mit dem vorhandenen Wecker; keine Konsolenfehler. Der Wecker feuerte vom Scheduler des Servers von selbst (`Pending` → `Due` nach zwei Sekunden).

### Decided

- Damit ist der Punkt „im echten Browser“ aus dem Eintrag oben erledigt, bis auf echte Browser-Benachrichtigungen (Berechtigung) und das Banner über einen Seitenwechsel hinweg.

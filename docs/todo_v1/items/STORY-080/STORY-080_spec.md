# `STORY-080` — Wecker

Grundlage: `EPIC-007_spec.md`, Abschnitte 5 (Zeitgeber), 9 (`alarms`), 10. Ersetzt `STORY-056`.
Format: `docs/techdocs/interfaces.md`, Abschnitt „Dateiformat Version 2“; Beispiele unter `tests/fixtures/mirror-v2/`.

## Abgrenzung

- Backlog: Arbeit mit Abschlusskriterien.
- Note: Gedanke zum Wiederansehen (Prüfdatum, Ereignisse).
- Wecker: fester Zeitpunkt, optional an ein Element gebunden. Für den
  Harness: „Erinner mich“ → Wecker, „Merk dir“ → Note.

## Datenmodell

`alarms_alarms(uid PK FK workspace_elements, at TIMESTAMP UTC, text,
target_uid NULL FK workspace_elements, status CHECK in
('Pending','Due','Done','Snoozed'), snoozed_until NULL)`.
Keine Wiederholung (`STORY-060` Frage 5).

## Umfang

- Domäne: `next_due(alarms, now)` und `due_now(alarms, now)` als reine
  Funktionen.
- Anwendung: nach jeder Änderung und beim Start
  `Scheduler.schedule("alarms", next_due)`; der Callback setzt fällige auf
  `Due` und veröffentlicht `alarms.due` (public).
- Operationen: `create_alarm`, `update_alarm`, `snooze_alarm`,
  `finish_alarm`, `list_alarms(due_only?)`.
- Frontend: Neu-Typ „Wecker“ im Neu-Dialog und „Wecker stellen“ im
  Detailpanel jedes Elements (Slot `workspace.detail-sections`); Banner bei
  `alarms.due`; Zähler; Browser-Benachrichtigung über die Notification API,
  wenn erlaubt (`STORY-060` Frage 6).
- Codec `alarms.md` und Sync-Teilnehmer.

## Tests

Test zuerst: `next_due`/`due_now` mit fester Uhr; Scheduler-Integration;
Codec-Golden-Files.

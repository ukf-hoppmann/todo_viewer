# `STORY-078` — Notes-Auslöser und Hinweise

Grundlage: `EPIC-007_spec.md`, Abschnitt 9. Inhalt von `STORY-041` (Änderungshinweise) eingeschlossen.

## Datenmodell

- `notes_triggers(uid PK, note_uid, kind CHECK in ('event','topic_date'),
  target_uid NULL, status NULL, fired_at NULL, already_met BOOL)`.
  Zeit-Auslöser gibt es nicht mehr; sie sind Wecker (`STORY-080`, `STORY-060` Frage 7).
- `notes_notices(uid PK, note_uid, source_uid, kind, created_at, decided NULL)`.

## Umfang

- Abonnement `backlog.item.status_changed` → Auslöser prüfen.
- Fällig-Entscheidung als reine Funktion `due_state(note, triggers, topic,
  now)`; ausgewertet beim Lesen.
- Hinweise: bei Änderung eines verknüpften Items/einer Note
  (`backlog.item.changed`, `notes.note.changed`).
- Befördern über den öffentlichen Port von `backlog` (`create_item`);
  Zurückstufen nur bei Status `Open`.
- Operationen wie `notes_api.py` heute (`trigger_add`, `trigger_remove`,
  `due`, `notice_decide`, `promote`, `demote`).
- Frontend: Abschnitte „Auslöser“ und „Hinweise“ im Detail, Fällig-Liste
  hinter dem Zähler, „Zur Note zurückstufen“ im Item-Detail über Slot.

## Tests

Test zuerst: `due_state`-Tabellentests mit fester Uhr; Ereignis-Auslöser
über den EventBus; Befördern/Zurückstufen.

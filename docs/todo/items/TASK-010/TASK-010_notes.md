# TASK-010 — Hinweis-Modell: speichern, fällig machen, entscheiden

## 2026-10-08 — Umsetzung Hinweis-Modell

### Decided

- Neue Routen: GET /api/v2/notices?project&label&side&open (Hinweise einer Note oder eines Items), POST /api/v2/notices/{id}/decision {decision, version?} -> {notice, note}. NoteOut hat open_notices; die Fällig-Liste nennt für Grund notice die Aktionen keep, detach, drop, promote.
- Neue Fehlercodes: notice_not_found (404), notice_already_decided (409), decision_not_available (409, solange promote nicht angeschlossen ist), invalid_value (400, Entscheidung der falschen Seite).
- Neuer Fälligkeitsgrund notice; Reihenfolge der Gründe: trigger, notice, topic_due, review_expired.
- Datenbank: Migration 7 mit Tabelle note_notices; Hinweise nennen Note und Item über Projekt plus Label (kein uid), folgen einem retype (relink_item) und dem Projektwechsel einer Note und gehen mit der Note beim Purge.
- NoteService.decide(notice_id, decision, version?) statt decide(project, label, ...): die Hinweis-ID bestimmt Note und Seite. Wirkung zuerst, dann wird der Hinweis erledigt; scheitert die Wirkung, bleibt er offen. drop läuft über finish und erzeugt damit auch die Hinweise an den Items.

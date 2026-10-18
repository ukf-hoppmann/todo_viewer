# STORY-040 — Spec: Auslöser und Wiedervorlage

## Was und warum
Der Viewer erkennt selbst, wann eine Note Aufmerksamkeit braucht. Das kostet keine Tokens und braucht keine offene Sitzung. Es gibt bewusst keinen Hintergrund-Takt.

## Auswertung
- **Zeit:** Beim Lesen wird `Zeitpunkt <= jetzt` bewertet. Das Ergebnis hängt nur von den gespeicherten Daten ab, nicht vom Zeitpunkt des Lesens; `fired_at` des Auslösers ist der geplante Zeitpunkt.
- **Ereignis:** Der Use Case, der einen Item-Status ändert, sucht Auslöser auf dieses Item mit passendem Zielstatus und setzt `fired_at`. Zulässige Zielstatus: In progress, Awaiting confirmation, Completed, Rejected. Ist das Ziel bei Anlage des Auslösers schon erreicht, feuert er sofort (`already_met`). Ein gefeuerter Auslöser bleibt gefeuert, auch wenn das Item später wieder geöffnet wird.
- **Topic-Termin:** `topic_due` feuert, wenn der Termin des Topics erreicht ist.
- **Prüf-Datum:** Jede Note hat `review_at` (Standard jetzt + `notes.review_days`, 30). Es gilt für alle Notes, auch für solche mit offenem Auslöser. Es wird bei Anlage, Textänderung, Zurückstellen und „behalten" neu gesetzt.
- **Modus:** `any` (Standard): die Note ist fällig, sobald ein Auslöser gefeuert hat. `all`: erst wenn alle gefeuert haben. Unabhängig vom Modus meldet die Auswertung, welche Auslöser gefeuert haben und ob alle gefeuert haben. Der Schalter in der UI kommt später.

## Zustände
`waiting` → `due` (Auslöser oder Prüf-Datum) → `snoozed` | `done` | `dropped` | `promoted`. Zurückstellen löscht die gefeuerten Auslöser, setzt `review_at` neu, nimmt optional ein neues Datum oder ein neues Ereignis an; die Note ist danach wieder wartend und wird wie `waiting` ausgewertet (`snoozed` zeigt nur, dass sie zurückgestellt wurde). `due` bleibt, bis die Note zurückgestellt, erledigt, verworfen oder gelöscht ist; es gibt keine erneute Erinnerung. `done`, `dropped`, `promoted` führen ins Archiv (STORY-043).
Der Fälligkeitsgrund wird angegeben: `trigger`, `review_expired`, `topic_due` (später auch offener Änderungshinweis aus STORY-041).

## Zeit
Gespeichert wird UTC, die Eingabe und Anzeige erfolgen in der Zeitzone des Rechners. `jetzt` kommt über einen Clock-Port, damit Tests es steuern können.

## Betroffene Dateien
`domain/notes.py` (Auswertung als reine Funktionen), `application/services/items.py` (Ereignis-Aufruf), `application/services/notes.py`, `application/ports.py` (Clock), Konfiguration `notes.review_days`.

## Abnahme
- Zeit-, Ereignis- und Termin-Auslöser sowie die Wiedervorlage sind mit festem Clock-Test geprüft, auch der Standardwert 30.
- Mehrere Auslöser: jeder einzeln, beide eingetroffen, Modus `all`.
- Zurückstellen setzt die Note auf wartend und löscht die gefeuerten Auslöser.
- Der Vorgang braucht keine offene Sitzung und keinen Hintergrundprozess.

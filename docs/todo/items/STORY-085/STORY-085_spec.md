# STORY-085 — Serienwecker: Wiederholung am Wecker

## Was und warum

Ein Wecker kann sich wiederholen: täglich, wöchentlich, monatlich oder jährlich. Wiederkehrende Erinnerungen
(„jeden Montag 9 Uhr Backlog sichten“) brauchen dann nicht jedes Mal einen neuen Wecker. Wird ein Serienwecker
lange nicht beachtet, erscheint er einmal, mit der Zahl der verpassten Termine, statt sich zu stapeln.

Entscheidungen: Notizen dieser Story vom 2026-10-19 („Planung Serienwecker“, „Zeitzone: die Zeit kommt vom
Backend“). Sie gehen dem Wortlaut von Abschlusskriterium 2 vor (Vorrücken erst beim Erledigen, nicht beim
Fälligwerden).

## Zeitzone

- Gültig ist die Zeitzone des Rechners, auf dem das Backend läuft (Architektur §4). Der Browser schickt keine
  Zone mit, und ein Wecker speichert keine eigene Zone.
- Der Container `todo-viewer-next` rechnet heute in UTC, weil kein `TZ` gesetzt ist. Künftig:
  - `docker-compose.yml` setzt `TZ` für `todo-viewer-next` aus der Umgebung, Standard `Europe/Berlin`.
  - `todo.sh` gibt `TZ` aus der Zone des Macs weiter, wenn sie nicht gesetzt ist (Name aus dem Ziel von
    `/etc/localtime`, z. B. `Europe/Berlin`).
  - Das Image braucht Zeitzonendaten: das Python-Paket `tzdata` als Abhängigkeit des Servers (`python:3.11-slim`
    hat kein `/usr/share/zoneinfo`).
- Der Server liest die Zone beim Start (`TZ`, IANA-Name) und reicht sie als `ZoneInfo` an das Plugin weiter.
  Fehlt sie oder ist sie unbekannt, gilt UTC, und das Log meldet es einmal als Warnung.
- Die Domain bekommt die Zone als Parameter, so wie sie heute die aktuelle Zeit bekommt (reine Funktionen, §4).
  Tests geben die Zone vor.
- Gespeichert und über API, MCP und Spiegel ausgetauscht wird weiter UTC. Nur die Rechnung der Serientermine läuft
  in Ortszeit: „11 Uhr“ bleibt 11 Uhr über die Sommerzeit-Umstellung.

## Datenmodell

Neue Felder am Wecker (`Alarm` in `plugins/alarms/domain/model.py`):

| Feld | Werte | Bedeutung |
|---|---|---|
| `repeat` | `none` (Standard), `daily`, `weekly`, `monthly`, `yearly` | Wiederholung |
| `series_from` | Zeitpunkt (UTC) oder leer | Startpunkt der Serie; leer genau dann, wenn `repeat = none` |

- Migration v3 von `alarms`: Spalten `repeat` (NOT NULL, Standard `none`, Prüfung gegen eine Tabelle
  `alarms_repeats` wie bei `alarms_statuses`) und `series_from`. Bestehende Wecker bekommen `none`.
- `series_from` wird gesetzt, wenn ein Wecker mit `repeat ≠ none` angelegt wird, wenn `repeat` von `none`
  wechselt oder wenn sich bei einem Serienwecker `at` ändert: dann ist `series_from = at` (eine neue Serie).
  `repeat = none` leert `series_from`.

## Regeln (Domain, reine Funktionen)

- **Termin n** der Serie: `series_from` in Ortszeit plus n Intervalle (Tage, Wochen, Monate, Jahre), immer vom
  Startpunkt aus gerechnet, nie vom vorigen Termin, damit nichts wandert.
  - Monatlich und jährlich wird auf den letzten Tag des Monats gekürzt: Start 31.01. → 28.02. (29.02. im
    Schaltjahr) → 31.03.; Start 29.02. → 28.02. im Nicht-Schaltjahr.
  - Eine Ortszeit, die es am Umstellungstag nicht gibt (Frühjahr, 02:30), rückt um die Länge der Lücke vor
    (03:30). Eine doppelte Ortszeit (Herbst) nimmt die erste (`fold = 0`).
- **Fälligwerden** bleibt wie heute: zur Zeit `at` (zurückgestellt: `snoozed_until`) wird der Wecker `Due`.
- **Erledigen** (`finish_alarm`) eines Serienweckers: Er wird nicht `Done`, sondern wartet auf den ersten Termin der
  Serie nach jetzt (`status = Pending`, `at` = dieser Termin, `snoozed_until` und `done_at` leer). Er wird nicht
  aufgeräumt.
- **Verpasste Termine** werden abgeleitet, nicht gespeichert: `missed` = Zahl der Serientermine nach `at` bis
  jetzt. Ein Wecker, der drei Tage lang `Due` stand (täglich), hat `missed = 3`. Für Wecker ohne Wiederholung ist
  `missed = 0`.
- **Zurückstellen** verschiebt nur die nächste Meldung, nicht die Serie. Erledigen danach rückt vom Termin `at` aus
  vor.
- **Rückgängig** (`reopen_alarm`) gibt es für Serienwecker nicht, weil sie nie `Done` werden; der Server antwortet
  wie heute mit `alarm_not_done`.
- **Elemente:** Erlischt ein Serienwecker, weil keins seiner Elemente mehr offen ist (`Expired`), endet die
  Serie damit. Wird ein Element wieder offen und der Wecker kehrt zurück, läuft die Serie weiter, und `missed`
  zählt die Termine seit `at`.
- Der Termin für den `Scheduler` (`next_wakeup`) ändert sich nicht: nach dem Vorrücken ist `at` einfach der
  nächste Zeitpunkt.

## Schnittstellen

- **API und MCP:** `create_alarm` und `update_alarm` nehmen `repeat` in `fields`. Ein unbekannter Wert ist
  `invalid_input` mit den erlaubten Werten in `details`. Die Antwort (`AlarmOut`) enthält zusätzlich `repeat`,
  `series_from` und `missed`. Die Tool-Beschreibungen nennen die Werte und sagen, dass Serientermine in der
  Zeitzone des Servers gerechnet werden.
- **Markdown-Spiegel** (`alarms.md`, Format Version 2): neue Felder `Repeat` (`Daily.`, `Weekly.`, `Monthly.`,
  `Yearly.`; fehlt bei `none`) und `Series from` (UTC wie `At`), in `FIELD_ORDER` direkt nach `At`. Eine Datei ohne
  diese Felder ist weiter gültig (keine Wiederholung). Unbekannte Werte meldet der Abgleich wie andere
  Formatfehler. `docs/techdocs/interfaces.md` beschreibt die Felder.
- **Client** (`client/src/plugins/alarms/`): Auswahl „Wiederholung“ im Formular (keine, täglich, wöchentlich,
  monatlich, jährlich). Karte und Detail zeigen bei Serienweckern ein Wiederholungssymbol mit Tooltip und, wenn
  `missed > 0`, den Zähler („3 verpasst“), sofern er sich gut in die Karte fügt. „Erledigt“ bei einem Serienwecker
  zeigt danach den nächsten Termin; der Rückgängig-Knopf entfällt dort. Texte in den Locales.
- **Harness:** Die neuen Felder und die Zeitzonenregel gehen als Text an den Projektinhaber für die Harness-Doku
  `alarms.md` (Claude_Harness wird hier nicht geändert).

## Tests

- Domain (Test zuerst, `tests/implementation/unit/server/plugins/alarms/`): Termine täglich, wöchentlich,
  monatlich, jährlich; Monatsende 31.; Schaltjahr 29.02.; Sommerzeit-Beginn und -Ende in `Europe/Berlin` (11 Uhr
  bleibt 11 Uhr, Lücke 02:30, doppelte Stunde); Erledigen rückt auf den ersten Termin nach jetzt; `missed` nach
  langer Pause; Zurückstellen ändert die Serie nicht; `Expired` beendet die Serie.
- Migration v3 auf einer Datenbank mit v2-Weckern.
- Spiegel: Golden-File mit und ohne `Repeat`, Hin- und Rückweg.
- API/MCP: Anlegen mit `repeat`, falscher Wert, Erledigen eines Serienweckers.
- Client: Formularfeld, Anzeige von Symbol und Zähler, Erledigen ohne Rückgängig.
- Betrieb: Container zeigt mit gesetztem `TZ` die Ortszeit (`python -c "import datetime; print(datetime.datetime.now().astimezone())"`).

## Nicht Teil dieser Story

- Wiederholungen nach Wochentagen („Mo–Fr“), Enddatum oder Anzahl der Termine.
- Eine Zone je Wecker oder je Projekt.

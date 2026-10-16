# STORY-060 — Noch zu klären: offene Fragen zum Neubau

## 2026-10-16 — Antworten des Projektinhabers

### Decided

- Frage 9 (2026-10-16): Annahme bestätigt. Bereiche bekommen eine eigene Tabelle backlog_areas je Projekt; neue Bereiche legt man im Feld an; ein unbekannter Bereich aus den Dateien wird beim Sync angelegt.
- Alle übrigen Fragen: Die Annahmen gelten für die Umsetzung; der Projektinhaber entscheidet sie spätestens vor dem Umstieg (STORY-084).

## 2026-10-16 — Fragen aus der Umsetzung (Cloud-Sitzung)

### Open

- Frage 13 (betrifft STORY-061): Die Spec nennt „Plugin-Definition und Operation als Datentypen“ in `core/domain`. `PluginDefinition.build` braucht aber einen Kontext mit Ports (`Clock`, `EventBus`, `Scheduler`), und Ports gehören nach Architektur-Scope `server` §2 nach `application/ports.py`; `domain` darf `application` nicht importieren. Annahme: `Operation`, `HttpBinding`, `Subscription`, `Migration` und die reine Prüfung (gegen ein Protokoll `PluginShape`) liegen in `core/domain`, `PluginDefinition` und `PluginContext` in `core/application`. Ein Operations-Handler hat die Form `handler(services, input)`.

- Frage 14 (betrifft STORY-063): „Vor jeder Migration ein Backup“ (Architektur §2): ein Backup je Start oder je einzelner Migration? Annahme: ein Backup je Start, bevor die erste ausstehende Migration läuft; nicht bei einer Datenbank ohne Tabellen. Die letzten 10 je Grund bleiben.
- Frage 15 (betrifft STORY-063): Muss `PUT /api/core/ui-state/{owner}` ein Versions-Token nehmen (Architektur §3: schreibende Operationen nehmen eins)? Annahme: nein, der UI-Zustand ist ein Dokument je Besitzer ohne Konfliktprüfung (letzter Schreiber gewinnt); das UI hält je Besitzer genau eine Sitzung.

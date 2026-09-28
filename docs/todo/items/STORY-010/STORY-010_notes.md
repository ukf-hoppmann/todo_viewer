# STORY-010 — Notizen

## 2026-09-28 — Zugangsvariante

### Discussed

- Varianten: Container läuft dauerhaft und wird per HTTP angesprochen;
  Server wird bei Bedarf gestartet; zusätzliches CLI ohne Server.

### Decided

- Variante „dauerhaft laufender Container, Zugriff per HTTP“.
- Wie ein Agent reagiert, wenn der Server nicht erreichbar ist, regelt das
  Claude_Harness; im ToDo-Viewer ist dafür nichts zu tun.

## 2026-09-28 — Umsetzung

### Decided

- `GET /api/v2/health` als günstige Erreichbarkeitsprüfung für das Harness.
- Port 5411 wird nur noch an `127.0.0.1` gebunden: Die API kann jetzt Items
  anlegen, ändern und löschen und soll nicht im lokalen Netz offen sein.
- Agenten-Nutzung ist in `docs/techdocs/interfaces.md` („Nutzung durch
  Agenten“) und im README beschrieben.
- Nachweis: Ein vollständiger Durchlauf (Health, source_id, Index, Anlegen,
  Ändern mit Regelprüfungen und Versionskonflikt, Notes, Spec, Löschen) lief
  nur über HTTP gegen einen Testserver auf einer Fixture-Kopie; danach war der
  Ordner byte-gleich mit dem Ausgangszustand.

### Open

- Der laufende Container zeigt die neue API erst nach `./todo.sh update`.
- Beobachtung: Beim Zurückholen aus dem Archiv landet ein Eintrag am
  Dateiende von `TODO.md`, auch wenn nach `## Work items` noch ein anderer
  Abschnitt folgt (festgeschriebenes Altverhalten, betrifft die echten
  Backlogs nicht).

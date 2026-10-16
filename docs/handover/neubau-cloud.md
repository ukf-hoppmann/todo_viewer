# Übergabe: Neubau (EPIC-007) in einer Cloud-Sitzung

Auftrag des Projektinhabers vom 2026-10-16: Den Neubau des ToDo-Viewers
(`EPIC-007`) in dieser Sitzung so weit wie möglich umsetzen, **ohne dass der
Projektinhaber eingreifen kann**. Diese Datei sagt, was gilt und wie gearbeitet
wird. Sie ersetzt keine Regel; wo sie eine Ausnahme nennt, hat der
Projektinhaber sie freigegeben (festgehalten in
`docs/todo/items/EPIC-007/EPIC-007_notes.md`, Eintrag „Freigaben für die
Umsetzung in der Cloud“).

## 1. Zuerst lesen

1. `docs/development/architecture.md` und die Scopes
   `docs/development/architecture/server.md` und `client.md` (verbindlich).
2. `docs/todo/items/EPIC-007/EPIC-007_spec.md` (Architektur, Abschnitt 13:
   Kinder und Reihenfolge) und `EPIC-007_notes.md` (alle Entscheidungen).
3. `docs/todo/items/STORY-060/STORY-060_spec.md` und `_notes.md`: offene
   Fragen mit Annahmen. **Die Annahmen gelten**; Frage 9 ist bestätigt.
4. Vor jedem Item seine Spec `docs/todo/items/<ID>/<ID>_spec.md` und, falls
   vorhanden, seine Notizen.
5. Format des Markdown-Spiegels: `docs/techdocs/interfaces.md`, Abschnitt
   „Dateiformat Version 2“, Beispiele unter `tests/fixtures/mirror-v2/`.

## 2. Umfang

- Die Kinder von `EPIC-007` in der Reihenfolge aus Abschnitt 13 der
  Epic-Spec, jeweils erst, wenn ihre Abhängigkeiten umgesetzt sind.
  `TASK-034` und `TASK-035` sind schon abgeschlossen.
- **Nicht** in dieser Sitzung:
  - `STORY-084` (Umstieg) — nur der Projektinhaber.
  - Jeder Zugriff auf echte Daten: `configs/todo.db`, `configs/viewer.db`
    außerhalb von Tests, Backups, die Ordner anderer Projekte.
    `STORY-082` (Datenübernahme) wird nur mit synthetischen Daten unter
    `tests/fixtures/` gebaut und getestet.
  - Änderungen in `src_old/` (alter Viewer) und `reference/` (Vorlage
    ezf-ui). Beide sind nur Vorlage (Regel 0): lesen, kopieren, anpassen,
    nie importieren, nie löschen.
- Es muss nicht alles fertig werden. Lieber wenige Items vollständig und grün
  als viele halb.

## 3. Freigaben des Projektinhabers

- **Pläne ohne Vorlage.** Vor Beginn eines Items schreibe den
  Umsetzungsplan (Abschnitte nach der Zerlegungsregel: je ein Job, ein Test,
  integrierbar, letzter Abschnitt Integration) als Notiz-Eintrag in dessen
  Notizen und setze ihn dann um. Nicht auf eine Freigabe warten.
- **Keine Releases.** Keine Version in `docs/VERSION`, keine Tags, kein
  Changelog-Eintrag bis zum Umstieg (1.0.0).
- **Abhängigkeiten.** Freigegeben sind die in den Scopes `server` (§7) und
  `client` (§8) genannten Pakete. Jede weitere Abhängigkeit: nicht
  installieren, sondern als Frage mit Annahme in `STORY-060` notieren und
  ohne sie weiterarbeiten.

## 4. Arbeitsweise in der Cloud

- **Branch.** Arbeite auf einem Branch `neubau/epic-007` (vom aktuellen
  `main`). Committe je abgeschlossenem Plan-Abschnitt, Nachricht auf Deutsch
  mit Item-ID, z. B. `STORY-061: Plugin-Host prüft requires`. Pushe den
  Branch nach jedem fertigen Item, damit nichts verloren geht. **Nicht** nach
  `main` mergen, nichts force-pushen, keinen Pull Request mergen.
- **Worktree.** Die Sitzung ist bereits isoliert; keinen weiteren Worktree
  anlegen.
- **Backlog.** Die ToDo-Viewer-API (`localhost:5411`) ist aus der Cloud nicht
  erreichbar. Der Projektinhaber hat entschieden: In dieser Sitzung wird der
  Backlog **direkt in den Dateien unter `docs/todo/` bearbeitet**
  (Claude_Harness-Backlog-Format Version 1, wie die Dateien jetzt aussehen),
  nicht über die API, und es wird nicht nachgefragt. Lokal übernimmt der Sync
  des alten Viewers die Änderungen nach dem Pull in die Datenbank. Erlaubt:
  - `Status:` eines Items auf `In progress` beim Beginn und auf
    `Awaiting confirmation`, wenn alle Abschlusskriterien erfüllt und geprüft
    sind. **Nie** `Completed` oder `Rejected`.
  - Notiz-Einträge in `docs/todo/items/<ID>/<ID>_notes.md` anhängen
    (`## YYYY-MM-DD — Thema`, darunter `### Discussed`, `### Decided`,
    `### Open`). Hat ein Item noch keine Notizen: Datei anlegen, im Eintrag in
    `TODO.md` das Feld `- Notes: items/<ID>/<ID>_notes.md.` nach `Summary`
    ergänzen; ein `Summary` hat jedes Item des Epics schon.
  - Neue Fragen als Notiz-Eintrag in `STORY-060` (Frage, Annahme, betroffenes
    Item).
  - Nichts anderes in `docs/todo/` ändern, keine Items anlegen oder löschen,
    `docs/todo/notes/` nicht anfassen.
- **Tests.** Alle neuen Tests unter `tests/` (Struktur nach
  `tests/implementation/{unit,integration}/{server,client}/…`, siehe Scopes);
  `tests/README.md` (mit dem ersten Test anlegen) nennt die Befehle. Für
  `scripts/check.sh` erst `python3.11 -m venv .venv`,
  `.venv/bin/pip install -r src_old/backend/requirements-dev.txt` und
  `npm --prefix src_old/web ci` ausführen. Vor jedem Commit laufen die betroffenen
  Tests, vor dem Status `Awaiting confirmation` alle Tests des Neubaus und
  `scripts/check.sh` (alter Viewer) grün.
- **Python 3.11.** Ziel ist Python 3.11 (wie im Image). Hat die Cloud eine
  neuere Version, keine Sprachmittel oder Bibliotheksfunktionen nach 3.11
  nutzen; mypy mit `python_version = "3.11"`. Eine frühere Cloud-Sitzung ist
  genau daran gescheitert (`Path.read_text(newline=…)` gibt es erst ab 3.13).
- **Docker.** Steht Docker nicht zur Verfügung, die Dateien von `STORY-083`
  trotzdem schreiben und in den Notizen „Image nicht gebaut, nicht geprüft“
  vermerken.
- **Kein Tagesbericht, keine Technikdoku außerhalb des Neubaus.** Den
  Tagesbericht schreibt die lokale Sitzung nach dem Merge. Technikdoku des
  Neubaus (`docs/techdocs/`) gehört zu dem Item, das sie ändert.

## 5. Wenn etwas nicht geht

- **Frage oder Lücke in der Spec:** Annahme treffen, als Frage mit Annahme in
  `STORY-060` notieren, weiterarbeiten.
- **Konflikt mit einer Regel:** nicht brechen. Notieren (Regel, Grund,
  Vorschlag) in `STORY-060`, das betroffene Teilstück auslassen, mit dem Rest
  oder einem unabhängigen Item weitermachen.
- **Item nicht grün zu bekommen:** Status `In progress` lassen, in seinen
  Notizen festhalten, was fehlt und was geprüft ist, mit Items weitermachen,
  die nicht davon abhängen.
- Nie Prüfungen abschalten, Tests löschen oder abschwächen, um grün zu werden.

## 6. Zum Schluss

Ein Notiz-Eintrag in `EPIC-007` „Stand nach der Cloud-Sitzung“: je Item
Status, was geprüft ist, was nicht, offene Punkte; dazu Branch und letzter
Commit. Dann den Branch pushen.

# STORY-059 — Spec: Auto-Sync für Projekte mit Spiegel (abschaltbar)

## Was und warum
Wer Dateien aus der Cloud (claude.ai, Git) pullt, darf den Sync nicht vergessen können. Der Viewer gleicht deshalb ein Projekt mit Spiegel-Ordner von selbst ab, solange der Besitzer das eingeschaltet hat.

## Festgelegt (Besitzer, 2026-10-14)
- Echter Auto-Sync im Viewer (nicht nur ein externer Auslöser). Pro Projekt ein- und ausschaltbar; Standard: aus.
- Alles Konfliktfreie wird abgeglichen (beidseitig pro Eintrag, STORY-057). Konflikte und Löschungen werden nie automatisch übertragen; sie bleiben offen und sichtbar, bis der Besitzer im Sync-Dialog entscheidet (STORY-058).
- Der Auto-Sync löscht nie etwas.

## Architekturregel (geändert und vom Besitzer freigegeben am 2026-10-14)
Bisher verbot `docs/development/architecture.md` §1 jede automatische Datenübertragung (so festgelegt in EPIC-004). Die Änderung steht jetzt in §1 und §3 dieser Datei und ist verbindlich. Kurzfassung:
- §1: Daten wandern nur durch einen Sync. Ein Sync wird angefordert (Besitzer oder API-Aufruf) oder, nur bei Projekten mit eingeschaltetem Auto-Sync-Schalter, vom Viewer selbst gestartet. Ohne den Schalter (Standard: aus) wandert nichts von selbst.
- §1: Der Sync vergleicht Eintrag für Eintrag mit dem Stand des letzten Syncs. Ein nur auf einer Seite geänderter Eintrag geht auf die andere Seite; Änderung auf beiden Seiten, beidseitig neu mit verschiedenem Inhalt oder Löschung auf einer Seite sind Konflikte und werden nie überschrieben; der Besitzer entscheidet je Konflikt (Datenbank, Datei, aufschieben). Die Richtung darf je Lauf eingeschränkt werden (statt Standardrichtung Primärquelle → Spiegel).
- §1: Ein automatischer Sync überträgt nur Konfliktfreies, löscht nie, liest keine unlesbaren Dateien und keine Dateien mit Merge-Markern und legt vor einem Schreiben in die Datenbank ein Backup an.
- §3: „There MUST be no background timer“ bleibt für Auslöser; der Auto-Sync ist ausgenommen und läuft nur, solange mindestens ein Projekt den Schalter an hat.

## Vorschläge für den Plan (noch nicht festgelegt)
- Auslöser: Hintergrundaufgabe im Server, die nur läuft, solange mindestens ein Projekt den Schalter an hat (ein Viewer ohne Auto-Sync kostet nichts). Prüfintervall als globale Einstellung (Vorschlag: 30 Sekunden). Die Prüfung ist billig: Fingerabdrücke wie `GET /sync-status`. Zusätzlich ein Lauf beim Start. Kein Dateisystem-Watcher (auf Docker unter macOS unzuverlässig).
- Beruhigungszeit: Eine Änderung der Dateiseite wird erst übernommen, wenn ihr Fingerabdruck bei zwei Prüfungen gleich war (ein laufender Pull schreibt Dateien nacheinander).
- Schutz vor Git-Konfliktständen: Dateien mit Merge-Markern (`<<<<<<<`, `=======`, `>>>>>>>` am Zeilenanfang) oder unlesbare Dateien werden nicht eingelesen; der Lauf pausiert mit Meldung (`sync_source_invalid`) und übernimmt nichts.
- Backup (betrifft TASK-031): Ein automatischer Lauf, der in die Datenbank schreibt, sichert höchstens einmal pro Stunde; die Aufbewahrung richtet sich nach dem Alter (z. B. die letzten 10 plus eine je Tag der letzten 14 Tage), damit häufige Läufe ältere Sicherungen nicht verdrängen. Manuelle Syncs und Migrationen sichern immer.
- Sichtbarkeit: Schalter in Einstellungen → Projekte, Anzeige „letzter Lauf“ und „N offene Konflikte“, Badge in der Sidebar, Protokoll im Server-Log.
- Derselbe Use Case und dieselbe Sperre pro Projekt wie der manuelle Sync, kein eigener Pfad. Tests mit fester Uhr, kein echter Timer.
- Sobald STORY-047 fertig ist, deckt der Auto-Sync die Notes mit ab (derselbe Sync).

## Offen
- Standard des Intervalls, Namen der Einstellungen, ob die Beruhigungszeit einstellbar sein soll.

## Betroffene Stellen (Stand der Analyse)
`docs/development/architecture.md` §1 und §3, `application/services/sync.py`, `syncstatus.py`, neuer Dienst für den Auto-Lauf, `bootstrap.py` (Start der Hintergrundaufgabe), `domain/source.py` und `infrastructure/database/` (Schalter je Projekt, Migration), `api/v2/*`, `web/src/components/settings/*`, Sidebar-Badge.

## Abnahme
Siehe Abschlusskriterien. Szenario: Pull ändert eine Story-Datei, der Auto-Sync übernimmt sie in die Datenbank, ohne Klick; gleichzeitig geänderte Story → Konflikt bleibt offen und sichtbar; Schalter aus → nichts passiert.

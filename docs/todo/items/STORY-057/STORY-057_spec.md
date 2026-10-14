# STORY-057 — Spec: Abgleich pro Eintrag mit Konfliktmeldung

## Was und warum
Der Sync (`POST /sources/{id}/sync`) kennt heute nur den Stand ganzer Seiten (`Source.baseline`: zwei Fingerabdrücke) und überschreibt das Ziel in der gewählten Richtung vollständig. Ändern Cloud und lokaler Rechner verschiedene Einträge, bleibt nur `both_changed` und eine Richtung, die die andere Änderung verwirft. Legen beide dieselbe ID neu an, steht in der Vorschau nur `changed`, und beim Ausführen geht ein Eintrag still verloren. Ziel: Backlog zwischen Rechnern und Cloud (claude.ai) über Git abgleichen, ohne dass etwas stillschweigend überschrieben wird.

## Festgelegt (Besitzer, 2026-10-14)
- Jeder Konflikt wird gemeldet. Entscheidung je Konflikt: Datenbank übernehmen, Datei übernehmen oder aufschieben.
- Aufschieben hat keinen eigenen Zustand: Ein nicht entschiedener Konflikt bleibt auf beiden Seiten unberührt, behält seinen alten Stand und wird beim nächsten Abgleich wieder gemeldet. Der Besitzer kann ihn zwischendurch von Hand ändern (z. B. Teile herüberkopieren); sind danach beide Seiten gleich, ist er kein Konflikt mehr.
- **Beidseitiger Abgleich pro Eintrag (Besitzer, 2026-10-14, Variante A):** Ein nur in der Datenbank geänderter Eintrag geht in die Datei, ein nur in der Datei geänderter in die Datenbank, ein auf einer Seite neuer Eintrag auf die andere Seite. `direction` bleibt nur als Einschränkung („nur diese Richtung ausführen“) erhalten. Das ändert Architektur §1 (Standardrichtung); der Wortlaut steht zur Freigabe in der Spec der Auto-Sync-Story.
- **Löschungen sind Konflikte (Besitzer, 2026-10-14):** Ein Eintrag mit gespeichertem Stand, der auf einer Seite fehlt, wird weder ignoriert noch wiederbelebt, sondern wie ein Konflikt entschieden: `database` = der Zustand der Datenbank gilt, `markdown` = der Zustand der Datei gilt (löschen bzw. wiederherstellen), oder aufschieben. Unbeaufsichtigt bleibt er aufgeschoben. `delete_missing` entfällt (Vorschlag, im Plan zu bestätigen).
- Vorläufig: kein automatisches Zusammenführen innerhalb eines Eintrags; die Dateiseite führt Git zusammen. Vorläufig wird je Eintrag nur die Version (Hash) gespeichert, kein Inhalt (siehe Offen: Merge).
- Vor jeder Schema-Migration und vor jedem Sync, der in die Datenbank schreibt, legt der Viewer automatisch ein Backup an (TASK-031).
- Ein manueller Sync bietet weiter eine Vorschau und löscht nichts ohne ausdrückliche Entscheidung. Ein optionaler Auto-Sync (eigene Story, Schalter pro Projekt, Standard aus) startet den Sync für Projekte mit eingeschaltetem Schalter von selbst; er überträgt nur Konfliktfreies.
- Reihenfolge: TASK-031 (Backup) → TASK-032 (Stand je Eintrag) → TASK-033 (Entscheidungen). Danach STORY-058 (Dialog) und STORY-047 (Notes im selben Sync).

## Offen (vor dem Plan mit dem Besitzer klären)
- **Merge:** Der Besitzer sagte „Konflikte sollten gemerged sein“. Zu klären: (a) Konflikte liegen zur Entscheidung bereit (Datenbank, Datei, aufschieben; Diff-Ansicht in STORY-058) oder (b) zusätzlich werden Konflikte automatisch zusammengeführt, wo es eindeutig ist (verschiedene Felder desselben Items, verschiedene Textstellen desselben Dokuments, wie Git; nur echte Überschneidungen bleiben Konflikte). (b) braucht den Inhalt des letzten gemeinsamen Stands (Snapshot statt Hash), eine Prüfung der Lebenszyklus-Regeln nach dem Zusammenführen und ist deutlich größer. Empfehlung: Snapshots von Anfang an speichern (TASK-032), den automatischen Merge als eigene Story danach.

## Betroffene Stellen (Stand der Analyse)
`domain/sync.py` (`plan_sync`, `classify`, `merged_items`), `domain/source.py` (`SyncBaseline`), `application/services/sync.py`, `syncstatus.py`, `application/ports.py`, `infrastructure/database/schema.py` und `migrations.py`, `api/v2/routers.py` und `schemas.py` (Sync-Vorschau, Sync-Status), `bootstrap.py`, Tests unter `backend/tests/{unit,integration,api_v2,contract}`.

## Nicht Teil dieser Story
Notes, Topics und Links (STORY-047; sie nutzen danach denselben Mechanismus), die Konflikt-Ansicht in der UI (STORY-058), ein Drei-Wege-Merge innerhalb von Einträgen.

## Abnahme
Siehe Abschlusskriterien. Zwei Szenarien als Test: (1) Datei ändert STORY-A, Datenbank ändert STORY-B → beide Änderungen bleiben erhalten; (2) beide legen eine neue Story mit derselben ID an → Konflikt, nichts überschrieben.

# STORY-057 — Spec: Abgleich pro Eintrag mit Konfliktmeldung

## Was und warum
Der Sync (`POST /sources/{id}/sync`) kennt heute nur den Stand ganzer Seiten (`Source.baseline`: zwei Fingerabdrücke) und überschreibt das Ziel in der gewählten Richtung vollständig. Ändern Cloud und lokaler Rechner verschiedene Einträge, bleibt nur `both_changed` und eine Richtung, die die andere Änderung verwirft. Legen beide dieselbe ID neu an, steht in der Vorschau nur `changed`, und beim Ausführen geht ein Eintrag still verloren. Ziel: Backlog zwischen Rechnern und Cloud (claude.ai) über Git abgleichen, ohne dass etwas stillschweigend überschrieben wird.

## Festgelegt (Besitzer, 2026-10-14)
- Jeder Konflikt wird gemeldet. Entscheidung je Konflikt: Datenbank übernehmen, Datei übernehmen oder aufschieben.
- Aufschieben hat keinen eigenen Zustand: Ein nicht entschiedener Konflikt bleibt auf beiden Seiten unberührt, behält seinen alten Stand und wird beim nächsten Abgleich wieder gemeldet. Der Besitzer kann ihn zwischendurch von Hand ändern (z. B. Teile herüberkopieren); sind danach beide Seiten gleich, ist er kein Konflikt mehr.
- Kein automatisches Zusammenführen innerhalb eines Eintrags (kein Drei-Wege-Merge von Feldern oder Texten); die Dateiseite führt Git zusammen. Gespeichert wird je Eintrag nur die Version (Hash), kein Inhalt.
- Vor jeder Schema-Migration und vor jedem Sync, der in die Datenbank schreibt, legt der Viewer automatisch ein Backup an (TASK-031).
- Wie bisher: nie automatisch, Vorschau vor dem Ausführen, nichts löschen ohne Bestätigung (Architektur §1).
- Reihenfolge: TASK-031 (Backup) → TASK-032 (Stand je Eintrag) → TASK-033 (Entscheidungen). Danach STORY-058 (Dialog) und STORY-047 (Notes im selben Sync).

## Offen (vor dem Plan mit dem Besitzer klären)
- **Richtung:** Heute wählt der Aufrufer `to_md` oder `from_md`. Vorschlag: Der Abgleich ist beidseitig pro Eintrag (nur Datenbank geändert → Datei; nur Datei geändert → Datenbank; beide → Konflikt; nur auf einer Seite neu → auf die andere kopieren). `direction` bleibt als Einschränkung („nur diese Richtung ausführen“). Alternative: Richtung wie bisher, aber ein Eintrag, der nur auf der Zielseite geändert wurde, zählt als Konflikt.
- **Gelöschte Einträge:** Ein Eintrag mit gespeichertem Stand, der auf einer Seite fehlt. Vorschlag: weiter als „fehlt“ melden und nur mit Bestätigung löschen, nicht als Konflikt.

## Betroffene Stellen (Stand der Analyse)
`domain/sync.py` (`plan_sync`, `classify`, `merged_items`), `domain/source.py` (`SyncBaseline`), `application/services/sync.py`, `syncstatus.py`, `application/ports.py`, `infrastructure/database/schema.py` und `migrations.py`, `api/v2/routers.py` und `schemas.py` (Sync-Vorschau, Sync-Status), `bootstrap.py`, Tests unter `backend/tests/{unit,integration,api_v2,contract}`.

## Nicht Teil dieser Story
Notes, Topics und Links (STORY-047; sie nutzen danach denselben Mechanismus), die Konflikt-Ansicht in der UI (STORY-058), ein Drei-Wege-Merge innerhalb von Einträgen.

## Abnahme
Siehe Abschlusskriterien. Zwei Szenarien als Test: (1) Datei ändert STORY-A, Datenbank ändert STORY-B → beide Änderungen bleiben erhalten; (2) beide legen eine neue Story mit derselben ID an → Konflikt, nichts überschrieben.

# STORY-025 — Doku und Release für das wählbare Speicher-Backend

## 2026-09-30 — Doku, Probe-Migration und Release-Stand

### Discussed

- Die Spec erwartete ein einzelnes Release 0.3.0. Tatsächlich wurden die Schritte des Epics einzeln veröffentlicht (v0.3.0 SQLite-Adapter, v0.4.0 Projekte in der Datenbank, v0.5.0 Sync, v0.5.1 Backend-Wechsel, v0.6.0 UI). Diese Story ändert nur Dokumentation und braucht kein weiteres Release.

### Decided

- Techdocs ergänzt: operations (Speicherort wechseln, Verhalten der Datenbank-Kopie, Sprache beim Export, Fehlerbilder sync_stale, sync_source_invalid, sync_required, db_unavailable, project_not_empty, Log-Felder beim Sync) und configuration (storage_url-Wechsel verschiebt keine Daten, sync_path liegt in der Datenbank). README, architecture und interfaces waren mit den Stories 022 bis 024 schon aktuell.
- Probe-Migration am 2026-09-30 mit einer Kopie von docs/todo in einer eigenen Scratch-Konfiguration (die echten configs/ blieben unberührt): 33 Items, 36 Dokumente, kein Papierkorb. Markdown → Datenbank per from_md und Umstellen: gleiche Item-Versionen und source_id. Datenbank → neuer Ordner per to_md, dort wieder als Markdown-Projekt gelesen: gleiche Item-Versionen, alle Dokumente inhaltsgleich, zweiter Export ohne Unterschiede, Export → Import → Export byteidentisch.
- Der Export in einen neuen Ordner ist gegenüber der Handschrift normalisiert: Kopfzeilen von TODO.md/archive.md aus der Vorlage (bei language=en englisch statt der deutschen Vorlage dieses Projekts), Zeilenumbruch bei 76 Zeichen und Notes/Spec am Ende des Eintrags. TODO.md unterscheidet sich nur in den Kopfzeilen; die Items-Ordner sind identisch.

### Open

- Welches Backend dieses Projekt dauerhaft nutzen soll, entscheidet der Projekteigner. Bei einem Export in einen neuen Ordner sollte language passend gewählt werden (die UI nimmt ihre Sprache).

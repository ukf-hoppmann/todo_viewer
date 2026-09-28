# STORY-011 — Notizen

## 2026-09-28 — Entscheidungen

### Discussed

- Statt echtem Löschen ein Markieren als gelöscht, auch mit Blick auf eine
  spätere Datenbank (dort üblich als `deleted_at`).
- Varianten: Formatänderung im Harness (a), nur im Viewer (b), `Rejected`
  als weiches Löschen (c).

### Decided

- Variante a) im Viewer umgesetzt, ohne den Harness zu ändern: Feld
  `Deleted: <Datum>.`, gelöschte Einträge liegen in `archive.md`. Die
  Anpassung des Harness folgt in einer eigenen Session.
- Papierkorb mit eigener Route (`/trash`): auflisten, wiederherstellen,
  endgültig löschen.
- Kinder erzeugen beim Löschen eine Warnung (409 `has_children`); mit
  Bestätigung (`cascade=true`) wird kaskadiert. Wiederherstellen und
  endgültiges Löschen kaskadieren immer.
- Dependencies von Items außerhalb des Papierkorbs blockieren das Löschen.
- Das bisherige echte Löschen (`STORY-008`) ist jetzt das endgültige Löschen
  aus dem Papierkorb.
- Beim Wiederherstellen blockieren eigene Altlasten des Items (z. B.
  fehlendes `Required for parent`) nicht; Regeln zwischen Items gelten
  weiter.
- Ohne `archive.md` bleibt ein gelöschter Eintrag markiert an seinem Platz.
- Format-Schlüssel wie `No entries.` bleiben englisch; lokalisiert wird nur
  in der UI (Vorgabe des Projektverantwortlichen).

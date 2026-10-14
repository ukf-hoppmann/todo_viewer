# TASK-011 — Hinweise an Notes bei Änderung eines verlinkten Items

## 2026-10-08 — Umsetzung Hinweise an Notes

### Decided

- ItemStatusListener kennt jetzt item_deleted und item_retyped; TrashService (je gelöschtem Item, auch bei Kaskade, nicht beim Wiederherstellen) und RetypeService (nach relink_item und Umbenennen, vor dem Umschreiben der Texte) rufen ihn nach dem erfolgreichen Schreiben.
- Hinweise entstehen nur für Links mit Rolle reference auf offene Notes im Gebrauch; trigger- und origin-Links nie. Ein offener Hinweis gleicher Ursache und Gegenseite wird nicht verdoppelt.
- Fehler beim Anlegen werden mit structlog protokolliert (notice_failed, notice_links_failed) und nie an den Aufrufer gegeben; eine fehlgeschlagene Note stoppt die anderen nicht.

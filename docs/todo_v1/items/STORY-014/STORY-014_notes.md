# STORY-014 — Löschen und Papierkorb-Ansicht

## 2026-09-28 — Umsetzung

### Decided

- Löschen im Detail-Panel versucht es zuerst ohne Kaskade; meldet der Server has_children, nennt der Dialog die Kinder und bietet „Samt Kindern in den Papierkorb“ an.
- Die Papierkorb-Ansicht zeigt gelöschte Items aller nutzbaren Quellen je Projekt, neueste zuerst; endgültiges Löschen verlangt eine eigene Bestätigung.
- Regelverstöße beim Löschen (z. B. letztes Pflichtkind eines laufenden Epics) werden im Dialog angezeigt.

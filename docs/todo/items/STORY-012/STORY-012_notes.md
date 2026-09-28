# STORY-012 — Felder im Bearbeiten-Modus ändern

## 2026-09-28 — Umsetzung

### Decided

- Auch Status, Priorität und Pflicht für Parent sind nur noch im Bearbeiten-Modus änderbar; die bisherigen Sofort-Speicher-Auswahlfelder sind entfernt (Begründung: keine versehentlichen Änderungen).
- Bei einem Versionskonflikt übernimmt „Aktuellen Stand laden“ fremde Änderungen an nicht bearbeiteten Feldern und behält die eigenen Eingaben (rebaseDraft), damit Speichern fremde Änderungen nicht zurückdreht.
- Parent-Auswahl nur aus derselben Quelle, passender Typ, ohne das Item selbst und seine Nachfahren.

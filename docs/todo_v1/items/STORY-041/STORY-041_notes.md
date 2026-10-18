# STORY-041 — Änderungshinweise zwischen Notes und Items

## 2026-10-08 — Vorbereitung der Umsetzung

### Discussed

- Wer über Hinweise entscheidet
- Doppelte Meldung bei Auslöser-Links

### Decided

- Hinweise bleiben bis zur Entscheidung; Optionen behalten, abkoppeln, verwerfen, befördern.
- Wer entscheiden darf, klärt der Besitzer im Harness.

### Open

- Bei Links mit Rolle trigger wird die Note durch den Auslöser fällig; ein zusätzlicher Hinweis beim Abschluss wäre doppelt (Vorschlag: nur bei Rolle reference).

## 2026-10-08 — Offene Frage geklärt, Umsetzung abgeschlossen

### Decided

- Hinweis an der Note bei Abschluss, Verwerfen, Löschen oder Typwechsel nur bei Link-Rolle reference; bei trigger entscheidet der Auslöser, bei origin gibt es keinen Hinweis.
- Hinweise laufen in beide Richtungen (TASK-010, TASK-011, TASK-012). Nicht Teil: Ursache project_unreachable wird erst von TASK-017 erzeugt, die Entscheidung promote von STORY-042, die Anzeige von STORY-045.

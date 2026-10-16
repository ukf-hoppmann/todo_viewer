# STORY-080 — Wecker (Plugin alarms)

## 2026-10-16 — Entscheidungen

### Decided

- Eigene Wecker-Funktion statt der Krücke über Notes.
- Der Wecker meldet sich nur, solange der Viewer läuft.
- Das Backend löst den Wecker aus und meldet ihn per SSE; die UI hält dafür keinen eigenen Zustand.
- Ein Timer auf den nächsten fälligen Zeitpunkt statt Polling; die Fällig-Entscheidung bleibt eine reine Funktion mit der Uhr als Parameter.

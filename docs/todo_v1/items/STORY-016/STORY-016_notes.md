# STORY-016 — Wichtige Schritte und Fehler systematisch protokollieren

## 2026-09-28 — Umfang und Format des Loggings

### Discussed

- Bestand: kein Logging im Backend; Fehler sieht nur der Aufrufer. Still behandelte Fehler in repository.py (unlesbare Quelle), ui_state.py (defekte ui_state.json) und im Ordner-Browser (OSError).
- Format für sparsame KI-Auswertung: key=value ist kompakter als JSON Lines und direkt grep-bar.

### Decided

- Umfang von 'abgelehnte/fehlgeschlagene Requests' auf alle wichtigen Schritte erweitert (Start, Schreibaktionen, 4xx/5xx, geschluckte Fehler); GET nur auf DEBUG.
- Format: einzeilig key=value mit Request-ID; Stacktrace eingerückt unter der Fehlerzeile (grep -A).
- Rotation nach Größe: 5 MB, 5 Dateien.
- Ablage: ./logs/todo-viewer.log im Projekt, Volume ./logs:/app/logs, logs/ in .gitignore; LOG_FILE und LOG_LEVEL per Umgebungsvariable.

## 2026-09-28 — Bibliothek und Umsetzung

### Discussed

- Standard-logging mit eigenem Formatter vs. structlog: structlog bietet key=value-Ausgabe, Kontextvariablen (Request-ID) und Exception-Formatierung fertig und hält die Log-Aufrufe knapp.
- Polling der UI: Lesezugriffe und PUT /ui-state würden das Log auf INFO fluten.

### Decided

- structlog 26.1.0, angebunden über das Standard-logging (RotatingFileHandler, uvicorn im selben Format).
- Domain und Application loggen nicht; protokolliert wird in der API (eine Zeile pro Request, Fehlercode/details, Stacktrace bei 5xx) und in der Infrastruktur (Dateischreibvorgänge, bisher still behandelte Fehler).
- GET und PUT /ui-state nur auf DEBUG.
- ./todo.sh logs folgt der Logdatei statt docker compose logs.

### Open

- Weitere Stellen können nachgetragen werden, z. B. Quellen-Probleme (fehlender Ordner/Mount): bisher nur in der UI sichtbar und bei jedem Polling wiederholt.

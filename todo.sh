#!/bin/bash
# Steuerskript für den ToDo Viewer (Neubau, EPIC-007) als Docker-Container.
# Nutzung: ./todo.sh <befehl>
# Der alte Viewer (Port 5411) wird mit ./todo_old.sh gesteuert.
set -euo pipefail
cd "$(dirname "$0")"

URL="http://localhost:5412"
SERVICE="todo-viewer-next"
LOG_FILE="logs/viewer.log"
# Zum Prüfen des Skripts austauschbar (tests/implementation/system/ops).
DOCKER="${DOCKER:-docker}"

usage() {
  cat <<EOF
Nutzung: ./todo.sh <befehl>

Befehle:
  start     Image bauen (falls nötig) und im Hintergrund starten, Browser öffnen ($URL)
  stop      Container anhalten
  restart   Container neu starten
  down      Container entfernen (configs/ und logs/ auf dem Host bleiben erhalten)
  update    Neu bauen (--no-cache) und Container ersetzen, z.B. nach Code-Änderungen
  logs      Live-Log aus $LOG_FILE anzeigen (Strg+C zum Beenden)
  status    Zustand des Containers und Antwort von /api/core/health
  open      Nur den Browser öffnen (Container muss bereits laufen)

Der alte Viewer läuft getrennt davon: ./todo_old.sh
EOF
}

cmd_start() {
  $DOCKER compose up -d --build "$SERVICE"
  echo "Läuft unter $URL"
  open "$URL" 2>/dev/null || true
}

cmd_update() {
  $DOCKER compose build --no-cache "$SERVICE"
  $DOCKER compose up -d "$SERVICE"
  echo "Aktualisiert und neu gestartet unter $URL"
}

cmd_down() {
  $DOCKER compose rm -sf "$SERVICE"
  echo "Container entfernt. configs/ (viewer.db, Backups) und logs/ bleiben unangetastet."
}

cmd_logs() {
  if [ ! -f "$LOG_FILE" ]; then
    echo "$LOG_FILE fehlt noch; Container-Ausgabe:"
    $DOCKER compose logs "$SERVICE"
    return
  fi
  tail -n 50 -F "$LOG_FILE"
}

cmd_status() {
  $DOCKER compose ps -a "$SERVICE"
  if curl -fsS --max-time 3 "$URL/api/core/health" 2>/dev/null; then
    echo
  else
    echo "Der Viewer antwortet nicht unter $URL" >&2
  fi
}

cmd_open() {
  open "$URL" 2>/dev/null || echo "$URL"
}

case "${1:-}" in
  start)   cmd_start ;;
  stop)    $DOCKER compose stop "$SERVICE" ;;
  restart) $DOCKER compose restart "$SERVICE" ;;
  down)    cmd_down ;;
  update)  cmd_update ;;
  logs)    cmd_logs ;;
  status)  cmd_status ;;
  open)    cmd_open ;;
  *)       usage; exit 1 ;;
esac

#!/bin/bash
# Steuerskript für den ToDo Viewer (Neubau, EPIC-007) als Docker-Container.
# Nutzung: ./todo.sh <befehl>
# Der alte Viewer (Port 5412) wird mit ./todo_old.sh gesteuert.
set -euo pipefail
cd "$(dirname "$0")"

URL="http://todo.localhost:5413"
DIRECT_URL="http://localhost:5411"
SERVICE="todo-viewer-next"
# nginx vor dem Viewer, damit er ohne Port unter $URL erreichbar ist
PROXY="todo-proxy"
LOG_FILE="logs/viewer.log"
# Zum Prüfen des Skripts austauschbar (tests/implementation/system/ops).
DOCKER="${DOCKER:-docker}"

# Zeitzone des Rechners für den Container (Serientermine der Wecker): Name aus dem Ziel von /etc/localtime.
if [ -z "${TZ:-}" ] && [ -L /etc/localtime ]; then
  TZ="$(readlink /etc/localtime | sed 's|.*/zoneinfo/||')"
  [ -n "$TZ" ] && export TZ
fi

usage() {
  cat <<EOF
Nutzung: ./todo.sh <befehl>

Befehle:
  start     Image bauen (falls nötig), Viewer und Proxy im Hintergrund starten, Browser öffnen ($URL)
  stop      Container (Viewer und Proxy) anhalten
  restart   Container neu starten
  down      Container entfernen (configs/ und logs/ auf dem Host bleiben erhalten)
  update    Neu bauen (--no-cache) und Container ersetzen, z.B. nach Code-Änderungen
  logs      Live-Log aus $LOG_FILE anzeigen (Strg+C zum Beenden)
  status    Zustand der Container und Antwort von /api/core/health (direkt und über den Proxy)
  open      Nur den Browser öffnen (Container muss bereits laufen)

Der alte Viewer läuft getrennt davon: ./todo_old.sh
EOF
}

cmd_start() {
  $DOCKER compose up -d --build "$SERVICE" "$PROXY"
  echo "Läuft unter $URL (direkt: $DIRECT_URL)"
  open "$URL" 2>/dev/null || true
}

cmd_update() {
  $DOCKER compose build --no-cache "$SERVICE"
  $DOCKER compose up -d "$SERVICE" "$PROXY"
  echo "Aktualisiert und neu gestartet unter $URL"
}

cmd_down() {
  $DOCKER compose rm -sf "$SERVICE" "$PROXY"
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
  $DOCKER compose ps -a "$SERVICE" "$PROXY"
  if curl -fsS --max-time 3 "$DIRECT_URL/api/core/health" 2>/dev/null; then
    echo
  else
    echo "Der Viewer antwortet nicht unter $DIRECT_URL" >&2
  fi
  if ! curl -fsS --max-time 3 -o /dev/null "$URL/api/core/health" 2>/dev/null; then
    echo "Der Proxy antwortet nicht unter $URL" >&2
  fi
}

cmd_open() {
  open "$URL" 2>/dev/null || echo "$URL"
}

case "${1:-}" in
  start)   cmd_start ;;
  stop)    $DOCKER compose stop "$SERVICE" "$PROXY" ;;
  restart) $DOCKER compose restart "$SERVICE" "$PROXY" ;;
  down)    cmd_down ;;
  update)  cmd_update ;;
  logs)    cmd_logs ;;
  status)  cmd_status ;;
  open)    cmd_open ;;
  *)       usage; exit 1 ;;
esac

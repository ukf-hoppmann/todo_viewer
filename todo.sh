#!/bin/bash
# Steuerskript für den ToDo Viewer Docker-Container.
# Nutzung: ./todo.sh <befehl>
set -euo pipefail
cd "$(dirname "$0")"

URL="http://todo.localhost:5411"
SERVICE="todo-viewer"
LOG_FILE="logs/todo-viewer.log"

usage() {
  cat <<EOF
Nutzung: ./todo.sh <befehl>

Befehle:
  start     Container bauen (falls nötig) und im Hintergrund starten, Browser öffnen
  stop      Container anhalten (Zustand/Netzwerk bleiben erhalten)
  restart   Container neu starten
  down      Container + Netzwerk entfernen (configs/ auf dem Host bleiben erhalten)
  update    Neu bauen (--no-cache) und Container ersetzen, z.B. nach Code-Änderungen
  logs      Live-Log aus $LOG_FILE anzeigen (Strg+C zum Beenden)
  status    Laufender Zustand des Containers
  open      Nur den Browser öffnen (Container muss bereits laufen)
EOF
}

cmd_start() {
  docker compose up -d --build
  echo "Läuft unter $URL"
  open "$URL" 2>/dev/null || true
}

cmd_stop() {
  docker compose stop
}

cmd_restart() {
  docker compose restart
}

cmd_down() {
  docker compose down
  echo "Container entfernt. configs/ (config.json, ui_state.json) bleibt unangetastet."
}

cmd_update() {
  docker compose build --no-cache
  docker compose up -d
  echo "Aktualisiert und neu gestartet unter $URL"
}

cmd_logs() {
  # Der Server schreibt in die Logdatei; die Konsole des Containers zeigt nur
  # Meldungen, bevor das Logging konfiguriert ist (docker compose logs).
  if [ ! -f "$LOG_FILE" ]; then
    echo "$LOG_FILE fehlt noch; Container-Ausgabe:"
    docker compose logs "$SERVICE"
    return
  fi
  tail -n 50 -F "$LOG_FILE"
}

cmd_status() {
  docker compose ps -a
}

cmd_open() {
  open "$URL" 2>/dev/null || echo "$URL"
}

case "${1:-}" in
  start)   cmd_start ;;
  stop)    cmd_stop ;;
  restart) cmd_restart ;;
  down)    cmd_down ;;
  update)  cmd_update ;;
  logs)    cmd_logs ;;
  status)  cmd_status ;;
  open)    cmd_open ;;
  *)       usage; exit 1 ;;
esac

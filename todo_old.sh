#!/bin/bash
# Steuerskript für den ToDo Viewer Docker-Container.
# Nutzung: ./todo.sh <befehl>
set -euo pipefail
cd "$(dirname "$0")"

URL="http://todo.localhost:5412"
SERVICE="todo-viewer"
LOG_FILE="logs/todo-viewer.log"
# Der Neubau (EPIC-007) läuft als eigener Dienst daneben: ./todo.sh next <befehl>
NEXT_URL="http://localhost:5411"
NEXT_SERVICE="todo-viewer-next"
NEXT_LOG_FILE="logs/viewer.log"
# Zum Prüfen des Skripts austauschbar (tests/implementation/system/scripts).
DOCKER="${DOCKER:-docker}"

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

Der alte Viewer ($SERVICE) und der Neubau ($NEXT_SERVICE) sind getrennte Dienste;
die Befehle oben betreffen nur den alten Viewer (außer down: beide).

Neubau:  ./todo.sh next <befehl>
  next start    Image bauen (falls nötig) und den Neubau im Hintergrund starten ($NEXT_URL)
  next stop     Neubau anhalten
  next restart  Neubau neu starten
  next update   Neubau neu bauen (--no-cache) und den Container ersetzen
  next logs     Live-Log aus $NEXT_LOG_FILE anzeigen (Strg+C zum Beenden)
  next status   Zustand des Containers und Antwort von /api/core/health
EOF
}

cmd_start() {
  $DOCKER compose up -d --build "$SERVICE"
  echo "Läuft unter $URL"
  open "$URL" 2>/dev/null || true
}

cmd_stop() {
  $DOCKER compose stop "$SERVICE"
}

cmd_restart() {
  $DOCKER compose restart "$SERVICE"
}

cmd_down() {
  $DOCKER compose down
  echo "Container (auch der Neubau) entfernt. configs/ (config.json, ui_state.json) bleibt unangetastet."
}

cmd_update() {
  $DOCKER compose build --no-cache "$SERVICE"
  $DOCKER compose up -d "$SERVICE"
  echo "Aktualisiert und neu gestartet unter $URL"
}

cmd_logs() {
  # Der Server schreibt in die Logdatei; die Konsole des Containers zeigt nur
  # Meldungen, bevor das Logging konfiguriert ist (docker compose logs).
  if [ ! -f "$LOG_FILE" ]; then
    echo "$LOG_FILE fehlt noch; Container-Ausgabe:"
    $DOCKER compose logs "$SERVICE"
    return
  fi
  tail -n 50 -F "$LOG_FILE"
}

cmd_status() {
  $DOCKER compose ps -a "$SERVICE"
}

cmd_open() {
  open "$URL" 2>/dev/null || echo "$URL"
}

cmd_next() {
  case "${1:-}" in
    start)
      $DOCKER compose up -d --build "$NEXT_SERVICE"
      echo "Neubau läuft unter $NEXT_URL"
      ;;
    stop) $DOCKER compose stop "$NEXT_SERVICE" ;;
    restart) $DOCKER compose restart "$NEXT_SERVICE" ;;
    update)
      $DOCKER compose build --no-cache "$NEXT_SERVICE"
      $DOCKER compose up -d "$NEXT_SERVICE"
      echo "Neubau aktualisiert und neu gestartet unter $NEXT_URL"
      ;;
    logs)
      if [ ! -f "$NEXT_LOG_FILE" ]; then
        echo "$NEXT_LOG_FILE fehlt noch; Container-Ausgabe:"
        $DOCKER compose logs "$NEXT_SERVICE"
        return
      fi
      tail -n 50 -F "$NEXT_LOG_FILE"
      ;;
    status)
      $DOCKER compose ps -a "$NEXT_SERVICE"
      if curl -fsS --max-time 3 "$NEXT_URL/api/core/health" 2>/dev/null; then
        echo
      else
        echo "Der Neubau antwortet nicht unter $NEXT_URL" >&2
      fi
      ;;
    *) usage; exit 1 ;;
  esac
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
  next)    shift; cmd_next "$@" ;;
  *)       usage; exit 1 ;;
esac

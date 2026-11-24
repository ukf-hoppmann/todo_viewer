# Betrieb

## Deployment

Der Viewer läuft als Docker-Container, gesteuert mit `./todo.sh` (siehe [README](../../README.md)). Beteiligt sind zwei
Dienste aus `docker-compose.yml`:

- **Image** (`server/Dockerfile`, gebaut vom Projektordner). Stage 1 baut den Client (`node:22-alpine`, `npm ci
  --ignore-scripts`, `vite build`). Stage 2 (`python:3.11-slim`) installiert den Server (`pip install -c
  server/constraints.txt ./server`; die Versionen in `server/constraints.txt` sind die getesteten) und kopiert
  `client/dist`. Der Server liefert `/` (die Oberfläche, `index.html` für jede Adresse der Oberfläche), `/api/…`
  (HTTP-API, Health: `GET /api/core/health`) und `/mcp` (MCP für KI-Agenten). Ein `HEALTHCHECK` fragt die
  Health-Adresse.
- **Dienst `todo-viewer-next`** (Container gleichen Namens). `restart: unless-stopped`; der Port ist nur an
  `127.0.0.1:5411` gebunden, weil API und MCP alles ändern können. Volumes: `./configs` → `/app/configs`
  (`viewer.db`, `configs/backups`), `./logs` → `/app/logs` (`viewer.log`) und der Projekte-Ordner des Hosts unter
  demselben Pfad (Spiegel-Ordner; `BROWSE_START` zeigt dorthin).
- **Proxy `todo-proxy`** (`nginx:1.27-alpine`, Konfiguration `nginx/todo.localhost.conf`, schreibgeschützt eingebunden).
  Er leitet `http://todo.localhost:5413` an den Viewer weiter, ohne Pufferung und mit 1 h Lese-Timeout (Ereignisstrom
  unter `/api/core/events`, MCP-Streams unter `/mcp`); andere Hostnamen beantwortet er nicht. Er löst den Namen des
  Viewers bei Bedarf neu auf, ein Neustart des Viewers braucht also keinen Neustart des Proxys. Der Host-Port ist nur an
  `127.0.0.1:5413` gebunden und muss frei sein; sonst startet der Proxy nicht, der Viewer bleibt unter
  `http://localhost:5411` erreichbar. `*.localhost` löst macOS ohne `/etc/hosts`-Eintrag auf `127.0.0.1` auf.
- **Umgebung im Container** (siehe [Konfiguration](configuration.md)): `VIEWER_HOST=0.0.0.0`, `VIEWER_PORT=5411`,
  `VIEWER_DB=/app/configs/viewer.db`, `VIEWER_BACKUP_DIR=/app/configs/backups`, `VIEWER_LOG_DIR=/app/logs`,
  `VIEWER_STATIC_DIR=/app/client/dist` und `TZ`. Ohne `TZ` rechnet der Container in UTC. Prüfung der Zone:
  `docker exec todo-viewer-next python -c "import datetime; print(datetime.datetime.now().astimezone())"` zeigt die
  Ortszeit.

## Befehle (`./todo.sh`)

| Befehl | Wirkung |
|---|---|
| `start` | Baut das Image (falls nötig), startet Viewer und Proxy im Hintergrund und öffnet den Browser |
| `stop` / `restart` | Hält beide Container an bzw. startet sie neu |
| `down` | Entfernt die Container; `configs/` und `logs/` auf dem Host bleiben |
| `update` | Baut ohne Cache neu und ersetzt die Container, z. B. nach Code-Änderungen |
| `logs` | Folgt `logs/viewer.log`, sonst der Container-Ausgabe |
| `status` | Zustand der Container und Antwort von `/api/core/health`, direkt und über den Proxy |
| `open` | Öffnet nur den Browser |

## Datenbank und Sicherungen

- Alle Daten liegen in der SQLite-Datei `configs/viewer.db` (im Betrieb mit `viewer.db-wal` und `viewer.db-shm`). Das
  Schema wird beim Start vorwärts migriert (versionierte Migrationen je Plugin).
- Der Dienst sichert die Datenbank selbst nach `configs/backups/viewer-<Zeit>Z-<Grund>.db` (SQLite-Backup, auch im
  laufenden Betrieb): Grund `migration` (vor der ersten ausstehenden Migration einer nicht leeren Datenbank), `sync`
  (vor einem Abgleich, der die Datenbank ändert), `purge` (vor dem
  endgültigen Löschen aus dem Papierkorb) und `import` (vor der Datenübernahme in eine bestehende Datei). Je Grund
  bleiben die letzten 10; ältere löscht der Dienst. Scheitert die Sicherung, wird nichts geändert.
- Wiederherstellen: `./todo.sh stop`, die gewählte Sicherung nach `configs/viewer.db` kopieren (`-wal` und `-shm`
  daneben löschen), `./todo.sh start`.
- Manuelle Sicherung bei gestopptem Container: alle drei Dateien kopieren; im laufenden Betrieb
  `sqlite3 configs/viewer.db ".backup configs/viewer-backup.db"`.

## Spiegel und Sync

- Ein Projekt kann einen Spiegel-Ordner haben (Backlog, Memos und Wecker als Markdown, Format siehe
  [Schnittstellen](interfaces.md)). Er trägt die Daten über Git zwischen Rechnern und in die Cloud (claude.ai). Neue
  Einträge dort legt man mit einem Platzhalter an; der Sync vergibt `Uid` und Label. Die Mindmap liegt im Unterordner
  `mindmap/` des Spiegel-Ordners (Knoten, Bäume, Dokumente; eigenes Format, siehe [Schnittstellen](interfaces.md)); eine
  Cloud-Sitzung bearbeitet sie wie die übrigen Dateien, der nächste Sync übernimmt sie.
- Der Sync gleicht Eintrag für Eintrag ab und zeigt vorher eine Vorschau. Was nur auf einer Seite geändert wurde, geht
  auf die andere. Ein Eintrag, der auf beiden Seiten geändert, auf beiden neu oder auf einer Seite gelöscht wurde, ist
  ein Konflikt: er wird nie überschrieben oder gelöscht, und man entscheidet je Konflikt (Datenbank, Dateien oder
  später). Löschungen nehmen die Sammelknöpfe aus. Die Richtung lässt sich auf eine Seite beschränken.
- Auto-Sync (je Projekt, Standard aus; Takt siehe [Konfiguration](configuration.md)): überträgt nur Konfliktfreies, löscht
  nie und pausiert, wenn der Ordner fehlt oder nicht lesbar ist, Git-Merge-Marker enthält oder ein Git-Vorgang läuft. Die
  Projektliste zeigt ⚠ bei „braucht dich“ und „pausiert“ und ↻ bei einem gespiegelten Projekt. Ohne eingeschalteten
  Auto-Sync läuft kein Timer.
- Eine Löschung, die man bewusst ausführt (endgültig aus dem Papierkorb, Notiz oder Spec in den Papierkorb), geht sofort
  auch in die Spiegel-Dateien, sofern der Eintrag dort seit dem letzten Sync unverändert ist; sonst bleibt es ein
  Konflikt. Davor wird die Datenbank gesichert.
- Ein Formatfehler in den Dateien bricht den Sync vor jeder Änderung ab; die Meldung nennt Datei und Zeile.

## Datenübernahme aus dem alten Viewer

Einmalig (nur der Projektinhaber): `python -m viewer.app.import_legacy` liest die alte Datenbank `configs/todo.db`
schreibgeschützt und schreibt nur, wenn alles geprüft ist. Erst mit `--dry-run` laufen lassen. Markdown-primäre Projekte
müssen vorher im alten Viewer in ihre Datenbank gespiegelt sein. Ablauf und Abbildung: [Neubau: Server](neubau-server.md).

## Memos und Wecker im Betrieb

- Zeitpunkte speichert und liefert die API in UTC. Die Oberfläche zeigt und erfragt sie in der Zeitzone des Rechners.
  Wer die API direkt aufruft, übergibt ISO 8601 mit Zeitzone.
- Es gibt keinen Hintergrund-Takt außer dem Scheduler des Servers, der nur den nächsten fälligen Zeitpunkt vormerkt. Ob ein
  Memo fällig ist, wird beim Lesen berechnet; ein Viewer ohne offenes Fenster kostet nichts und meldet nichts.
- Der Server holt verpasste Wecker beim Start nach. Browser-Benachrichtigungen schaltet man in den Einstellungen ein.
- Es gibt kein endgültiges Löschen und keine Einstellungsänderung als MCP-Tool; beides geht nur in der Oberfläche.

## Log

`logs/viewer.log` enthält je Ereignis eine JSON-Zeile, rotiert. Alle Zeilen eines Requests tragen dieselbe Request-ID
(`X-Request-ID`, vom Client übernommen, wenn sie `[A-Za-z0-9._-]{1,64}` ist). Warnungen und Fehler der Oberfläche
landen über `POST /api/core/client-log` ebenfalls dort. Meldungen vor der Log-Einrichtung stehen in
`docker compose logs todo-viewer-next`.

```bash
grep -i '"level": *"error"' logs/viewer.log | tail -20   # letzte Fehler
grep 'version_conflict' logs/viewer.log                # nach Fehlercode
grep '<request-id>' logs/viewer.log                    # alles zu einem Request
```

## Prüfen

`scripts/check-next.sh` führt Lint, Typen, Schichtregeln und Tests von Server und Client aus (inklusive der Systemtests
des Servers als Prozess und von `todo.sh`). Den Image-Test (`tests/implementation/system/ops/test_image.py`) startet man
mit einem laufenden Docker und `VIEWER_IMAGE_TEST=1`; ohne Docker wird er übersprungen. Es gibt keine CI.

## Fehlerbilder

| Symptom | Ursache | Behebung |
|---|---|---|
| Proxy startet nicht | Host-Port 5413 ist belegt | Port freigeben; der Viewer bleibt unter `http://localhost:5411` erreichbar |
| `todo.localhost:5413` antwortet nicht, `localhost:5411` schon | Proxy gestoppt oder anderer Hostname | `./todo.sh status`, `./todo.sh restart` |
| Banner „Server nicht erreichbar“ in der Oberfläche | Viewer gestoppt oder startet noch | `./todo.sh status`; die Oberfläche prüft selbst erneut und lädt danach neu |
| Nur die API antwortet, keine Oberfläche | `VIEWER_STATIC_DIR` zeigt auf einen fehlenden Ordner (lokaler Start ohne Build) | `cd client && npm run build` oder das Image verwenden |
| Speichern bricht mit `version_conflict` ab | Das Element wurde seit dem Lesen geändert, z. B. durch einen Agenten | Aktuellen Stand laden und erneut bearbeiten |
| Sync meldet einen Formatfehler | Eine Datei im Spiegel-Ordner verletzt das Format; nichts wurde geändert | Datei und Zeile aus der Meldung korrigieren, Vorschau wiederholen |
| Sync bricht mit `mirror_conflict` ab | Eine Datei hat sich während des Schreibens geändert | Vorschau neu holen und wiederholen |
| Auto-Sync pausiert | Ordner fehlt, nicht lesbar, Git-Merge-Marker oder laufender Git-Vorgang | Ursache beheben; der nächste gute Lauf setzt fort |
| Serientermine der Wecker verschoben | `TZ` fehlt, der Container rechnet in UTC | `TZ` setzen (`todo.sh` tut es selbst), Container neu starten |
| Sicherung scheitert | `configs/backups/` nicht beschreibbar oder Platte voll | Ursache beheben; bis dahin wird nichts migriert oder synchronisiert |

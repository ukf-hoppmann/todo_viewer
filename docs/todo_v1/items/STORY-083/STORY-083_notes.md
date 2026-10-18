# STORY-083 — Notizen

## 2026-10-17 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- **Auslieferung.** Der Server liefert das gebaute Frontend selbst aus (`core/api/frontend.py`): Dateien aus `static_dir` (Einstellung `static_dir`, Umgebung `VIEWER_STATIC_DIR`, Standard `client/dist`), `index.html` für alle übrigen Adressen der Oberfläche (der Client benutzt einen Browser-Router), unter `/api` und `/mcp` nie – dort ist eine unbekannte Adresse ein 404 im Fehlerformat. Fehlt der Ordner, läuft nur die API. Die Route steht zuletzt, damit API und MCP gewinnen.
- **Image.** `server/Dockerfile`, gebaut vom Projektordner aus (der Client liegt neben dem Server): Stage 1 `node:22-alpine` baut mit `vite build` (Typen und Lint prüft `check-next.sh`, nicht das Image; `--ignore-scripts`, weil `postinstall` Test-Ordner verlinkt); Stage 2 `python:3.11-slim` installiert `server/` (neu: `[build-system]` mit setuptools in `server/pyproject.toml`) mit den getesteten Versionen aus `server/constraints.txt` und kopiert `client/dist`. Umgebung: Host `0.0.0.0`, Port 5412, Datenbank, Backups und Logs unter `/app/configs` bzw. `/app/logs`.
- **Compose.** Dienst `todo-viewer-next` neben `todo-viewer`: Port `127.0.0.1:5412`, `restart: unless-stopped`, Volumes `./configs`, `./logs` und der Projekte-Ordner (`BROWSE_START` wie beim alten Dienst). Der alte Dienst bleibt unverändert.
- **`todo.sh`.** `next start|stop|restart|update|logs|status`. Weil die Compose-Datei jetzt zwei Dienste hat, nennen die alten Befehle ihren Dienst ausdrücklich (`todo-viewer`), sonst würden `start`/`update` beide betreffen; `down` bleibt für beide. `DOCKER` ersetzt das Programm für die Tests.
- **Backups.** Keine neue Rotation: `SqliteBackupMaker` (`STORY-063`) behält je Grund (`migration`, `sync`, `import`) die letzten 10; die Doku nennt das.
- **Tests.** Frontend-Auslieferung (Integration, `test_frontend.py`); `todo.sh` mit einem Ersatz für `docker` und die Compose-Datei mit `docker compose config` (`tests/implementation/system/ops/test_todo_script.py`); der Server als echter Prozess (`test_server_process.py`: Health, Frontend, MCP, Dateien); das Image bauen, starten und `GET /api/core/health` fragen (`test_image.py`, eigener Befehl, übersprungen ohne Docker-Daemon). Wo Docker nicht läuft oder die Registry nicht erreichbar ist, wird „Image nicht gebaut, nicht geprüft“ vermerkt.

### Decided

1. Server liefert das Frontend (mit Tests). 2. Dockerfile, `pyproject`-Build, Constraints. 3. Compose-Dienst und `todo.sh next`. 4. Systemtests und Techdoku (`operations.md`, `tests/README.md`, `neubau-server.md`), Checks, Status.

### Open

- Keine neuen Fragen.

## 2026-10-17 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Wie geplant. Beim Bauen des Images fiel ein echter Fehler auf: `npm ci` im Container scheiterte mit `ERESOLVE`, weil `client/.npmrc` (`legacy-peer-deps=true`) nicht mitkopiert war; das Dockerfile kopiert sie jetzt mit.
- Der Image-Test in `tests/implementation/system/ops/test_image.py` ist eine Wahl (`VIEWER_IMAGE_TEST=1`), nicht Teil von `check-next.sh`: er lädt Basis-Images und Pakete aus dem Netz und dauert Minuten.
- In dieser Sitzung erreicht der Docker-Daemon (selbst gestartet) die Pakete nur über den TLS-abfangenden Proxy der Sitzung; das Dockerfile bleibt davon frei. Zur Prüfung wurde dasselbe Dockerfile mit zusätzlich eingefügtem CA-Zertifikat der Sitzung gebaut (Datei nur in dieser Sitzung, danach gelöscht).

### Decided

- Abschlusskriterien geprüft: (1) Dockerfile baut Server und Client in ein Image, der Server liefert das Frontend aus: das Image wurde (mit dem CA-Zusatz) gebaut und gestartet, `GET /api/core/health` → `{"status":"ok"}`, `/` und `/notes/main` liefern `index.html`, `/api/nope` ist ein 404 im Fehlerformat, `viewer.db` und `viewer.log` entstehen in den Volumes, der `HEALTHCHECK` meldet `healthy`; (2) `docker compose config` kennt den Dienst `todo-viewer-next` (Port 127.0.0.1:5412, `restart: unless-stopped`, Volumes `configs/` und `logs/`, `BROWSE_START`) neben dem unveränderten alten Dienst (`test_todo_script.py`); (3) `todo.sh next start|stop|restart|update|logs|status` (`test_todo_script.py`, mit Ersatz für `docker`); (4) `docs/techdocs/operations.md`, Abschnitt „Neubau (EPIC-007)“, dazu `neubau-server.md` (Einstellung `static_dir`) und `tests/README.md`.
- Dazu: Server als echter Prozess (`test_server_process.py`: Health, Frontend, MCP, Dateien) und die Auslieferung des Frontends (`test_frontend.py`).
- `scripts/check-next.sh` und `scripts/check.sh` grün. Status: `Awaiting confirmation`.

### Open

- Nicht geprüft: der Test `test_image.py` selbst in dieser Sitzung (scheitert hier nur an der Proxy-Zertifikatskette beim `pip install`; von Hand geprüft, siehe oben); ein Start mit `docker compose up` und echten Projekt-Ordnern (Pfad `/Users/hoppmann/…` gibt es hier nicht); Verhalten auf macOS (Bind-Mounts).
- Die Versionen in `server/constraints.txt` sind die der Entwicklungsumgebung; sie müssen bei Abhängigkeits-Updates mitgezogen werden.

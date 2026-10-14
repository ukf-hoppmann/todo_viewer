# TASK-014 — Spec: Offenes Item zur Note zurückstufen (Backend)

## Arbeitsweise (gilt für jede Task dieser Epic)
- Vorher lesen: `docs/development/architecture.md`, die Scope-Datei (`docs/development/architecture/backend.md` bzw. `web.md`) und die Spec der Story (STORY-042), die das Gesamtbild gibt. **Diese Task-Spec legt den Umfang fest; was hier nicht steht, gehört nicht dazu.**
- Skills laden: `claude-harness:decomposition` (Plan in Abschnitten, jeder testbar), `claude-harness:testing` (Testorte). Neues Verhalten: Test zuerst, er muss aus dem erwarteten Grund fehlschlagen.
- Fertig ist die Task, wenn `scripts/check.sh` grün ist. Ändert sich ein API-Schema: `python backend/scripts/export_openapi.py`, dann `npm run gen:api` in `web/`; `schema.d.ts` und `openapi.json` nie von Hand ändern.
- Techdocs und README schreibt STORY-046 gesammelt. Halte dafür in den Backlog-Notes dieser Task fest: neue Routen, Fehlercodes, Konfiguration, Besonderheiten (kurz, als `Decided`-Einträge).
- Backlog: Task beim Start auf `In progress`, bei erfüllten Abschlusskriterien auf `Awaiting confirmation` setzen. Die Specs der abhängigen Tasks stehen unter den Dependencies.
- Weicht der Code von dieser Spec ab (Datei, Name oder Verhalten anders als beschrieben): nicht raten, anhalten und fragen. Das gilt auch für jeden Punkt unter „Stoppen und fragen“.
- Verweise auf andere Tasks dieser Epic nennen deren echte ID (TASK-0xx); ihre Specs sind über `show`/`doc` lesbar.

## Ziel
Richtung Item → Note der STORY-042 (Backend und HTTP).

## Schon vorhanden (nach TASK-013)
`ConversionService`, `domain/conversion.py`, Link `origin` (TASK-007), Note-Dokumente (TASK-008), `ItemService.update` mit Statuswechsel und `resolution`, die Backlog-Regeln in `domain/lifecycle.py`.

## Festgelegte Regeln und Reihenfolge
Zulässig nur, wenn alle drei gelten; sonst Fehler mit Code:
- `demote_not_open`: Status ist nicht `Open`.
- `demote_has_children`: das Item hat Kinder (auch geschlossene zählen, sie hängen am Parent).
- `demote_referenced`: das Item ist Parent oder Dependency eines anderen Items.
Die Prüfung ist eine reine Funktion `check_demote(item, all_items)` in `domain/conversion.py`.

Ablauf (Reihenfolge ist Pflicht):
1. Prüfen (siehe oben), Token des Items prüfen.
2. Note anlegen: `summary` = Titel des Items (Kurzfassung ist eine Zeile), `body` = Zusammenfassung des Items (falls vorhanden), Topic nach Wahl des Aufrufers (optional).
3. **Sofort** den Link `origin` Note → Item anlegen (Beleg für den Abbruchfall).
4. Notizen und Specs des Items als Dokumente der Note anlegen (Namen mit der Note-Label); vorhandene Dokumente nicht überschreiben.
5. Das Item abschließen. Welcher Status: `Rejected` mit Resolution „zur Notiz zurückgestuft“ (das Item wurde nicht umgesetzt). Die Rückstufung selbst ist die Entscheidung des Besitzers, es braucht keine zweite Bestätigung; die Statusprüfungen des Backlogs müssen sie trotzdem zulassen. Das Item wandert damit ins Archiv wie jedes abgeschlossene Item.
6. Wiederholung ist idempotent: existiert zur Note schon ein `origin`-Link auf dieses Item, werden Schritt 2 und 3 übersprungen; fehlende Dokumente und der Abschluss werden nachgeholt.

Die Hinweise aus TASK-011 (Item abgeschlossen) dürfen für die neue Note **nicht** entstehen: Der Link ist `origin`, nicht `reference`.

## Zu tun
1. `check_demote` in `domain/conversion.py` und `ConversionService.demote(source, item_id, version, topic?)` mit obigem Ablauf; neue Fehlercodes (`demote_not_open`, `demote_has_children`, `demote_referenced`) als `DomainError`-Unterklassen.
2. Route `POST /api/v2/items/{source_id}/{item_id}/demote` Body `{version, topic?}` → `{item, note: NoteOut}`; `topic` ist ein Topic-Label im Projekt der Quelle.
3. Wenn der Abschluss in 5 am Backlog-Lifecycle scheitert (z. B. Status `Rejected` ist von `Open` aus nicht erlaubt), nicht umgehen, sondern anhalten und fragen.
4. OpenAPI neu erzeugen.

## Dateien
`domain/conversion.py`, `domain/errors.py`, `application/services/conversion.py`, `api/v2/routers.py` (Items-Route) oder `notes_routers.py`, `schemas.py`, Tests `backend/tests/unit/domain/test_conversion.py`, `tests/unit/application/test_conversion.py`, `tests/api_v2/test_demote.py`.

## Nicht anfassen
Beförderung (TASK-013), die Lifecycle-Regeln des Backlogs, das UI-Formular.

## Tests (zuerst; ein Fall je Zeile)
Erfolg; nicht Open; mit Kindern; als Parent referenziert; als Dependency referenziert; Notizen und Specs an der Note; Link `origin` an Note und Item; Item archiviert mit der Resolution; kein Hinweis aus TASK-011; Abbruch nach Schritt 3 und Wiederholung → genau eine Note; Markdown- und Datenbank-Projekt.

## Stoppen und fragen
Wenn `Open → Rejected` im Backlog-Lifecycle nicht ohne Zwischenstatus geht, oder wenn der Besitzer statt `Rejected` lieber `Completed` will (Entscheidung steht in den Backlog-Notes von STORY-042 offen).

## Abnahme
Erfolg und alle drei Ablehnungsgründe per Test; Wiederholung idempotent; `scripts/check.sh` grün.

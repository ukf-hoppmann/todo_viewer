# STORY-093 — Spec: Item-Notes mit Kopf und Protokoll

Diese Spec ist der aktuelle technische Stand; der Weg zu den Entscheidungen
steht in den Notes. Gegenstück im Harness: STORY-051 (Claude_Harness,
`docs/todo/items/STORY-051/STORY-051_spec.md`), dort vor allem „Aufbau der
Notes-Datei“, „Absicherung des Kopfs“, „Umstellung“ und „Schnittstelle zum
ToDo-Viewer“. Bei Widersprüchen zur Prüfsumme oder zum Dateiaufbau gilt
`plugin/skills/todo/format.md` des Harness (gemeinsamer Vertrag, TASK-021).

## Was und warum

Die Notes eines Backlog-Items (`<ID>_notes.md`) bestehen künftig aus einem
**Kopf** (`## Stand`, geltender Stand, wird ersetzt) und einem **Protokoll**
(datierte Einträge, wird angehängt). Ein **Stempel** hält fest, gegen welchen
Protokollstand der Kopf zuletzt angepasst oder bestätigt wurde. Der Harness
lädt so den Kopf ohne das Protokoll und erzwingt nach Änderungen eine Prüfung
des Kopfs.

Betroffen sind nur die Notes von Backlog-Items (Plugin `backlog`). Specs
bleiben unverändert. Die Dokumente der Notes im Plugin `notes` (Merkzettel)
sind nicht betroffen.

## Dateiaufbau (zusammengesetzte Form)

```markdown
# <Label> — <Titel>
<Vorspann, falls vorhanden>
## Stand

<Kopf>

Stand bestätigt nach Eintrag <YYYY-MM-DD> — <Thema> (<Prüfsumme>)

## <YYYY-MM-DD> — <Thema>
…
```

- **Titelzeile:** wird immer aus dem aktuellen Label und Titel des Items
  erzeugt. Eine Titelzeile in eingehendem Text (erste Zeile, beginnt mit
  `# `) wird verworfen; fehlt sie, geht nichts verloren. Damit folgt die
  Titelzeile auch einem Typwechsel.
- **Protokolleintrag:** beginnt mit einer Zeile, die auf
  `^## \d{4}-\d{2}-\d{2} — ` passt (Gedankenstrich U+2014), und reicht bis
  vor die nächste solche Zeile oder das Dateiende. Datum und Thema kommen aus
  der Überschrift, der Rest ist der Text des Eintrags, unverändert
  (Leerzeilen am Ende eingeschlossen).
- **Kopf:** der Abschnitt ab der Zeile `## Stand` vor dem ersten Eintrag, ohne
  die Überschrift, ohne die Stempelzeile und ohne umgebende Leerzeilen.
- **Stempelzeile:** die letzte nichtleere Zeile des Kopf-Abschnitts, wenn sie
  auf `^Stand bestätigt nach Eintrag (\d{4}-\d{2}-\d{2}) — (.+) \(([0-9a-f]{12})\)$`
  passt.
- **Vorspann:** alles zwischen Titelzeile und `## Stand` bzw. erstem Eintrag
  (z. B. ein altes `## Summary`), unverändert. Gehört weder zum Kopf noch zum
  Protokoll. Notes ganz ohne datierte Einträge (ältere Formate) bestehen nur
  aus Vorspann.
- **Zusammensetzen:** Titelzeile, Vorspann; dann, falls ein Kopf da ist,
  `## Stand`, Leerzeile, Kopf, Leerzeile, Stempelzeile (falls vorhanden),
  Leerzeile; dann die Einträge.
- **Verlustfreiheit:** Für Notes ohne Kopf gilt
  `zusammensetzen(zerlegen(t)) == t` bis auf die Titelzeile. Notes mit Kopf
  werden beim Zusammensetzen auf das obige Layout normalisiert.

## Prüfsumme und Zustand

- Prüfsumme: SHA-256 über die kanonische Form des Protokolls, davon die ersten
  12 Hex-Zeichen (Kleinbuchstaben). Kanonische Form: alle Einträge in ihrer
  Reihenfolge ab der ersten Eintragszeile, Zeilenenden LF, Leerzeichen und
  Tabs am Zeilenende entfernt, genau ein Zeilenumbruch am Ende. Vorspann,
  Kopf und Stempel gehören nicht dazu. Maßgeblich ist `format.md` des
  Harness. Ein leeres Protokoll braucht keine Prüfsumme, weil es ohne Eintrag
  keinen Stempel gibt. Testvektoren: `tests/fixtures/notes-state/checksum.json`,
  erzeugt direkt aus dieser Definition; der Harness übernimmt sie (TASK-022).
- Zustand des Kopfs (`notes_state`):
  - `null`: das Item hat keine Notes.
  - `missing`: Notes ohne Kopf (auch leerer Kopf). Kein Fehler.
  - `stale`: Kopf vorhanden, aber kein Stempel oder Prüfsumme des Stempels ≠
    aktuelle Prüfsumme.
  - `current`: sonst.
- Zerlegen, Zusammensetzen, kanonische Form, Prüfsumme, Zustand und die
  Hinweise unten sind reine Funktionen in `plugins/backlog/domain/`
  (Architektur server §1 und §2).

## Datenmodell

Neue Tabellen des Plugins `backlog` (Migration v3, vorwärts, mit dem Backup
des Cores davor):

- `backlog_notes`: eine Zeile pro Item mit Notes. `item_uid` (PK, FK auf
  `backlog_items`, `ON DELETE CASCADE`), `name` (`<Label>_notes.md`),
  `preamble` (Text, leer erlaubt), `state` (Kopf, Text, leer = kein Kopf),
  `stamp_day`, `stamp_topic`, `stamp_checksum` (alle NULL ohne Stempel),
  `state_revision` (Version des Kopfs), `revision` (Version der
  zusammengesetzten Datei), `updated_at`.
- `backlog_notes_entries`: `item_uid` (FK, `ON DELETE CASCADE`), `position`
  (0…n-1, PK zusammen mit `item_uid`), `day` (TEXT `YYYY-MM-DD`), `topic`,
  `body` (Markdown nach der Überschriftszeile, unverändert).
- Versionen: `revision` steigt bei jeder Änderung an Vorspann, Kopf, Stempel
  oder Protokoll; sie ist die `version` der zusammengesetzten Datei in den
  bisherigen Endpunkten. `state_revision` steigt bei jeder Änderung von Kopf
  oder Stempel; sie ist die `version` der Kopf-Endpunkte. Anhängen eines
  Eintrags ändert nur `revision`, so dass Anhängen und Kopf-Bearbeitung sich
  nicht gegenseitig in `version_conflict` treiben.
- Die Migration zerlegt alle Dokumente mit `kind = 'notes'` aus
  `backlog_documents` nach den Regeln oben, schreibt sie in die neuen Tabellen
  und entfernt sie aus `backlog_documents` (dort bleiben nur Specs). Ein
  vorhandenes `## Stand` wird Kopf, eine gültige Stempelzeile wird Stempel.
  Ergibt das Zusammensetzen für ein Dokument nicht wieder den Ursprungstext
  (bis auf die Titelzeile, bei Notes ohne Kopf), kommt dessen ganzer Text
  nach der Titelzeile in den Vorspann. So geht nie Text verloren. Es werden
  keine Köpfe erzeugt (Harness: kein Massenlauf).
- Repository: `Item.notes` (Liste der Namen) kommt künftig aus
  `backlog_notes`. Typwechsel benennt `name` dort um wie heute in
  `backlog_documents`.

## Endpunkte (Operationen, HTTP und MCP)

Alle als Operationen des Plugins `backlog`, also auch als MCP-Tools
(`backlog_<name>`). Fehler als `DomainError` mit stabilem `code`.

Neu:

| Operation | HTTP | Eingabe | Ausgabe |
|---|---|---|---|
| `get_notes_state` | `GET /items/{ref}/notes/state` | `ref`, `project` | `NotesStateOut` |
| `put_notes_state` | `PUT /items/{ref}/notes/state` | `content`, `version` (= `state_revision`, Pflicht) | `NotesStateOut` |
| `confirm_notes_state` | `POST /items/{ref}/notes/state/confirm` | `version` | `NotesStateOut` |
| `list_notes_entries` | `GET /items/{ref}/notes/entries` | `last` (optional, die letzten N) | Liste von `{position, day, topic, text}` |

- `NotesStateOut`: `name`, `content` (Kopf), `stamp` (`{day, topic,
  checksum}` oder `null`), `state` (`current`/`stale`/`missing`),
  `checksum` (aktuelle Prüfsumme des Protokolls), `last_entry` (`{day,
  topic}` oder `null`), `version` (= `state_revision`), `hints`.
- `put_notes_state` ersetzt den Kopf und setzt den Stempel auf den letzten
  Eintrag und die aktuelle Prüfsumme. Es legt keine Notes an: ohne Notes
  `notes_not_found`, ohne Protokolleintrag `notes_without_entries`. Neue Notes
  mit Kopf entstehen mit `append_note` und `state`. Ein leerer Kopf ist
  `invalid_input`.
- `confirm_notes_state` setzt nur den Stempel; ohne Kopf Fehler
  `notes_state_missing`.
- Ohne Protokolleinträge kann kein Stempel gesetzt werden (Fehler
  `notes_without_entries`).
- Fehlercodes `notes_not_found`, `notes_state_missing`,
  `notes_without_entries` antworten mit HTTP 400 (Standard des Cores).
- `text` in `list_notes_entries` ist der Eintrag mit Überschriftszeile.

Erweitert, rückwärtskompatibel (Felder nur zusätzlich):

- `append_note` (`POST /items/{ref}/notes`): optional `state` (neuer Kopf)
  und `state_version` (nötig, wenn schon ein Kopf existiert). Erst wird der
  Eintrag angehängt, dann der Kopf ersetzt und gestempelt, in einer
  Transaktion. Ausgabe `DocumentOut` wie bisher plus `notes_state` und
  `hints`.
- `get_document` / `put_document` auf `<ID>_notes.md`: arbeiten auf der
  zusammengesetzten Datei mit `version` = `revision`. `put_document` zerlegt
  den Text: Vorspann und Protokoll werden ersetzt; ein Abschnitt `## Stand`
  ersetzt den Kopf, fehlt er, bleibt der Kopf unverändert. Eine Stempelzeile
  im Text wird ignoriert; den Stempel setzt über die API nur der Server
  (`put_notes_state`, `confirm_notes_state`, `append_note` mit `state`).
  `put_document` ändert den Stempel nie. Ausgabe plus `notes_state` und
  `hints`. Anlegen per `put_document` (`version` fehlt) zerlegt ebenso.
- `list_documents`: listet die Notes weiter mit Name, Art und `version`.
- `get_item` (`show`): neues Feld `notes_state`. `index_lines` (`index`):
  neue letzte Spalte `Notes` mit `current`/`stale`/`missing` oder `-`.
- Interne Nutzer (Befördern und Zurückstufen im Plugin `notes` über
  `backlog_gateway`) bleiben bei `get_document`/`put_document` und
  bekommen dadurch Zerlegen und Zusammensetzen mit.

Hinweise (`hints`: Liste von `{code, message}`, nie Ablehnung):

- `notes_state_stale`: der Kopf ist nach dem Schreiben `stale` oder `missing`.
- `notes_state_long`: mehr als 15 Punkte unter `- Beschlossen:` im Kopf
  (Unterpunkte bis zum nächsten Punkt der obersten Ebene).
- `notes_history_rewritten`: `put_document` hat einen bisherigen Eintrag
  geändert oder entfernt (Vergleich je Position mit dem gespeicherten Stand;
  neue Einträge am Ende zählen nicht).

Ereignis: jede Änderung an den Notes veröffentlicht wie bisher
`backlog.document.changed` (`uid`, `name`, `change`).

Fähigkeitsprüfung des Harness: ein Viewer ohne Köpfe antwortet auf
`GET …/notes/state` mit 404; mehr braucht es nicht.

## Spiegel

- Ein Spiegel-Eintrag `backlog.document` pro Notes-Datei. Für Notizen
  enthält er den Text **ohne Titelzeile** (`content`) und den Titel des Items
  (`title`); beim Einlesen kommt `title` aus dem Item-Eintrag in `TODO.md`,
  nicht aus der Datei. Der Codec schreibt die Titelzeile aus Label und `title`.
  Die Titelzeile ist damit abgeleitet und wird nicht verglichen: Ein
  Typwechsel ist nur ein Umbenennen, ein Titelwechsel schreibt die Datei neu,
  und eine abweichende alte Titelzeile (z. B. `— Notizen`) ist kein Konflikt;
  sie wird beim nächsten Schreiben der Datei erneuert.
- Der Sync-Teilnehmer setzt beim Lesen aus der Datenbank zusammen und zerlegt
  beim Schreiben in die Datenbank. Anders als über die API wird eine gültige
  Stempelzeile aus der Datei übernommen (Files-Modus bestätigt mit
  `backlog.py --confirm-state`). Fehlt `## Stand` in der Datei, wird der Kopf
  geleert, weil die Datei dort die ganze Wahrheit ist.
- Die Fälle (Kopf mit Stempel, Vorspann, ohne datierte Einträge, abweichende
  Titelzeile, Typ- und Titelwechsel) sind mit byte-genauen Erwartungen in den
  Spiegel-Tests abgedeckt.

## Oberfläche

- In der Detailansicht eines Items stehen bei den Notes oben der Kopf, darunter
  das Protokoll, standardmäßig eingeklappt. Ein Kopf `stale` oder `missing`
  ist sichtbar markiert (Symbol mit Tooltip). Daten nur über die RTK-Query-API
  des Plugins, nach `backlog.document.changed` neu laden; TypeScript-Typen
  aus dem OpenAPI-Schema neu erzeugen.
- Bearbeiten bleibt wie heute über die ganze Datei. Kopf bestätigen oder
  einzeln bearbeiten gibt es in der Oberfläche in dieser Story nicht.
- Baut auf dem gemeinsamen `DocumentsSection` auf; die zum Zeitpunkt der
  Spec nicht committeten Änderungen dort sind vorher abgeschlossen.

## Tests

- Unit (domain): Zerlegen und Zusammensetzen (mit und ohne Kopf, mit Vorspann,
  ohne Einträge, ohne Titelzeile, falsche Titelzeile), Verlustfreiheit,
  Prüfsumme gegen feste Testvektoren, Zustände, Hinweise.
- Testvektoren: synthetisch unter `tests/fixtures/notes-state/`, inhaltlich
  identisch mit den Vektoren des Harness (TASK-022); jede Änderung in beiden
  Projekten.
- Vertragstests der Endpunkte (HTTP und MCP): Versionen, Stempel, `append_note`
  mit `state`, `put_document` ohne `## Stand` und mit Stempelzeile,
  Fehlercodes, Hinweise.
- Migration: leere Datenbank bis v3 (Architektur server §5) und v2 mit
  Notes-Dokumenten → v3, inklusive Rückfall in den Vorspann.
- Spiegel: Contract-Suite des Teilnehmers und Golden Files, beide Richtungen.

## Dokumentation

- `docs/techdocs/interfaces.md`: neue Endpunkte, neue Felder, Hinweise,
  Fehlercodes, Dateiaufbau der Notes.
- `docs/techdocs/architecture.md`: Tabellen des Plugins `backlog`.

## Betrieb

- Vor dem Deployment ein geprüftes Backup der Datenbank; die Migration läuft
  beim Start.

## Nicht in dieser Story

- Entfernen der bisherigen Wege (`POST …/notes` ohne Kopf-Felder,
  `GET`/`PUT` auf die ganze Datei): eigene Folge-Story, sobald das
  Harness-Release (STORY-051, TASK-023) draußen ist. Dort auch, wie ältere
  Einträge danach korrigiert werden (z. B. ein Endpunkt je Eintrag).
- Regeln, Hooks und Helfer des Harness.

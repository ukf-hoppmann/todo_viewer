# STORY-095 — Spec: Sync-Konflikte erklären

## Anlass

Im Sync-Dialog ist oft nicht erkennbar, woher ein Konflikt kommt und was richtig wäre. Beispiel (Projekt
`image_refiner`, 2026-11-03): Die Datei `STORY-086_spec_nsfw-papierkorb.md` wurde in git umbenannt in
`STORY-086_spec_sensibel-papierkorb.md` und leicht geändert (`R074`). Der Sync ordnet Dokumente über
`<item-uid>/<suffix>` zu. Für ihn war das deshalb ein neuer Eintrag, der ohne Rückfrage übernommen wurde, und
ein Löschkonflikt „in den Dateien gelöscht“ für den alten. Die Datenbankseite war seit dem letzten Abgleich
unverändert. Richtig wäre also „Dateien übernehmen“, aber der Dialog gibt dafür keinen Hinweis.

## Grundsatz

Der Viewer erklärt und empfiehlt, entscheidet aber nicht. Löschkonflikte bleiben Konflikte (Architektur §2).
Eine Empfehlung wird nie vorausgewählt.

## Abgeleitete Angaben je Konflikt

Alles wird aus vorhandenen Daten berechnet: Einträge beider Seiten, Basis-Hash und `synced_at` je Eintrag in
`core_sync_state`. Es gibt keine neue Spalte und keine Migration.

1. **Geändert seit dem Abgleich, je Seite:** `database_changed` / `files_changed` aus dem Vergleich des
   Seiten-Hashes mit dem Basis-Hash. Ist eine Seite gelöscht, ist ihr Wert `null`. Bei `both_created` gibt es
   keine Basis; beide Werte sind dann `null`.
2. **Letzter Abgleich des Eintrags:** `synced_at` aus `core_sync_state`. Dafür braucht der Port
   `SyncStateStore` einen Lesezugriff je Eintrag.
3. **Umbenennungspartner** (nur bei `deleted_in_files` / `deleted_in_database`): Gesucht wird ein Eintrag auf
   der Seite, auf der gelöscht wurde. Er muss dieselbe `kind` und dieselben `refs` haben. Ob er neu ist oder schon
   früher übernommen wurde, spielt keine Rolle: im Beispiel stand der neue Name schon in der Datenbank und in der
   Basis. Die Ähnlichkeit ist `difflib.SequenceMatcher.ratio()` über die
   kanonische Feldform. Der Partner gilt ab einer Ähnlichkeit von 0,6. Gibt es mehrere, zählt der ähnlichste.
   Angezeigt werden Schlüssel, Label und Ähnlichkeit.
4. **Empfehlung** (`database` | `files` | `none`) mit Begründungscode:
   - Gelöscht auf einer Seite, die andere unverändert → die Löschung übernehmen (`deleted_other_unchanged`).
     Mit Umbenennungspartner: `renamed`.
   - Gelöscht auf einer Seite, die andere seither geändert → den Eintrag behalten (`deleted_other_changed`),
     sonst gehen Änderungen verloren.
   - `both_changed` / `both_created` → `none` (`both_changed` / `both_created`). Hier entscheidet der
     Besitzer anhand des Diffs.

Die Ableitungen sind reine Funktionen in `core/domain/sync.py`. Sie arbeiten nur auf `MirrorEntry`, ohne SQL,
Dateiformat oder Plugin-Wissen. Die Anwendungsschicht reicht sie über `ConflictOut` heraus.

## Dialog

- Die Überschrift ist Klartext aus Konfliktart und Herkunft, z. B. „In den Dateien gelöscht oder umbenannt. Die
  Datenbank ist unverändert seit dem 22.10.“
- Kontext in der Kopfzeile, z. B. „Spec zu STORY-086“, statt der Tabellenzeilen `kind` / `item`.
- Die empfohlene Option trägt die Markierung „Empfohlen“ und einen Satz Begründung. Ausgewählt ist nichts.
- Ein Umbenennungspartner wird genannt: „Wahrscheinlich umbenannt in `…` (95 % gleich)“.
- Sind beide Seiten vorhanden, wird der Text als zeilenweiser Diff gezeigt statt als zwei Volltexte. Kurze
  Felder bleiben in der Tabelle.

## Nicht Teil der Story

- Den Stand vom letzten Abgleich speichern, um bei `both_changed` die Änderungen je Seite zu zeigen
  (braucht eine Migration).
- Löschungen automatisch übernehmen, wenn die andere Seite unverändert ist (würde Architektur §2 ändern).
- Umbenennungen über git ermitteln.
- Einen Umbenennungspartner im Sync als Umbenennung ausführen, statt als Löschen und Neu-Anlegen.

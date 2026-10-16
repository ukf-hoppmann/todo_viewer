# Beispiele für Format Version 2

Beispiele für den Markdown-Spiegel des Neubaus (Format: Abschnitt
„Dateiformat Version 2“ in `docs/techdocs/interfaces.md`). Sie sind die
Golden-Files der Codecs (`STORY-075`, `STORY-079`, `STORY-080`) und des
Sync-Dienstes (`STORY-065`).

- `valid/`: ein vollständiges, gültiges Projekt namens `Beispiel` mit allen
  Feldern, einem abgeschlossenen und einem gelöschten Item, Dokumenten, einem
  neuen Item mit Platzhalter (`NEW-login-dialog`) samt Verweis darauf, Notes
  (mit Auslösern und Links, im Papierkorb, neu in der Cloud), Topics (eins
  archiviert, eins neu) und Weckern (mit Ziel, frei und zurückgestellt, neu
  mit Ziel in einem anderen Projekt).
- `invalid/<code>/`: je Fehlercode eine Kopie von `valid/` mit genau einem
  Fehler. `expected.json` nennt `code`, `file` und `line` des Fehlers, den
  der Sync melden muss, und den Grund.

Verweise in andere Projekte (`Misc:NOTE-003`) sind absichtlich nicht
auflösbar; sie bleiben ungeprüft erhalten.

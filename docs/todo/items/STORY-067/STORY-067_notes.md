# STORY-067 — Gemeinsame UI-Bausteine für alle Plugins

## 2026-10-16 — Entscheidungen

### Decided

- Größeres Augenmerk auf Wiederverwendbarkeit: neue Plugins stecken Bausteine zusammen, statt sie neu zu bauen.
- Behalten aus dem alten Viewer: Baum, Abhängigkeiten, Notes, Papierkorb.
## 2026-10-16 — Umsetzungsplan (Cloud-Sitzung)

### Discussed

- `shared` darf nur Pakete von Dritten importieren (Scope client §1), also weder Core-Modals noch i18n-Ressourcen des Core. `ConfirmDialog` und `ChoiceDialog` sind deshalb schlichte MUI-Dialoge mit Texten als Eigenschaften (die Plugins übersetzen), nicht Aufrufe der Core-Modals. Siehe Frage 21 in `STORY-060`. Aus demselben Grund tragen alle Bausteine ihre Texte als Eigenschaften (`labels`); Standardtexte sind englisch.
- Test-IDs: Besitzer `shared`, Form `shared.<element>`, als Konstante `sharedTestIds` aus `client/src/shared/index.ts`.
- Reine Logik (flache Liste → Baum, sichtbare Knoten, Ablageposition, Überschriften, Markdown → sauberes HTML) liegt in eigenen Dateien ohne React und hat eigene Tests.
- `marked` (^18) und `dompurify` (^3) sind im Scope freigegeben und jetzt in `client/package.json`.

### Decided

1. **Logik**: `buildTree`, `flattenVisible`, `dropPosition`, `extractHeadings`, `renderMarkdown` (sauber, mit Überschrift-IDs). Tests zuerst.
2. **TreeView** (Auswahl, Tastatur, Hover-Aktionen, Drag & Drop mit `canDrop`/`onDrop`), **ProgressRing**.
3. **DetailPanel** (Kopfleiste, einklappbare Abschnitte, Felder), **InlineField**, **EditForm** mit Versionskonflikt.
4. **MarkdownView/MarkdownEditor**, **LargeView**.
5. **FilterSection**, **ConfirmDialog/ChoiceDialog**, **EntityPicker**.
6. **Beispielseite** im Test-Plugin `example`: Baum, Detailpanel und Editor zusammen.
7. **Integration**: `check-next.sh` grün, Techdoku `neubau-client.md`.

### Open

- Frage 21 in `STORY-060`.

## 2026-10-16 — Umgesetzt und geprüft (Cloud-Sitzung)

### Discussed

- Umsetzung wie geplant; die Bausteine liegen unter `client/src/shared/`, Beschreibung in `docs/techdocs/neubau-client.md`. Die Bausteine sind neu geschrieben (nicht aus `src_old` kopiert), weil der alte Viewer ohne MUI und ohne Typen für Plugins gebaut ist; Form und Verhalten richten sich nach der Spec.
- Beim Bauen aufgefallen: `InlineField` führt den Entwurf als „Eingabe oder nichts“, damit sich der Wert nach einem erfolgreichen Speichern wieder dem gespeicherten Stand anpasst, ohne `setState` im Effekt.

### Decided

- Abschlusskriterien geprüft: (1) alle Bausteine der Spec sind über `client/src/shared/index.ts` nutzbar; (2) jeder hat Unit-Tests (`tests/implementation/unit/client/shared/`, 69 Tests) und Test-IDs `shared.<element>`; (3) die Beispielseite „Bausteine“ im Plugin `example` nutzt Baum, Detailpanel, Inline-Feld und Editor zusammen (`WorkbenchPage.test.tsx`, inkl. gemerkter geöffneter Knoten im UI-Zustand und Verschieben per Drag & Drop); (4) kein Baustein hält globalen Store-Zustand (Lint-Regel und Aufbau: `shared` importiert nur Pakete).
- `scripts/check-next.sh` und `scripts/check.sh` grün.
- Status: `Awaiting confirmation`.

### Open

- Frage 21 in `STORY-060` (Annahme gilt).

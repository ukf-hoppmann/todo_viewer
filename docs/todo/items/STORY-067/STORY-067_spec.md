# `STORY-067` — Gemeinsame UI-Bausteine

Grundlage: `EPIC-007_spec.md`, Abschnitte 1, 8, 9.

## Bausteine (fest)

| Baustein | Vertrag |
|---|---|
| `TreeView` | Knoten `{id, parentId, label, badge?, statusColor?, progress?, children}`; auf-/zuklappen (Zustand vom Aufrufer), Auswahl, Tastatur, Hover-Aktionen, Drag & Drop mit `canDrop(source, target, position)` und `onDrop` (vor, nach, hinein) |
| `ProgressRing` | erledigt/gesamt als Tortendiagramm |
| `DetailPanel` | Kopfleiste mit Aktionen (Icon-Buttons), Abschnitte einklappbar, Felder |
| `InlineField` | Text, Auswahl, Mehrfachauswahl; speichert sofort; Fehler am Feld |
| `EditForm` | Formular mit Speichern/Abbrechen und Versionskonflikt („Aktuellen Stand laden“) |
| `MarkdownView` / `MarkdownEditor` | `marked` + `dompurify`; Editor mit Vorschau daneben; Konflikt („Aktuellen Stand anzeigen“, „Trotzdem speichern“) |
| `FilterSection` | Checkbox-Liste mit Farbpunkt für die Seitenleiste |
| `ConfirmDialog`, `ChoiceDialog` | über die Modals des Core |
| `EntityPicker` | Auswahl von Elementen (Label — Titel) für Parent, Abhängigkeiten, Verknüpfungen |
| `LargeView` | fast vollbildschirmgroße Ansicht mit Inhaltsverzeichnis aus Überschriften |

Vorlagen aus `src_old/web/src/components` und `src_old/web/src/views` dürfen gelesen und
angepasst kopiert werden.

## Nicht im Umfang

Fachlogik (gehört in die Plugins), der Neu-Dialog (gehört `workspace`,
`STORY-068`).

## Tests

Unit-Tests je Baustein (Testing Library, Test-IDs nach §8).

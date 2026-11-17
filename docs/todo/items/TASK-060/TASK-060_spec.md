# TASK-060 — Spec: runde Anordnung

Regeln: `STORY-101_spec.md` (Abschnitt „Anordnung“). Nur Client. Unabhängig von `TASK-058`/`TASK-059`, ändert aber
dieselbe Seite; deshalb nach ihnen oder mit sauberem Merge vor `TASK-059`.

## Umfang

1. **Prototyp zuerst** (Skript im Scratchpad, nicht ins Repository): eine Map mit etwa 300 Knoten (breite und tiefe
   Äste gemischt, Knotengröße 190 × 36 wie in `mindmapLayout.ts`) in ELK `radial` und `mrtree`, bei Bedarf in einer
   eigenen Berechnung (Winkelsektor je Teilbaum nach Blattzahl, Radius je Ebene). Gemessen werden Überlappungen von
   Knoten und die Lesbarkeit; als Bild festgehalten, gerne mit Playwright. Das Ergebnis und die Wahl kommen in die
   Notizen der Story `STORY-101` (Eintrag mit Optionen, Vor- und Nachteilen).
2. `layoutTree(nodes, mode)` in `mindmapLayout.ts` mit `mode: "side" | "round"`; die Anordnung zur Seite bleibt
   unverändert. Die runde Anordnung setzt die Wurzel in die Mitte; Geschwister behalten ihre Reihenfolge (im Uhrzeigersinn).
3. Die Kanten und die Anschlussseiten der Knoten (`MindmapNode`) folgen dem Modus (rechts/links statt immer rechts).
4. Umschalter in einer Sektion der Seitenleiste; UI-State `layout` (`"side"` ist der Standard, Eigentümer
   `mindmap`). Die Wahl gilt für Einzel- und Gesamtansicht und für den Fokus.
5. Fit-to-view und Drag-and-drop (Zonen vor/nach/innerhalb) funktionieren in beiden Anordnungen; ist das in der runden
   Anordnung nicht eindeutig, bleibt die Zone „innerhalb“ und die Notiz sagt es.

## Schnittstellen und Dateien

`client/src/plugins/mindmap/mindmapLayout.ts`, `MindmapNode.tsx`, `pages/MindmapPage.tsx`, `state.ts`, neue oder
erweiterte Sektion der Seitenleiste, `testIds.ts`, `locales/*`. ELK kommt über `loadElk` aus `shared`; es wird keine
neue Abhängigkeit eingeführt (eine solche braucht die Freigabe des Owners, Scope `client`, Abschnitt 8).

## Tests

`mindmapLayout.test.ts`: kein Rechteck überlappt ein anderes in der runden Anordnung bei einer festen großen Map;
die Wurzel liegt in der Mitte; die Anordnung zur Seite bleibt byte-gleich zu heute. `MindmapPage.test.tsx` und Test
der Sektion: Umschalten, Wahl bleibt gespeichert. Techdocs nachziehen.

# STORY-002 — Notizen

## 2026-09-28 — Bedienkonzept

### Discussed

- Statt eines Schalters für „alle offen/alle zu“ wird der vorhandene
  Zustand der eingeklappten Items genutzt: „Alle zu“ klappt alle
  betroffenen Items zu, „Alle auf“ klappt sie auf. So bleibt das einzelne
  Auf- und Zuklappen erhalten.

### Decided

- Zwei Buttons in der Baumansicht: einer für Epics (Stories ein-/ausblenden),
  einer für Stories (Tasks ein-/ausblenden). Die Beschriftung zeigt die
  jeweils nächste Aktion.
- Projekte lassen sich in der Seitenleiste zusätzlich markieren: Ein Klick
  auf den Namen (nicht die Checkbox) markiert, ein weiterer hebt die
  Markierung auf. Mehrere Projekte können markiert sein.
- Die Buttons wirken auf die markierten Projekte, ohne Markierung auf alle.
- „Alle zu“ betrifft auch ausgefilterte Items; werden sie wieder
  eingeblendet, sind sie zu.
- Die Markierung wird wie die Filter gespeichert und übersteht einen
  Neustart.
- Items, die nach dem Klick neu ins Backlog kommen, erscheinen offen.

## 2026-09-28 — Umsetzung

### Decided

- Umgesetzt wie oben beschrieben; die Markierung liegt als
  `markedProjects` im gespeicherten UI-Zustand.

# TASK-058 — Mindmap: Fokus auf einen Knoten und die Aktionen „Gehe hin“, „Erstelle“, „Anker“ am Item

## State

- Goal/Status: Spec steht; bereit zur Umsetzung in eigener Session.
- Next step: Plan aus der Spec erstellen, dem Owner vorlegen und umsetzen (Sections: Domain, Seite mit Pfad, Item-Aktionen, Integration, Doku).
- Open:
- Decided:
  - Der Fokus steht als `?focus=<uid>` in der Adresse; die Routen kennen sonst keine Parameter (2026-11-17)
  - „Gehe hin“ blendet ein ausgeblendetes Projekt des Items ein und markiert es (2026-11-17)
  - Schalter und Aktionen folgen `STORY-101_spec.md` (2026-11-17)
- References: Spec `TASK-058_spec.md`; Story-Spec `STORY-101_spec.md`; Notizen `STORY-101`

State confirmed after entry 2026-11-17 — Anlage aus der Planung der Story (3cc92bd28ff6)

## 2026-11-17 — Anlage aus der Planung der Story

### Discussed

- Planung der Story `STORY-101` mit dem Owner; Aufbau und Aufteilung stehen in deren Notizen.
- Ein Fokus in der Adresse braucht einen Query-Parameter, weil die Routen `<owner>/<name>` keine Pfadparameter haben.

### Decided

- Fokus als Query-Parameter `focus`
- „Gehe hin“ blendet ein ausgeblendetes Projekt ein und markiert es (Owner, 2026-11-17)

### Open

- Nichts offen.

# TASK-058 — Mindmap: Fokus auf einen Knoten und die Aktionen „Gehe hin“, „Erstelle“, „Anker“ am Item

## State

- Goal/Status: In Arbeit auf Branch `claude/task-058-mindmap-fokus`; Plan dem Owner vorgelegt, Freigabe steht aus (2026-11-17).
- Next step: Freigabe des Plans abwarten, dann umsetzen (Sections: Domain, Navigationsbaustein, Seite mit Pfad, Item-Aktionen, Doku, Integration).
- Open:
- Decided:
  - Der Fokus steht als `?focus=<uid>` in der Adresse; die Routen kennen sonst keine Parameter (2026-11-17)
  - „Gehe hin“ blendet ein ausgeblendetes Projekt des Items ein und markiert es (2026-11-17)
  - Schalter und Aktionen folgen `STORY-101_spec.md` (2026-11-17)
  - Der Fokusknoten verhält sich wie jeder andere Knoten (Umbenennen, Detail, Anlegen, Papierkorb); nur die Tiefe zählt ab ihm; wird er gelöscht, gilt die Projektwurzel (2026-11-17)
  - „Anker“ blendet ein ausgeblendetes Projekt des Items ebenfalls ein und markiert es, wie „Gehe hin“ (2026-11-17)
- References: Spec `TASK-058_spec.md`; Story-Spec `STORY-101_spec.md`; Notizen `STORY-101`

State confirmed after entry 2026-11-17 — Plan und Klärung offener Punkte (9324b8ce4b22)

## 2026-11-17 — Anlage aus der Planung der Story

### Discussed

- Planung der Story `STORY-101` mit dem Owner; Aufbau und Aufteilung stehen in deren Notizen.
- Ein Fokus in der Adresse braucht einen Query-Parameter, weil die Routen `<owner>/<name>` keine Pfadparameter haben.

### Decided

- Fokus als Query-Parameter `focus`
- „Gehe hin“ blendet ein ausgeblendetes Projekt ein und markiert es (Owner, 2026-11-17)

### Open

- Nichts offen.

## 2026-11-17 — Plan und Klärung offener Punkte

### Discussed

- Plan mit sechs Sections vorgelegt: Domain (Test zuerst), Navigationsbaustein, Seite mit Pfad, Item-Aktionen, Techdocs, Integration.
- Fokusknoten: wie jeder andere Knoten (empfohlen; wenig Sonderfälle) oder wurzelartig ohne Papierkorb und Detail.
- „Anker“ bei ausgeblendetem Projekt: einblenden und markieren (empfohlen, sonst Fokus ohne gezeigtes Projekt) oder nur navigieren.

### Decided

- Fokusknoten wie jeder andere Knoten (Owner)
- „Anker“ blendet das Projekt ein und markiert es, wie „Gehe hin“ (Owner)

### Open

- Freigabe des Plans durch den Owner

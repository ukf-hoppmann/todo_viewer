# STORY-094 — Notiz- und Spec-Dokumente löschen: Lösch-Befehl in API und MCP

## State

Lösch-Befehl für Notiz- und Spec-Dokumente über API, MCP und Harness-Helfer; Spec STORY-094_spec.md liegt vor. Entschieden: Löschen geht in den Papierkorb (wiederherstellbar); mit der Notiz entfallen Kopf und Kurzfassung (beim Wiederherstellen kommen sie zurück); Haupt- und Themen-Specs werden gleich und ohne Folgen gelöscht. Offen: Darstellung im Spiegel (Empfehlung: Datei entfernen, Architekturregel erweitern), Anzeige im zentralen Papierkorb (Empfehlung) und Wiederherstellen bei Namenskonflikt. Noch kein Code.

State confirmed after entry 2026-10-22 — Spec angelegt; offene Entwurfsfragen (b63ba0907d9c)

## 2026-10-22 — Löschverhalten von Notiz- und Spec-Dokumenten

### Discussed

- Anlass: Eine Notiz wurde beim falschen Item eingetragen und konnte nicht gelöscht werden; sie liegt jetzt geleert vor.
- Papierkorb mit Wiederherstellen (wie bei Items) oder sofortiges endgültiges Löschen. Empfehlung: Papierkorb, passt zum bisherigen Verhalten bei Items.
- Was beim Löschen der Notiz mit dem Kopf (## State) passiert.

### Decided

- Gelöschte Dokumente kommen in den Papierkorb und lassen sich wiederherstellen.
- Im Vordergrund steht das Löschen der ganzen Notiz eines Items. Mit ihr verschwinden der Kopf und die Kurzfassung (Summary) des Items.

### Open

- Ob Themen-Specs (<ID>_spec_<thema>.md) genauso behandelt werden wie die Haupt-Spec; Erklärung an den Owner gegeben, Antwort steht aus.

## 2026-10-22 — Themen-Specs

### Discussed

- Ein Item hat höchstens ein Notizdokument, aber mehrere Specs: die Haupt-Spec <ID>_spec.md und Themen-Specs <ID>_spec_<thema>.md.
- Empfehlung: Themen-Specs genauso behandeln wie die Haupt-Spec. An einer Spec hängen weder Kopf noch Kurzfassung.

### Decided

- Jedes Spec-Dokument (Haupt- oder Themen-Spec) lässt sich einzeln über seinen Namen löschen und kommt in den Papierkorb. Weitere Folgen hat das Löschen einer Spec nicht.

## 2026-10-22 — Spec angelegt; offene Entwurfsfragen

### Discussed

- Befund im Code: Der Papierkorb (Workspace-Plugin) kennt nur Elemente mit uid; Dokumente (backlog_documents, Notizen in eigener Tabelle) sind keine Elemente und werden heute hart gelöscht (nur der Sync löscht sie, wenn die Datei fehlt).
- Spiegel: Items im Papierkorb bleiben in den Dateien mit einem Löschdatum. Für Dokumente gibt es keine solche Form. Eine Löschung in der Datenbank ist im Sync ein Konflikt (Architektur §2), außer beim endgültigen Löschen.
- Spiegel-Optionen: (a) Datei beim Verschieben in den Papierkorb entfernen, konfliktfrei wenn unverändert – erweitert die Architekturregel zum gewollten Löschen auf den Papierkorb, braucht Owner-Freigabe; (b) Datei bleibt, wird als gelöscht markiert oder in einen Papierkorb-Ordner verschoben – Formatänderung (Format v2, Golden Files). Empfehlung: (a).
- Oberfläche: gelöschte Dokumente als eigene Einträge im zentralen Papierkorb (z. B. 'Notiz zu STORY-012') – braucht eine Erweiterung des Workspace-Papierkorbs für Einträge, die Plugins beisteuern; Alternative: Papierkorb je Item in der Detailansicht. Empfehlung: zentraler Papierkorb.
- Wiederherstellen: Empfehlung – abweisen mit document_exists, wenn inzwischen ein gleichnamiges Dokument existiert; abweisen, solange das Item selbst im Papierkorb liegt.

### Decided

- Spec STORY-094_spec.md mit dem entschiedenen Verhalten angelegt; Kurzfassung kommt beim Wiederherstellen der Notiz mit zurück.

### Open

- Spiegel-Darstellung eines Dokuments im Papierkorb: (a) Datei entfernen oder (b) Formatänderung.
- Anzeige im zentralen Papierkorb oder je Item.
- Wiederherstellen bei Namenskonflikt bzw. Item im Papierkorb abweisen?

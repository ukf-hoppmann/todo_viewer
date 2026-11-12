"""Schreibt die alte Datenbank in die neue, in der Transaktion des Aufrufers (SQL auf den Tabellen der Plugins)."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date
from typing import Any

import sqlalchemy as sa

from viewer.app.import_legacy.mapping import (
    ITEM_KINDS,
    counters,
    document_kind,
    extra_fields_lines,
    map_priority,
    stable_uid,
)
from viewer.app.import_legacy.reader import Legacy, Row
from viewer.app.import_legacy.report import Report
from viewer.app.import_legacy.validate import project_name
from viewer.core.infrastructure.database import SqlTransaction
from viewer.plugins.backlog.domain.documents import NotesEntry, append_entry
from viewer.plugins.backlog.domain.notes import split_lossless
from viewer.plugins.workspace.domain.model import BUILTIN_PROJECT

EXTRA_TOPIC = "Übernommene Zusatzfelder"
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _bool(value: object) -> int | None:
    return None if value is None else int(bool(value))


def _memo_label(label: str) -> str:
    """Der alte Viewer nannte Memos Notes (`NOTE-001`); im Neubau heißen sie `MEMO-001`."""
    return "MEMO-" + label[5:] if label.startswith("NOTE-") else label


def _hint_kind(cause: str) -> str:
    return {"note_dropped": "memo_dropped", "note_promoted": "memo_promoted"}.get(cause, cause)


class Importer:
    def __init__(self, legacy: Legacy, tx: SqlTransaction, report: Report, now: str) -> None:
        self._legacy = legacy
        self._c = tx.connection
        self._report = report
        self._now = now
        #: Altes Projekt (`id`) → neue `uid`.
        self._project: dict[str, str] = {}
        #: (neues Projekt, Label) → `uid` des Elements; je Projekt die vergebenen Labels.
        self._element: dict[tuple[str, str], str] = {}
        self._labels: dict[str, list[str]] = {}
        self._item_uids: set[str] = set()
        self._note_uids: dict[str, Row] = {}
        self._link_uids: dict[tuple[str, str, str], str] = {}

    def run(self) -> None:
        self._c.exec_driver_sql("PRAGMA defer_foreign_keys = ON")
        self._projects()
        self._backlog()
        self._notes()
        self._links_triggers_alarms()
        self._notices()
        self._counters()

    # --- Hilfen ---------------------------------------------------------------------------------------------------

    def _exec(self, sql: str, **params: Any) -> None:
        self._c.execute(sa.text(sql), params)

    def _day(self, value: object) -> str:
        text = str(value or "")
        return f"{text}T00:00:00+00:00" if _DATE.match(text) else (text or self._now)

    def _element_row(
        self, uid: str, project: str, kind: str, label: str, title: str, created: str, deleted: Any
    ) -> None:
        label = _memo_label(label)
        self._exec(
            "INSERT INTO workspace_elements(uid, project_uid, kind, label, revision, created_at, updated_at, "
            "deleted_at, title) VALUES (:uid, :project, :kind, :label, 1, :created, :created, :deleted, :title)",
            uid=uid,
            project=project,
            kind=kind,
            label=label,
            created=created,
            deleted=deleted,
            title=title,
        )
        self._exec(
            "INSERT INTO workspace_label_history(project_uid, label, element_uid) VALUES (:p, :l, :u)",
            p=project,
            l=label,
            u=uid,
        )
        self._element[(project, label)] = uid
        self._labels.setdefault(project, []).append(label)

    def _lookup(self, project_id: object, label: object) -> str | None:
        project = self._project.get(str(project_id))
        return self._element.get((project, _memo_label(str(label)))) if project else None

    # --- Projekte -------------------------------------------------------------------------------------------------

    def _projects(self) -> None:
        builtin = self._c.execute(
            sa.text("SELECT uid FROM workspace_projects WHERE name = :n"), {"n": BUILTIN_PROJECT}
        ).scalar_one()
        position = 0
        for row in self._legacy.projects:
            name = project_name(row)
            if not row.get("name"):
                self._report.deviation(f"Projekt '{row['id']}' hat keinen Namen: der Name ist die Kennung")
            if name == BUILTIN_PROJECT:
                self._project[str(row["id"])] = builtin
                self._report.deviation(f"Projekt '{name}' wird das eingebaute Projekt")
                continue
            position += 1
            folder = row.get("sync_path") or None
            self._exec(
                "INSERT INTO workspace_projects(uid, name, mirror_folder, mirror_enabled, auto_sync, sync_direction, "
                "position, revision, created_at) VALUES (:uid, :name, :folder, :enabled, :auto, 'both', :position, 1, "
                ":now)",
                uid=str(row["id"]),
                name=name,
                folder=folder,
                enabled=int(bool(folder) and not row.get("mirror_disabled")),
                auto=int(bool(row.get("auto_sync"))),
                position=position,
                now=self._now,
            )
            self._project[str(row["id"])] = str(row["id"])
            self._report.count("Projekte")

    # --- Backlog --------------------------------------------------------------------------------------------------

    def _backlog(self) -> None:
        legacy = self._legacy
        areas: dict[tuple[str, str], str] = {}
        for item in legacy.items:
            project = self._project[str(item["project_id"])]
            area = str(item["area"] or "").strip()
            if area and (project, area) not in areas:
                areas[(project, area)] = stable_uid("area", project, area)
                self._exec(
                    "INSERT INTO backlog_areas(uid, project_uid, name) VALUES (:u, :p, :n)",
                    u=areas[(project, area)],
                    p=project,
                    n=area,
                )
                self._report.count("Bereiche")
        self._item_uids = {str(item["uid"]) for item in legacy.items}
        for item in legacy.items:
            self._item(item, areas)
        self._dependencies()
        self._item_documents()

    def _item(self, item: Row, areas: Mapping[tuple[str, str], str]) -> None:
        project = self._project[str(item["project_id"])]
        kind = ITEM_KINDS[str(item["item_type"])]
        label = str(item["label"])
        if not label.startswith(kind.upper() + "-"):
            self._report.deviation(f"{label} ist ein {item['item_type']}, das Label hat einen anderen Präfix")
        created = self._day(item["created"])
        self._element_row(str(item["uid"]), project, kind, label, str(item["title"]), created, item["deleted"])
        parent = item["parent_uid"] if item["parent_uid"] in self._item_uids else None
        if item["parent_uid"] and parent is None:
            self._report.deviation(f"{label}: der Parent {item['parent_uid']} fehlt, das Item bekommt keinen")
        priority = map_priority(item["priority"])
        if priority != (item["priority"] or ""):
            self._report.deviation(f"{label}: Priorität '{item['priority'] or ''}' → {priority}")
        self._exec(
            "INSERT INTO backlog_items(uid, type, title, status, priority, area_uid, parent_uid, required_for_parent, "
            "goal, completion_criteria, summary, resolution, created, position) VALUES (:uid, :type, :title, :status, "
            ":priority, :area, :parent, :required, :goal, :criteria, :summary, :resolution, :created, :position)",
            uid=item["uid"],
            type=item["item_type"],
            title=item["title"],
            status=item["status"],
            priority=priority,
            area=areas.get((project, str(item["area"] or "").strip())),
            parent=parent,
            required=_bool(item["required_for_parent"]),
            goal=item["goal"],
            criteria=item["completion_criteria"],
            summary=item["summary"],
            resolution=item["resolution"],
            created=str(item["created"] or self._now[:10]),
            position=item["position"] or 0,
        )
        self._report.count(f"Items {item['item_type']}")

    def _dependencies(self) -> None:
        seen: set[tuple[str, str]] = set()
        for row in self._legacy.dependencies:
            pair = (str(row["item_uid"]), str(row["depends_on_uid"]))
            if pair[0] not in self._item_uids or pair[1] not in self._item_uids or pair[0] == pair[1]:
                self._report.deviation(f"Abhängigkeit {pair[0]} → {pair[1]} hat kein gültiges Ziel und entfällt")
                continue
            if pair in seen:
                continue
            seen.add(pair)
            self._exec(
                "INSERT INTO backlog_dependencies(item_uid, depends_on_uid) VALUES (:a, :b)", a=pair[0], b=pair[1]
            )
            self._report.count("Abhängigkeiten")

    def _item_documents(self) -> None:
        legacy = self._legacy
        labels = {str(i["uid"]): str(i["label"]) for i in legacy.items}
        titles = {str(i["uid"]): str(i["title"]) for i in legacy.items}
        listed = {(str(r["item_uid"]), str(r["name"])): str(r["kind"]) for r in legacy.document_names}
        contents: dict[tuple[str, str], str] = {}
        for row in legacy.documents:
            uid, name = str(row["item_uid"]), str(row["name"])
            if uid not in labels:
                self._report.deviation(f"Dokument {name}: das Item {uid} gibt es nicht, es entfällt")
                continue
            contents[(uid, name)] = str(row["content"] or "")
            if (uid, name) not in listed:
                self._report.deviation(f"Dokument {name} von {labels[uid]} steht nicht in der Namensliste")
        for key in sorted(set(listed) - set(contents)):
            self._report.deviation(
                f"Dokument {key[1]} von {labels.get(key[0], key[0])} ist gelistet, hat aber keinen Inhalt"
            )
        extras: dict[str, list[tuple[str, str]]] = {}
        for row in legacy.extra_fields:
            if str(row["item_uid"]) in labels:
                extras.setdefault(str(row["item_uid"]), []).append((str(row["key"]), str(row["value"] or "")))
        today = date.fromisoformat(self._now[:10])
        for uid, fields in extras.items():
            name = f"{labels[uid]}_notes.md"
            entry = NotesEntry.create(today, EXTRA_TOPIC, extra_fields_lines(fields), [], [])
            header = f"# {labels[uid]} — {titles[uid]}\n"
            contents[(uid, name)] = append_entry(contents.get((uid, name), header), entry)
            self._report.count("Einträge „Übernommene Zusatzfelder“")
            self._report.count("Zusatzfelder", len(fields))
        for (uid, name), content in sorted(contents.items()):
            if document_kind(labels[uid], name, listed.get((uid, name))) == "notes":
                self._item_notes(uid, name, content)
            else:
                self._exec(
                    "INSERT INTO backlog_documents(item_uid, name, kind, content, revision, updated_at) "
                    "VALUES (:u, :n, 'spec', :c, 1, :now)",
                    u=uid,
                    n=name,
                    c=content,
                    now=self._now,
                )
            self._report.count("Dokumente der Items")

    def _item_notes(self, uid: str, name: str, content: str) -> None:
        """Notes eines Items zerlegt in Vorspann, Kopf mit Stempel und Protokolleinträge (ohne Textverlust)."""
        parts = split_lossless(content)
        stamp = parts.stamp
        self._exec(
            "INSERT INTO backlog_notes(item_uid, name, preamble, state, stamp_day, stamp_topic, stamp_checksum, "
            "state_revision, revision, updated_at) VALUES (:u, :n, :p, :s, :sd, :st, :sc, 1, 1, :now)",
            u=uid,
            n=name,
            p=parts.preamble,
            s=parts.state,
            sd=stamp.day if stamp else None,
            st=stamp.topic if stamp else None,
            sc=stamp.checksum if stamp else None,
            now=self._now,
        )
        for position, entry in enumerate(parts.entries):
            self._exec(
                "INSERT INTO backlog_notes_entries(item_uid, position, day, topic, body) VALUES (:u, :i, :d, :o, :b)",
                u=uid,
                i=position,
                d=entry.day,
                o=entry.topic,
                b=entry.body,
            )

    # --- Memos ----------------------------------------------------------------------------------------------------

    def _notes(self) -> None:
        legacy = self._legacy
        topic_uids = {str(t["uid"]) for t in legacy.topics}
        for topic in legacy.topics:
            project = self._project[str(topic["project_id"])]
            self._element_row(
                str(topic["uid"]),
                project,
                "topic",
                str(topic["label"]),
                str(topic["name"]),
                self._day(topic["created"]),
                topic["deleted"],
            )
            parent = topic["parent_uid"] if topic["parent_uid"] in topic_uids else None
            if topic["parent_uid"] and parent is None:
                self._report.deviation(f"{topic['label']}: das Parent-Topic fehlt, das Topic wird eine Wurzel")
            self._exec(
                "INSERT INTO memos_topics(uid, name, parent_uid, due_at, archived_at, system) VALUES (:u, :n, :p, :d, "
                "NULL, 0)",
                u=topic["uid"],
                n=topic["name"],
                p=parent,
                d=topic["due_at"],
            )
            self._report.count("Topics")
        for note in legacy.notes:
            project = self._project[str(note["project_id"])]
            self._note_uids[str(note["uid"])] = note
            self._element_row(
                str(note["uid"]),
                project,
                "memo",
                str(note["label"]),
                str(note["summary"]),
                self._day(note["created"]),
                note["deleted"],
            )
            note_topic = note["topic_uid"] if note["topic_uid"] in topic_uids else None
            if note["topic_uid"] and note_topic is None:
                self._report.deviation(f"{note['label']}: das Topic fehlt, das Memo liegt ohne Topic")
            status = "waiting" if note["status"] == "due" else note["status"]
            self._exec(
                "INSERT INTO memos_memos(uid, summary, body, status, topic_uid, review_at, trigger_mode, archived) "
                "VALUES (:u, :s, :b, :st, :t, :r, :m, :a)",
                u=note["uid"],
                s=note["summary"],
                b=note["body"],
                st=status,
                t=note_topic,
                r=note["review_at"],
                m=note["trigger_mode"],
                a=int(bool(note["archived"])),
            )
            self._report.count("Memos")
        for row in legacy.note_documents:
            uid = str(row["note_uid"])
            if uid not in self._note_uids:
                self._report.deviation(f"Dokument {row['name']}: das Memo {uid} gibt es nicht, es entfällt")
                continue
            self._exec(
                "INSERT INTO memos_documents(memo_uid, name, content, revision, updated_at) VALUES (:u, :n, :c, 1, :t)",
                u=uid,
                n=str(row["name"]).replace("NOTE-", "MEMO-"),
                c=row["content"] or "",
                t=str(self._note_uids[uid]["updated"] or self._now),
            )
            self._report.count("Dokumente der Memos")

    # --- Verknüpfungen, Auslöser, Wecker --------------------------------------------------------------------------

    def _links_triggers_alarms(self) -> None:
        legacy = self._legacy
        links: dict[int, tuple[str, str]] = {}
        for link in legacy.links:
            source = str(link["note_uid"])
            target = self._lookup(link["target_project"], link["target_label"])
            if source not in self._note_uids or target is None:
                self._report.deviation(
                    f"Verknüpfung {link['id']} → {link['target_project']}:{link['target_label']} hat kein Ziel und "
                    "entfällt"
                )
                continue
            key = (source, target, str(link["role"]))
            if key in self._link_uids:
                self._report.deviation(f"Verknüpfung {link['id']} gibt es schon (gleiches Memo, Ziel und Rolle)")
                links[int(link["id"])] = (self._link_uids[key], target)
                continue
            uid = stable_uid("link", link["id"])
            self._link_uids[key] = uid
            links[int(link["id"])] = (uid, target)
            self._exec(
                "INSERT INTO workspace_links(uid, from_uid, to_uid, role, created_at) VALUES (:u, :f, :t, :r, :now)",
                u=uid,
                f=source,
                t=target,
                r=link["role"],
                now=self._now,
            )
            self._report.count("Verknüpfungen")
        for trigger in legacy.triggers:
            self._trigger(trigger, links)

    def _trigger(self, trigger: Row, links: Mapping[int, tuple[str, str]]) -> None:
        note = self._note_uids.get(str(trigger["note_uid"]))
        if note is None:
            self._report.deviation(f"Auslöser {trigger['id']}: das Memo fehlt, er entfällt")
            return
        uid = stable_uid("trigger", trigger["id"])
        kind = str(trigger["kind"])
        if kind == "time":
            self._alarm(trigger, note)
            return
        target: str | None = None
        link_uid: str | None = None
        if kind == "event":
            found = links.get(int(trigger["link_id"])) if trigger["link_id"] is not None else None
            if found is None:
                self._report.deviation(f"Auslöser {trigger['id']} von {note['label']} hat kein Ziel und entfällt")
                return
            link_uid, target = found
        self._exec(
            "INSERT INTO memos_triggers(uid, memo_uid, kind, target_uid, status, fired_at, already_met, link_uid) "
            "VALUES (:u, :n, :k, :t, :s, :f, :a, :l)",
            u=uid,
            n=note["uid"],
            k="event" if kind == "event" else "topic_date",
            t=target,
            s=trigger["target_status"] if kind == "event" else None,
            f=trigger["fired_at"],
            a=int(bool(trigger["already_met"])),
            l=link_uid,
        )
        self._report.count("Auslöser " + ("Ereignis" if kind == "event" else "Topic-Termin"))

    def _alarm(self, trigger: Row, note: Row) -> None:
        project = self._project[str(note["project_id"])]
        uid = stable_uid("alarm", trigger["id"])
        number = max(
            (int(label[6:]) for label in self._labels.get(project, []) if label.startswith("ALARM-")), default=0
        )
        text = str(note["summary"] or f"Wecker aus Memo {_memo_label(str(note['label']))}")
        self._element_row(uid, project, "alarm", f"ALARM-{number + 1:03d}", text, self._now, None)
        self._exec(
            "INSERT INTO alarms_alarms(uid, at, text, target_text, status, snoozed_until, done_at) VALUES (:u, :at, "
            ":t, NULL, :status, NULL, NULL)",
            u=uid,
            at=trigger["at"] or self._now,
            t=text,
            status="Due" if trigger["fired_at"] else "Pending",
        )
        self._exec(
            "INSERT INTO alarms_targets(alarm_uid, position, element_uid) VALUES (:u, 0, :target)",
            u=uid,
            target=note["uid"],
        )
        self._report.count("Wecker aus Zeit-Auslösern")

    # --- Hinweise und Zähler --------------------------------------------------------------------------------------

    def _notices(self) -> None:
        for notice in self._legacy.notices:
            if notice["cause"] == "project_unreachable":
                self._report.deviation(f"Hinweis {notice['id']} (Projekt nicht erreichbar) entfällt")
                continue
            subject = self._lookup(notice["project_id"], notice["label"])
            source = self._lookup(notice["counterpart_project"], notice["counterpart_label"])
            if subject is None or source is None:
                self._report.deviation(f"Hinweis {notice['id']} hat kein Ziel und entfällt")
                continue
            self._exec(
                "INSERT INTO memos_hints(uid, side, subject_uid, source_uid, kind, created_at, decided_at, decision) "
                "VALUES (:u, :side, :subject, :source, :kind, :created, :decided, :decision)",
                u=stable_uid("notice", notice["id"]),
                side="memo" if notice["side"] == "note" else notice["side"],
                subject=subject,
                source=source,
                kind=_hint_kind(str(notice["cause"])),
                created=notice["created_at"] or self._now,
                decided=notice["decided_at"],
                decision=notice["decision"],
            )
            self._report.count("Hinweise")

    def _counters(self) -> None:
        legacy_prefix = {"note": "MEMO", "topic": "TOPIC"}
        for project in sorted(set(self._project.values())):
            highest = counters(self._labels.get(project, []))
            for row in self._legacy.counters:
                prefix = legacy_prefix.get(str(row["kind"]))
                if prefix is None:
                    self._report.deviation(f"Zähler '{row['kind']}' von '{row['project_id']}' ist unbekannt")
                elif self._project.get(str(row["project_id"])) == project:
                    highest[prefix] = max(highest.get(prefix, 0), int(row["last"] or 0))
            for prefix, last in sorted(highest.items()):
                self._exec(
                    "INSERT INTO workspace_label_counters(project_uid, prefix, last) VALUES (:p, :x, :l) "
                    "ON CONFLICT(project_uid, prefix) DO UPDATE SET last = excluded.last",
                    p=project,
                    x=prefix,
                    l=last,
                )

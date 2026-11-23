"""Ein Memo zum Item befördern und ein offenes Item zum Memo zurückstufen.

Memo und Item liegen in verschiedenen Plugins und ihre Dienste teilen keine Transaktion. Darum wird zuerst die neue
Seite angelegt und gleich die Verknüpfung `origin` dazu geschrieben: sie belegt, dass der erste Schritt lief. Jeder
spätere Schritt prüft, was schon da ist, so dass ein abgebrochener Aufruf beim Wiederholen zu Ende geführt wird und nie
ein zweites Item oder eine zweite Memo entsteht.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from viewer.core.application.ports import Transaction
from viewer.core.domain.errors import NotFound, VersionConflict
from viewer.core.domain.events import Event
from viewer.plugins.memos.application.common import ELEMENT_TOPIC, MEMO_TOPIC
from viewer.plugins.memos.application.deps import ITEM_KINDS, Deps
from viewer.plugins.memos.application.memos import MemoService
from viewer.plugins.memos.application.ports import Document, ItemInfo
from viewer.plugins.memos.domain import lifecycle
from viewer.plugins.memos.domain.documents import NOTES, SPEC, NotesEntry, document_kind
from viewer.plugins.memos.domain.model import Memo, MemosViolation

DEMOTE_RESOLUTION = "zur Notiz zurückgestuft"


def promotion_marker(label: str) -> str:
    """Die Wörter in der Überschrift des Notiz-Eintrags, an denen man sieht, dass der Langtext übernommen wurde."""
    return f"Aus Memo {label} befördert"


def promotion_entry(day: date, label: str, body: str | None) -> NotesEntry:
    """Der Langtext einer beförderten Memo als erster datierter Eintrag der Notizen des Items, eine Zeile je Punkt."""
    lines = [line for line in (body or "").splitlines() if line.strip()]
    return NotesEntry.create(day, promotion_marker(label), lines or [f"Memo {label} ohne Langtext."], [], [])


def without_header(text: str) -> str:
    """Eine Notizen-Datei ohne ihre Überschrift `# <ID> — <Titel>`, damit ihre Einträge in eine andere passen."""
    lines = text.lstrip("\n").splitlines(keepends=True)
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "".join(lines).strip("\n")


def renamed_document(name: str, old_label: str, new_label: str) -> str | None:
    """`<ALT>_notes.md` und `<ALT>_spec[_thema].md` unter dem Label der anderen Seite; sonst `None`."""
    if re.fullmatch(rf"{re.escape(old_label)}_(notes|spec(_[A-Za-z0-9-]+)?)\.md", name) is None:
        return None
    return new_label + name[len(old_label) :]


def promotion_fields(summary: str, given: Mapping[str, Any]) -> dict[str, object]:
    """Felder des neuen Items: Titel und Kurzfassung kommen aus der Kurzfassung des Memos, wenn nichts gegeben ist."""
    fields: dict[str, object] = {"title": summary, "summary": summary}
    fields.update({name: value for name, value in given.items() if value is not None})
    return fields


@dataclass(frozen=True)
class Promoted:
    memo_uid: str
    item_uid: str


@dataclass(frozen=True)
class Demoted:
    memo_uid: str
    item_uid: str


def check_demote(info: ItemInfo) -> None:
    """Ein Item wird nur zum Memo, solange es `Open` ist, ohne Kinder und wenn kein Item von ihm abhängt."""
    if info.deleted:
        raise MemosViolation("item_deleted", f"{info.label} liegt im Papierkorb", item=info.label)
    if info.status != "Open":
        raise MemosViolation("demote_not_open", f"{info.label} ist nicht Open", item=info.label)
    if info.children:
        raise MemosViolation("demote_has_children", f"{info.label} hat Kinder", item=info.label)
    if info.dependents:
        raise MemosViolation("demote_referenced", f"Andere Items hängen von {info.label} ab", item=info.label)


class ConversionService:
    def __init__(self, deps: Deps, memos: MemoService) -> None:
        self._d = deps
        self._memos = memos

    # --- Memo → Item -----------------------------------------------------------------------------------------------

    def promote(
        self, ref: str, project_uid: str | None, version: int, item_type: str, given: Mapping[str, Any]
    ) -> Promoted:
        """Legt das Item im Projekt des Memos an, übernimmt Langtext, Notizen und Specs und schließt das Memo als
        `promoted`. `given` sind die Felder des Items (`goal`, `completion_criteria`, optional `area`, …)."""
        d = self._d
        with d.database.transaction() as tx:
            memo = d.resolver.memo(tx, ref, project_uid)
            lifecycle.check_open(memo)
            if memo.revision != version:
                raise VersionConflict("Das Memo wurde inzwischen geändert", details={"uid": memo.uid})
            item_uid = self._origin_of(tx, memo)
        if item_uid is None:
            item_uid = d.gateway.create_item(memo.project_uid, item_type, promotion_fields(memo.summary, given))
            with d.database.transaction() as tx:
                link = d.links.add(tx, memo.uid, item_uid, "origin")
            d.links.announce("added", link)
        else:
            info = d.gateway.get_item(item_uid)
            if info is None or info.deleted:
                raise MemosViolation("promote_origin_missing", "Das Item der Beförderung gibt es nicht mehr")
        self._take_over(item_uid, memo)
        self._memos.finish(memo.uid, None, version, "promoted")
        return Promoted(memo.uid, item_uid)

    def _origin_of(self, tx: Transaction, memo: Memo) -> str | None:
        link = next(
            (
                v
                for v in self._d.links.outgoing(tx, memo.uid)
                if v.link.role == "origin" and v.element.kind in ITEM_KINDS
            ),
            None,
        )
        return None if link is None else str(link.element.uid)

    def _take_over(self, item_uid: str, memo: Memo) -> None:
        """Langtext und Notizen des Memos werden ein Eintrag in den Notizen des Items, Specs behalten ihren Namen mit
        dem Label des Items. Was das Item schon hat, bleibt unberührt."""
        d = self._d
        info = d.gateway.get_item(item_uid)
        assert info is not None
        with d.database.transaction() as tx:
            documents = d.documents.list_for(tx, memo.uid)
        name = next((n for n in info.documents if document_kind(info.label, n) == NOTES), f"{info.label}_notes.md")
        current = d.gateway.read_document(item_uid, name)
        marker = promotion_marker(memo.label)
        if current is None or marker not in current.content:
            entry = promotion_entry(d.clock.now().date(), memo.label, memo.body).render()
            for document in documents:
                if document.kind == NOTES:
                    entry += "\n" + without_header(document.content) + "\n"
            if current is not None:
                content, version = f"{current.content.rstrip()}\n\n{entry}", current.revision
            else:
                content, version = f"# {info.label} — {info.title}\n\n{entry}", None
            d.gateway.write_document(item_uid, name, content, version, info.summary or memo.summary)
        for document in documents:
            target = renamed_document(document.name, memo.label, info.label)
            if document.kind == SPEC and target is not None and target not in info.documents:
                d.gateway.write_document(item_uid, target, document.content, None, None)

    # --- Item → Memo -----------------------------------------------------------------------------------------------

    def demote(self, ref: str, project_uid: str | None, version: int, topic: str | None) -> Demoted:
        """Legt aus einem offenen Item ein Memo an, übernimmt Notizen und Specs und setzt das Item auf `Rejected`."""
        d = self._d
        with d.database.transaction() as tx:
            element = d.registry.get(tx, ref) or (
                d.registry.find_by_label(tx, project_uid, ref) if project_uid else None
            )
        if element is None or element.kind not in ITEM_KINDS:
            raise NotFound(f"Item {ref} gibt es nicht", details={"ref": ref})
        info = d.gateway.get_item(element.uid)
        if info is None:
            raise NotFound(f"Item {ref} gibt es nicht", details={"ref": ref})
        if info.revision != version:
            raise VersionConflict("Das Item wurde inzwischen geändert", details={"uid": info.uid})
        check_demote(info)
        unnamed = [name for name in info.documents if renamed_document(name, info.label, "X") is None]
        if unnamed:
            raise MemosViolation(
                "demote_document_name", "Dokumente mit fremden Namen lassen sich nicht übernehmen", names=unnamed
            )
        memo_uid = self._open_memo_from(info)
        if memo_uid is None:
            memo_uid = self._memos.create(
                info.project_uid, {"summary": info.title, "body": info.summary, "topic": topic}
            )
            with d.database.transaction() as tx:
                link = d.links.add(tx, memo_uid, info.uid, "origin")
            d.links.announce("added", link)
        self._take_over_into_memo(info, memo_uid)
        d.gateway.reject_item(info.uid, info.revision, DEMOTE_RESOLUTION)
        d.events.publish(Event(MEMO_TOPIC, {"uid": memo_uid, "change": "created"}, public=True))
        d.events.publish(Event(ELEMENT_TOPIC, {"change": "updated", "uids": [info.uid, memo_uid]}, public=True))
        return Demoted(memo_uid, info.uid)

    def _open_memo_from(self, info: ItemInfo) -> str | None:
        """Das Memo, die eine frühere, unfertige Rückstufung dieses Items angelegt hat. Eine abgeschlossene Memo ist
        aus dem Item befördert worden und zählt nicht."""
        d = self._d
        with d.database.transaction() as tx:
            for view in d.links.incoming(tx, info.uid):
                if view.link.role != "origin" or view.element.kind != "memo":
                    continue
                memo = d.memos.get(tx, view.element.uid)
                if memo is not None and not memo.finished and not memo.archived and memo.deleted_at is None:
                    return memo.uid
        return None

    def _take_over_into_memo(self, info: ItemInfo, memo_uid: str) -> None:
        d = self._d
        with d.database.transaction() as tx:
            memo = d.memos.get(tx, memo_uid)
            assert memo is not None
            present = {document.name for document in d.documents.list_for(tx, memo_uid)}
            now = d.clock.now()
            for name in info.documents:
                target = renamed_document(name, info.label, memo.label)
                if target is None or target in present:
                    continue
                document = d.gateway.read_document(info.uid, name)
                if document is not None:
                    kind = document_kind(memo.label, target) or SPEC
                    d.documents.insert(tx, Document(memo_uid, target, kind, document.content, 1, now))

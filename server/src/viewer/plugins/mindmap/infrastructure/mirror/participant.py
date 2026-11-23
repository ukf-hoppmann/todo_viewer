"""Datenbank ⇄ Einträge für den Spiegel der Mindmap: liest Knoten, Bäume und Dokumente, vergibt Labels, schreibt.

Diese Stufe trägt Knoten (Titel, Text, Markierung, Papierkorb), den Projektbaum, freie Maps mit ihren Platzierungen
und die Dokumente der Knoten. Zuordnungen von Items und Memos, entfernte Platzierungen und der Papierkorb der Bäume
folgen in einer späteren Stufe; bis dahin lässt der Teilnehmer sie in der Datenbank unberührt.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping, Sequence
from dataclasses import replace
from datetime import datetime

from viewer.core.application.ports import Clock, Database, Transaction
from viewer.core.application.sync import SyncChanges
from viewer.core.domain.errors import DomainError
from viewer.core.domain.sync import MirrorEntry, MirrorFormatError
from viewer.plugins.mindmap.application.ports import Document, DocumentRepository, MindmapRepository
from viewer.plugins.mindmap.application.service import KIND, title_of
from viewer.plugins.mindmap.domain import tree as rules
from viewer.plugins.mindmap.domain.documents import document_kind
from viewer.plugins.mindmap.domain.listing import changed_placements, placements_from_listing
from viewer.plugins.mindmap.domain.model import TREE_FREE, TREE_PROJECT, MindmapViolation, Node, Tree
from viewer.plugins.mindmap.infrastructure.mirror.syntax import (
    KIND_DOCUMENT,
    KIND_NODE,
    KIND_TREE,
    PROJECT_FILE,
    format_time,
    parse_time,
)
from viewer.plugins.workspace import ElementRegistry

_LABEL = re.compile(r"^[A-Z]+-\d+$")


def _time(value: str) -> datetime:
    return datetime.fromisoformat(parse_time(value)[:-1] + "+00:00")


def _suffix(label: str, name: str) -> str | None:
    """`NODE-001_spec_Teil.md` → `spec_Teil`; `None`, wenn der Name nicht dem Label folgt."""
    match = re.fullmatch(rf"{re.escape(label)}_(notes|spec(?:_[A-Za-z0-9-]+)?)\.md", name)
    return match.group(1) if match else None


def _violation(entry: MirrorEntry, error: DomainError) -> MirrorFormatError:
    file, line = entry.source or (PROJECT_FILE, 1)
    return MirrorFormatError("rule_violation", str(error), file=file, line=line)


class MindmapParticipant:
    def __init__(
        self,
        repository: MindmapRepository,
        documents: DocumentRepository,
        registry: ElementRegistry,
        database: Database,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._documents = documents
        self._registry = registry
        self._database = database
        self._clock = clock

    # --- Lesen ----------------------------------------------------------------------------------------------------

    def load(self, project: str) -> list[MirrorEntry]:
        """Die Bäume, ihre Knoten (auch im Papierkorb) und die Dokumente der Knoten. Maps im Papierkorb und Knoten,
        die nur in ihnen stehen, gehören zur nächsten Stufe."""
        repo = self._repository
        with self._database.transaction() as tx:
            trees = [t for t in [repo.tree_of_project(tx, project)] if t is not None]
            trees += repo.free_maps(tx, project)
            nodes: dict[str, Node] = {}
            for tree in trees:
                nodes.update({n.uid: n for n in repo.nodes_in_tree(tx, tree.uid, include_deleted=True)})
            label = {uid: n.label for uid, n in nodes.items()}
            entries = [self._tree_entry(tx, tree, label) for tree in trees]
            entries += [self._node_entry(n) for n in nodes.values()]
            for node in nodes.values():
                for document in self._documents.list_for(tx, node.uid):
                    suffix = _suffix(node.label, document.name)
                    if suffix is not None:
                        fields = {"content": document.content, "kind": document.kind}
                        refs = {"node": (node.label,)}
                        entries.append(MirrorEntry(KIND_DOCUMENT, document.name, fields, refs, f"{node.uid}/{suffix}"))
        return entries

    @staticmethod
    def _node_entry(node: Node) -> MirrorEntry:
        fields = {
            "title": node.title,
            "text": (node.text or "").rstrip("\n") or None,
            "mark": node.mark,
            "deleted_at": format_time(node.deleted_at) or None,
        }
        return MirrorEntry(KIND_NODE, node.label, fields, {}, node.uid, trashed=node.deleted_at is not None)

    def _tree_entry(self, tx: Transaction, tree: Tree, label: Mapping[str, str]) -> MirrorEntry:
        """Der Baum als Liste in Tiefensuche: Labels der Knoten und ihre Tiefen."""
        placements = self._repository.placements(tx, tree.uid)
        tokens: list[str] = []
        depths: list[int] = []
        pending = [(p.node_uid, 0) for p in reversed(rules.children_of(placements, None))]
        while pending:
            node, depth = pending.pop()
            tokens.append(label.get(node, node))
            depths.append(depth)
            pending += [(p.node_uid, depth + 1) for p in reversed(rules.children_of(placements, node))]
        fields = {
            "tree_kind": tree.kind,
            "name": tree.name if tree.kind == TREE_FREE else None,
            "deleted_at": None,
            "depths": depths,
            "removed": [],
        }
        return MirrorEntry(KIND_TREE, None, fields, {"nodes": tuple(tokens)} if tokens else {}, tree.uid)

    def resolve_labels(self, project: str, labels: Collection[str]) -> Mapping[str, str]:
        found: dict[str, str] = {}
        with self._database.transaction() as tx:
            for token in labels:
                element = self._registry.find_by_label(tx, project, token) if _LABEL.match(token) else None
                if element is not None:
                    found[token] = str(element.label)
        return found

    def assign_labels(
        self, project: str, entries: Sequence[MirrorEntry], tx: Transaction, taken: Collection[str] = ()
    ) -> Mapping[str, str]:
        """Neue Knoten bekommen das nächste freie `NODE-nnn`; neue Maps haben kein Label, nur eine Uid (der Platzhalter
        bleibt ihr Name); Dokumente heißen nach dem Label ihres Knotens."""
        self._registry.note_labels(tx, project, list(taken))
        result: dict[str, str] = {}
        for entry in entries:
            if entry.kind == KIND_NODE:
                result[str(entry.placeholder)] = self._registry.reserve_label(tx, project, KIND)
            elif entry.kind == KIND_TREE:
                result[str(entry.placeholder)] = str(entry.placeholder)
        for entry in entries:
            if entry.kind == KIND_DOCUMENT:
                placeholder = str(entry.placeholder)
                owner = entry.refs["node"][0]
                result[placeholder] = f"{result.get(owner, owner)}_{placeholder.split('/', 1)[1]}.md"
        return result

    # --- Schreiben ------------------------------------------------------------------------------------------------

    def apply(self, project: str, changes: SyncChanges, tx: Transaction) -> None:
        """Reihenfolge: Bäume, Knoten, Platzierungen, Dokumente (ein Knoten besteht vor seiner Platzierung)."""
        both = (*changes.created, *changes.updated)
        new_uids = {str(e.uid) for e in changes.created}
        trees = [(e, self._write_tree(tx, project, e)) for e in both if e.kind == KIND_TREE]
        nodes = [e for e in both if e.kind == KIND_NODE]
        for entry in nodes:
            self._write_node(tx, project, entry, str(entry.uid) in new_uids)
        labels = {str(e.label): str(e.uid) for e in nodes}
        for entry, tree in trees:
            self._write_placements(tx, project, entry, tree, labels)
        for entry in both:
            if entry.kind == KIND_DOCUMENT:
                self._write_document(tx, project, entry, labels)
        for entry in changes.deleted:
            if entry.kind == KIND_NODE:
                element = self._registry.get(tx, str(entry.uid))
                if element is not None and element.deleted_at is None:
                    self._registry.mark_deleted(tx, element.uid)

    def _write_tree(self, tx: Transaction, project: str, entry: MirrorEntry) -> Tree:
        repo = self._repository
        f = entry.fields
        uid = str(entry.uid)
        try:
            if f["tree_kind"] == TREE_PROJECT:
                # Ein Projekt hat einen Projektbaum: eine Datei mit anderer Uid wird dem vorhandenen zugeordnet
                existing = repo.tree_of_project(tx, project)
                if existing is not None:
                    return existing
                tree = Tree(uid, project, TREE_PROJECT)
                repo.insert_tree(tx, tree)
                return tree
            name = rules.clean_map_name(f["name"])
            stored = repo.get_tree(tx, uid)
            taken = [t.name or "" for t in repo.free_maps(tx, project) if t.uid != uid]
            if stored is None:
                rules.check_map_name_free(name, taken)
                tree = Tree(uid, project, TREE_FREE, name)
                repo.insert_tree(tx, tree)
                return tree
            rules.check_project(stored.project_uid, project)
            if stored.name != name:
                rules.check_map_name_free(name, taken)
                repo.rename_tree(tx, uid, name, stored.revision)
                return replace(stored, name=name, revision=stored.revision + 1)
            return stored
        except MindmapViolation as error:
            raise _violation(entry, error) from error

    def _write_node(self, tx: Transaction, project: str, entry: MirrorEntry, is_new: bool) -> None:
        repo = self._repository
        f = entry.fields
        uid, label = str(entry.uid), str(entry.label)
        try:
            title = title_of(f["title"])
            mark = rules.check_mark(f["mark"])
        except DomainError as error:
            raise _violation(entry, error) from error
        text = f["text"] or None
        if is_new:
            self._registry.register_as(tx, project, KIND, uid, label, title)
            repo.insert_node(tx, Node(uid, project, label, title, text, 1, mark=mark))
        else:
            stored = repo.get_node(tx, uid)
            assert stored is not None
            updated = replace(stored, title=title, text=text, mark=mark)
            if updated != stored:
                self._registry.bump_revision(tx, uid, stored.revision)
                repo.update_node(tx, updated)
                if title != stored.title:
                    self._registry.set_title(tx, uid, title)
        element = self._registry.get(tx, uid)
        deleted_at = f["deleted_at"]
        if element is not None and deleted_at and element.deleted_at is None:
            self._registry.mark_deleted(tx, uid, _time(deleted_at))
        elif element is not None and not deleted_at and element.deleted_at is not None:
            self._registry.restore(tx, uid)

    def _node_uid(self, tx: Transaction, project: str, entry: MirrorEntry, token: str, new: Mapping[str, str]) -> str:
        if token in new:
            return new[token]
        element = self._registry.find_by_label(tx, project, token)
        if element is None or self._repository.get_node(tx, element.uid) is None:
            file, line = entry.source or (PROJECT_FILE, 1)
            raise MirrorFormatError("unknown_reference", f"`{token}` gab es nie", file=file, line=line)
        return str(element.uid)

    def _write_placements(
        self, tx: Transaction, project: str, entry: MirrorEntry, tree: Tree, new: Mapping[str, str]
    ) -> None:
        uids = [self._node_uid(tx, project, entry, token, new) for token in entry.refs.get("nodes", ())]
        stored = self._repository.placements(tx, tree.uid)
        try:
            wanted = placements_from_listing(tree.uid, uids, list(entry.fields["depths"]))
            changed = changed_placements(stored, wanted)
            rules.check_acyclic(rules.apply(stored, changed))
        except MindmapViolation as error:
            raise _violation(entry, error) from error
        self._repository.upsert_placements(tx, changed)

    def _write_document(self, tx: Transaction, project: str, entry: MirrorEntry, new: Mapping[str, str]) -> None:
        token = entry.refs["node"][0]
        node_uid = self._node_uid(tx, project, entry, token, new)
        name, content = str(entry.label), entry.fields["content"]
        existing = self._documents.get(tx, node_uid, name)
        now = self._clock.now()
        if existing is None:
            kind = document_kind(token, name) or entry.fields["kind"]
            self._documents.insert(tx, Document(node_uid, name, kind, content, 1, now))
        elif existing.content != content:
            self._documents.update(tx, node_uid, name, content, existing.revision, now)

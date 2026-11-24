"""Datenbank ⇄ Einträge für den Spiegel der Mindmap: liest Knoten, Bäume und Dokumente, vergibt Labels, schreibt.

Der Teilnehmer trägt Knoten (Titel, Text, Markierung, Papierkorb), den Projektbaum, freie Maps mit ihren Platzierungen,
entfernten Platzierungen und ihrem Papierkorb, die Dokumente der Knoten und die Zuordnungen von Items und Memos zu
Knoten. Er ändert nur Verknüpfungen, nie die Items und Memos selbst (sie gehören dem Backlog und den Memos).
Wie die Operationen der API öffnet er keine eigene Transaktion: der Sync bringt seine mit, darum rechnet er mit den
Regeln der Domäne und schreibt über die Ports, nicht über `AssignmentService`, `BranchService` oder `MapService`.
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
from viewer.plugins.mindmap.application.assignments import ITEM_KINDS, MEMO_KIND, ROLE
from viewer.plugins.mindmap.application.maps import MapTrash, trash_map
from viewer.plugins.mindmap.application.ports import Document, DocumentRepository, MindmapRepository
from viewer.plugins.mindmap.application.service import KIND, title_of
from viewer.plugins.mindmap.domain import assignment as assign_rules
from viewer.plugins.mindmap.domain import tree as rules
from viewer.plugins.mindmap.domain.documents import document_kind
from viewer.plugins.mindmap.domain.listing import (
    changed_placements,
    changed_removed,
    check_no_children_of_removed,
    placements_from_listing,
)
from viewer.plugins.mindmap.domain.model import (
    TREE_FREE,
    TREE_PROJECT,
    MindmapViolation,
    Node,
    Placement,
    RemovedPlacement,
    Tree,
)
from viewer.plugins.mindmap.infrastructure.mirror.syntax import (
    KIND_DOCUMENT,
    KIND_NODE,
    KIND_TREE,
    PROJECT_FILE,
    format_time,
    parse_time,
)
from viewer.plugins.workspace import Element, ElementRegistry, Links, Projects

_LABEL = re.compile(r"^[A-Z]+-\d+$")


def _time(value: str) -> datetime:
    return datetime.fromisoformat(parse_time(value)[:-1] + "+00:00")


def _suffix(label: str, name: str) -> str | None:
    """`NODE-001_spec_Teil.md` → `spec_Teil`; `None`, wenn der Name nicht dem Label folgt."""
    match = re.fullmatch(rf"{re.escape(label)}_(notes|spec(?:_[A-Za-z0-9-]+)?)\.md", name)
    return match.group(1) if match else None


def _violation(entry: MirrorEntry, error: DomainError, line: int | None = None) -> MirrorFormatError:
    file, header = entry.source or (PROJECT_FILE, 1)
    return MirrorFormatError("rule_violation", str(error), file=file, line=line or header)


class MindmapParticipant:
    def __init__(
        self,
        repository: MindmapRepository,
        documents: DocumentRepository,
        registry: ElementRegistry,
        links: Links,
        projects: Projects,
        database: Database,
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._documents = documents
        self._registry = registry
        self._links = links
        self._projects = projects
        self._map_trash = MapTrash(repository, registry, projects)
        self._database = database
        self._clock = clock

    # --- Lesen ----------------------------------------------------------------------------------------------------

    def load(self, project: str) -> list[MirrorEntry]:
        """Die Bäume (auch freie Maps im Papierkorb), ihre Knoten (auch im Papierkorb), die Knoten hinter entfernten
        Platzierungen und die Dokumente der Knoten."""
        repo = self._repository
        with self._database.transaction() as tx:
            trees = [t for t in [repo.tree_of_project(tx, project)] if t is not None]
            trees += repo.free_maps(tx, project)
            trees += repo.deleted_maps(tx, [project])
            removed = {t.uid: repo.removed_placements(tx, t.uid) for t in trees}
            nodes: dict[str, Node] = {}
            for tree in trees:
                nodes.update({n.uid: n for n in repo.nodes_in_tree(tx, tree.uid, include_deleted=True)})
                for row in removed[tree.uid]:
                    for uid in (row.node_uid, row.root_uid, row.parent_uid):
                        node = repo.get_node(tx, uid) if uid and uid not in nodes else None
                        if node is not None:
                            nodes[node.uid] = node
            label = {uid: n.label for uid, n in nodes.items()}
            names: dict[str, str] = {}
            entries = [self._tree_entry(tx, tree, label, removed[tree.uid]) for tree in trees]
            entries += [self._node_entry(tx, n, project, names) for n in nodes.values()]
            for node in nodes.values():
                for document in self._documents.list_for(tx, node.uid):
                    suffix = _suffix(node.label, document.name)
                    if suffix is not None:
                        fields = {"content": document.content, "kind": document.kind}
                        refs = {"node": (node.label,)}
                        entries.append(MirrorEntry(KIND_DOCUMENT, document.name, fields, refs, f"{node.uid}/{suffix}"))
        return entries

    def _node_entry(self, tx: Transaction, node: Node, project: str, names: dict[str, str]) -> MirrorEntry:
        fields = {
            "title": node.title,
            "text": (node.text or "").rstrip("\n") or None,
            "mark": node.mark,
            "deleted_at": format_time(node.deleted_at) or None,
        }
        refs: dict[str, tuple[str, ...]] = {}
        for role, element in self._assigned(tx, node.uid):
            refs.setdefault(role, ())
            refs[role] = (*refs[role], self._target(tx, element, project, names))
        refs = {role: tuple(sorted(set(targets))) for role, targets in refs.items()}
        return MirrorEntry(KIND_NODE, node.label, fields, refs, node.uid, trashed=node.deleted_at is not None)

    def _assigned(self, tx: Transaction, node_uid: str) -> list[tuple[str, Element]]:
        """Die Items (`items`) und Memos (`memos`), die der Knoten trägt, samt Verknüpfung."""
        found: list[tuple[str, Element]] = []
        for view in self._links.outgoing(tx, node_uid):
            if view.link.role != ROLE:
                continue
            if view.element.kind in ITEM_KINDS:
                found.append(("items", view.element))
            elif view.element.kind == MEMO_KIND:
                found.append(("memos", view.element))
        return found

    def _target(self, tx: Transaction, element: Element, project: str, names: dict[str, str]) -> str:
        """Das Label des Elements; das eines anderen Projekts mit dessen Namen (`Projekt:LABEL`)."""
        if element.project_uid == project:
            return str(element.label)
        if element.project_uid not in names:
            other = self._projects.get(tx, element.project_uid)
            names[element.project_uid] = other.name if other is not None else element.project_uid
        return f"{names[element.project_uid]}:{element.label}"

    def _tree_entry(
        self, tx: Transaction, tree: Tree, label: Mapping[str, str], removed: Sequence[RemovedPlacement]
    ) -> MirrorEntry:
        """Der Baum als Liste in Tiefensuche: Labels der Knoten und ihre Tiefen, dazu die entfernten Platzierungen."""
        placements = self._repository.placements(tx, tree.uid)
        tokens: list[str] = []
        depths: list[int] = []
        pending = [(p.node_uid, 0) for p in reversed(rules.children_of(placements, None))]
        while pending:
            node, depth = pending.pop()
            tokens.append(label.get(node, node))
            depths.append(depth)
            pending += [(p.node_uid, depth + 1) for p in reversed(rules.children_of(placements, node))]
        rows = sorted(removed, key=lambda r: label.get(r.node_uid, r.node_uid))
        # Ein Parent, den es nicht mehr gibt, steht als Wurzel
        parents = [label.get(r.parent_uid) if r.parent_uid else None for r in rows]
        fields = {
            "tree_kind": tree.kind,
            "name": tree.name if tree.kind == TREE_FREE else None,
            "deleted_at": format_time(tree.deleted_at) or None,
            "depths": depths,
            "removed": [
                {"position": r.position, "has_parent": p is not None} for r, p in zip(rows, parents, strict=True)
            ],
        }
        refs: dict[str, tuple[str, ...]] = {}
        if tokens:
            refs["nodes"] = tuple(tokens)
        if rows:
            refs["removed_nodes"] = tuple(label[r.node_uid] for r in rows)
            refs["removed_groups"] = tuple(label.get(r.root_uid, label[r.node_uid]) for r in rows)
            if any(parents):
                refs["removed_parents"] = tuple(p for p in parents if p is not None)
        return MirrorEntry(KIND_TREE, None, fields, refs, tree.uid)

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
        """Reihenfolge: Bäume, Knoten, Zuordnungen, Platzierungen, Papierkorb der Bäume, Dokumente, Löschungen (ein
        Knoten besteht vor seiner Platzierung, eine Map vor ihrem Papierkorb)."""
        both = (*changes.created, *changes.updated)
        new_uids = {str(e.uid) for e in changes.created}
        trees = [(e, self._write_tree(tx, project, e)) for e in both if e.kind == KIND_TREE]
        nodes = [e for e in both if e.kind == KIND_NODE]
        for entry in nodes:
            self._write_node(tx, project, entry, str(entry.uid) in new_uids)
        labels = {str(e.label): str(e.uid) for e in nodes}
        self._write_assignments(tx, project, nodes, new_uids)
        for entry, tree in trees:
            self._write_placements(tx, project, entry, tree, labels)
        for entry, tree in trees:
            self._write_map_trash(tx, entry, tree)
        for entry in both:
            if entry.kind == KIND_DOCUMENT:
                self._write_document(tx, project, entry, labels)
        for entry in changes.deleted:
            self._delete(tx, project, entry)

    def _delete(self, tx: Transaction, project: str, entry: MirrorEntry) -> None:
        """Eine Löschung, die der Owner entschieden hat: ein Knoten oder eine Map geht in den Papierkorb, ein Dokument
        wird entfernt (Dokumente haben keinen Papierkorb)."""
        if entry.kind == KIND_NODE:
            element = self._registry.get(tx, str(entry.uid))
            if element is not None and element.deleted_at is None:
                self._registry.mark_deleted(tx, element.uid)
        elif entry.kind == KIND_DOCUMENT:
            self._documents.delete(tx, str(entry.uid).split("/", 1)[0], str(entry.label))
        elif entry.kind == KIND_TREE:
            tree = self._repository.get_tree(tx, str(entry.uid))
            if tree is None or tree.deleted_at is not None:
                return
            try:
                trash_map(self._repository, self._registry, tx, tree, self._clock.now(), None)
            except MindmapViolation as error:
                raise MirrorFormatError("rule_violation", str(error), file=PROJECT_FILE, line=1) from error

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
            alive = not f["deleted_at"]  # eine Map im Papierkorb behält ihren Namen, ohne ihn zu belegen
            if stored is None:
                if alive:
                    rules.check_map_name_free(name, taken)
                tree = Tree(uid, project, TREE_FREE, name)
                repo.insert_tree(tx, tree)
                return tree
            rules.check_project(stored.project_uid, project)
            if stored.name != name:
                if alive:
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
        """Die Liste des Baums und seine `Removed:`-Zeilen. Eine entfernte Platzierung ist das Gedächtnis „stand
        dort“: Zeilen, die die Datei nicht mehr nennt, werden vergessen, solange der Knoten nicht wieder in der
        Liste steht."""
        refs = entry.refs
        uids = [self._node_uid(tx, project, entry, token, new) for token in refs.get("nodes", ())]
        stored = self._repository.placements(tx, tree.uid)
        wanted_removed = self._wanted_removed(tx, project, entry, tree, new)
        try:
            wanted = placements_from_listing(tree.uid, uids, list(entry.fields["depths"]))
            changed = changed_placements(stored, wanted)
            mark, forget = changed_removed(self._repository.removed_placements(tx, tree.uid), wanted_removed, uids)
            gone = {r.node_uid for r in mark}
            live = [p for p in rules.apply(stored, changed) if p.node_uid not in gone]
            rules.check_acyclic(live)
            check_no_children_of_removed(live, gone | {r.node_uid for r in wanted_removed})
        except MindmapViolation as error:
            raise _violation(entry, error) from error
        self._repository.upsert_placements(tx, changed)
        self._repository.delete_placements(
            tx, [Placement(r.tree_uid, r.node_uid, r.parent_uid, r.position) for r in forget]
        )
        for root in dict.fromkeys(r.root_uid for r in mark):
            rows = [Placement(r.tree_uid, r.node_uid, r.parent_uid, r.position) for r in mark if r.root_uid == root]
            self._repository.upsert_placements(tx, rows)
            self._repository.mark_removed(tx, rows, root)

    def _wanted_removed(
        self, tx: Transaction, project: str, entry: MirrorEntry, tree: Tree, new: Mapping[str, str]
    ) -> list[RemovedPlacement]:
        nodes = entry.refs.get("removed_nodes", ())
        groups = entry.refs.get("removed_groups", ())
        parents = iter(entry.refs.get("removed_parents", ()))
        wanted: list[RemovedPlacement] = []
        for row, node, group in zip(entry.fields["removed"], nodes, groups, strict=True):
            parent = self._node_uid(tx, project, entry, next(parents), new) if row["has_parent"] else None
            wanted.append(
                RemovedPlacement(
                    tree.uid,
                    self._node_uid(tx, project, entry, node, new),
                    parent,
                    int(row["position"]),
                    self._node_uid(tx, project, entry, group, new),
                )
            )
        return wanted

    def _write_map_trash(self, tx: Transaction, entry: MirrorEntry, tree: Tree) -> None:
        """Papierkorb einer freien Map: sie geht samt den Knoten, die nur in ihr stehen, hinein und kommt mit den
        Knoten zurück, die mit ihr gingen (Regeln der API). Nie endgültig löschen."""
        if tree.kind != TREE_FREE:
            return
        stored = self._repository.get_tree(tx, tree.uid)
        assert stored is not None
        wanted = entry.fields["deleted_at"]
        try:
            if wanted and stored.deleted_at is None:
                trash_map(self._repository, self._registry, tx, stored, _time(wanted), None)
            elif wanted and stored.deleted_at != _time(wanted):
                self._repository.set_tree_deleted(tx, stored.uid, _time(wanted))
            elif not wanted and stored.deleted_at is not None:
                self._map_trash.restore(tx, stored.uid)
        except MindmapViolation as error:
            raise _violation(entry, error) from error

    def _write_assignments(self, tx: Transaction, project: str, nodes: Sequence[MirrorEntry], new: set[str]) -> None:
        """Items und Memos an den Knoten: erst alles Gelöste, dann das Neue (ein Item darf in einer Synchronisierung
        den Knoten wechseln). Verknüpft wird nur; das Item selbst bleibt unberührt."""
        wanted = {str(e.uid): self._wanted_targets(tx, project, e) for e in nodes}
        for entry in nodes:
            uid = str(entry.uid)
            keep = wanted[uid]
            for role, element in self._assigned(tx, uid) if uid not in new else []:
                if element.uid not in keep[role]:
                    for view in self._links.outgoing(tx, uid):
                        if view.link.role == ROLE and view.element.uid == element.uid:
                            self._links.remove(tx, view.link.uid)
        for entry in nodes:
            uid = str(entry.uid)
            held = {(role, e.uid) for role, e in self._assigned(tx, uid)} if uid not in new else set()
            for role, targets in wanted[uid].items():
                for element_uid, token in targets.items():
                    if (role, element_uid) not in held:
                        self._attach(tx, project, entry, role, token, element_uid)

    def _wanted_targets(self, tx: Transaction, project: str, entry: MirrorEntry) -> dict[str, dict[str, str]]:
        """Je Rolle die Elemente der Datei: uid → Verweis."""
        return {
            role: {self._element_uid(tx, project, entry, role, token): token for token in entry.refs.get(role, ())}
            for role in ("items", "memos")
        }

    def _element_uid(self, tx: Transaction, project: str, entry: MirrorEntry, role: str, token: str) -> str:
        """Das Element hinter einem Verweis `LABEL` oder `Projekt:LABEL`; unbekannt ist `unknown_reference` mit der
        Zeile des Verweises."""
        qualifier, separator, bare = token.rpartition(":")
        target = project
        if separator:
            match = next((p for p in self._projects.list(tx) if p.name == qualifier), None)
            target = match.uid if match is not None else ""
        element = self._registry.find_by_label(tx, target, bare if separator else token) if target else None
        file, header = entry.source or (PROJECT_FILE, 1)
        line = entry.source_lines.get(f"{role}:{token}", header)
        if element is None:
            raise MirrorFormatError(
                "unknown_reference", f"`{token}` gab es nie (verwendet von `{entry.label}`)", file=file, line=line
            )
        kinds = ITEM_KINDS if role == "items" else (MEMO_KIND,)
        if element.kind not in kinds:
            what = "ein Item (`EPIC-…`, `STORY-…`, `TASK-…`)" if role == "items" else "ein Memo (`MEMO-…`)"
            raise MirrorFormatError("rule_violation", f"`{token}` ist kein {what}", file=file, line=line)
        return str(element.uid)

    def _attach(
        self, tx: Transaction, project: str, entry: MirrorEntry, role: str, token: str, element_uid: str
    ) -> None:
        """Hängt das Item an den Knoten (höchstens an einen) oder verlinkt das Memo (an mehrere); wie die API."""
        element = self._registry.get(tx, element_uid)
        assert element is not None
        line = entry.source_lines.get(f"{role}:{token}")
        try:
            if element.project_uid != project:
                raise MindmapViolation("mindmap_other_project", f"{token} gehört zu einem anderen Projekt")
            if element.deleted_at is not None:
                raise MindmapViolation("mindmap_item_deleted", f"{token} liegt im Papierkorb", ref=token)
            if role == "items":
                holders = [v.element.uid for v in self._links.incoming(tx, element_uid) if v.link.role == ROLE]
                assign_rules.check_assign(holders, str(entry.uid), False)
        except DomainError as error:
            raise _violation(entry, error, line) from error
        self._links.add(tx, str(entry.uid), element_uid, ROLE)

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

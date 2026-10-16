from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from todo_viewer.domain.documents import content_version
from todo_viewer.domain.errors import DocumentNotFoundError, VersionConflictError
from todo_viewer.domain.item import Item
from todo_viewer.domain.lifecycle import LifecycleRules
from todo_viewer.domain.retype import Notice, RetypePlan, RetypePlanner, rewrite_ids
from todo_viewer.domain.source import Source
from todo_viewer.domain.trash import live

from ..ports import BacklogRepository, DocumentStore, ItemStatusListener, NoteRepository


@dataclass(frozen=True)
class RetypeResult:
    item: Item
    archive_supported: bool
    old_id: str
    notices: tuple[Notice, ...]


@dataclass(frozen=True)
class _DocumentText:
    item_id: str  # where the document is after the retype
    name: str
    content: str
    version: str  # of the text that was read


class RetypeService:
    """Changes an item's type: new id, and every reference to the old id in the backlog follows."""

    def __init__(self, backlogs: BacklogRepository, documents: DocumentStore, planner: RetypePlanner,
                 rules: LifecycleRules, notes: NoteRepository, listener: ItemStatusListener | None = None):
        self._listener = listener
        self._backlogs = backlogs
        self._notes = notes
        self._documents = documents
        self._planner = planner
        self._rules = rules

    def retype(self, source: Source, item_id: str, version: str, new_type: str) -> RetypeResult:
        """Nothing is written before the plan passed the lifecycle rules and every document was read.

        The documents move first and move back if the backlog cannot be written. If the
        final rewrite of document texts fails, the backlog stays consistent but a text may still name the old id.
        """
        backlog = self._backlogs.load(source)
        if backlog.find(item_id).version != version:
            raise VersionConflictError(item_id)
        plan = self._planner.plan(backlog.items, item_id, new_type)
        after = {i.id: c.applied_to(i) for i, c in plan.changes}
        in_use = live(backlog.items)
        # Flaws the files already had move with the new id; only what the new type adds counts as new.
        renamed = dataclasses.replace(after[item_id], item_type=backlog.find(item_id).item_type)
        self._rules.check_change([renamed if i.id == item_id else after.get(i.id, i) for i in in_use],
                                 [after.get(i.id, i) for i in in_use])
        texts = self._rewritten_texts(source, plan, item_id)

        self._documents.relabel_documents(source, item_id, plan.new_id, plan.document_renames)
        try:
            self._notes.relink_item(source.project, item_id, plan.new_id)
            stored = self._backlogs.apply_all(source, list(plan.changes))
        except Exception:
            self._notes.relink_item(source.project, plan.new_id, item_id)
            self._documents.relabel_documents(source, plan.new_id, item_id,
                                              {new: old for old, new in plan.document_renames.items()})
            raise
        if self._listener is not None:  # the item is changed for good: tell the notes even if a text cannot follow
            self._listener.item_retyped(source.project, item_id, plan.new_id)
        for text in texts:
            self._documents.write(source, text.item_id, text.name, text.content, text.version)
        return RetypeResult(next(i for i in stored if i.id == plan.new_id), backlog.archive_available, item_id,
                            plan.notices)

    def _rewritten_texts(self, source: Source, plan: RetypePlan, item_id: str) -> list[_DocumentText]:
        texts = []
        for doc in plan.documents:
            try:
                content = self._documents.read(source, doc.item_id, doc.name)
            except DocumentNotFoundError:
                continue  # listed in the item but not stored: nothing to rewrite
            rewritten = rewrite_ids(content, item_id, plan.new_id)
            if rewritten != content:
                texts.append(_DocumentText(doc.new_item_id, doc.new_name, rewritten, content_version(content)))
        return texts

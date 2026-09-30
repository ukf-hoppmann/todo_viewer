from __future__ import annotations

from dataclasses import dataclass

from todo_viewer.domain.documents import content_version
from todo_viewer.domain.errors import DocumentNotFoundError, VersionConflictError
from todo_viewer.domain.lifecycle import LifecycleRules
from todo_viewer.domain.retype import RetypePlan, RetypePlanner, rewrite_ids
from todo_viewer.domain.source import Source
from todo_viewer.domain.trash import live

from ..ports import BacklogRepository, DocumentStore
from .items import ItemResult


@dataclass(frozen=True)
class _DocumentText:
    path: str  # where the document lives after the retype
    content: str
    version: str  # of the text that was read


class RetypeService:
    """Changes an item's type: new id, and every reference to the old id in the backlog follows."""

    def __init__(self, backlogs: BacklogRepository, documents: DocumentStore, planner: RetypePlanner,
                 rules: LifecycleRules):
        self._backlogs = backlogs
        self._documents = documents
        self._planner = planner
        self._rules = rules

    def retype(self, source: Source, item_id: str, version: str, new_type: str) -> ItemResult:
        """Nothing is written before the plan passed the lifecycle rules and every document was read.

        The document folder moves first and moves back if the backlog files cannot be written. If the
        final rewrite of document texts fails, the backlog stays consistent but a text may still name the old id.
        """
        backlog = self._backlogs.load(source)
        if backlog.find(item_id).version != version:
            raise VersionConflictError(item_id)
        plan = self._planner.plan(backlog.items, item_id, new_type)
        after = {i.id: c.applied_to(i) for i, c in plan.changes}
        in_use = live(backlog.items)
        self._rules.check_change(in_use, [after.get(i.id, i) for i in in_use])
        texts = self._rewritten_texts(source, plan, item_id)

        self._documents.rename_item_folder(source, item_id, plan.new_id, plan.file_renames)
        try:
            stored = self._backlogs.apply_all(source, list(plan.changes))
        except Exception:
            self._documents.rename_item_folder(source, plan.new_id, item_id,
                                               {new: old for old, new in plan.file_renames.items()})
            raise
        for text in texts:
            self._documents.write(source, text.path, text.content, text.version)
        return ItemResult(next(i for i in stored if i.id == plan.new_id), backlog.archive_available)

    def _rewritten_texts(self, source: Source, plan: RetypePlan, item_id: str) -> list[_DocumentText]:
        texts = []
        for old_path, new_path in plan.document_paths.items():
            try:
                content = self._documents.read(source, old_path)
            except DocumentNotFoundError:
                continue  # listed in the item but not on disk: nothing to rewrite
            rewritten = rewrite_ids(content, item_id, plan.new_id)
            if rewritten != content:
                texts.append(_DocumentText(new_path, rewritten, content_version(content)))
        return texts

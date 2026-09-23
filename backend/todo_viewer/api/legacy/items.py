from __future__ import annotations

from pathlib import Path, PurePath

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from todo_viewer.domain.editing import Field
from todo_viewer.domain.errors import ConfigMissingError, EntryMovedError, UnknownFormatError
from todo_viewer.domain.item import ItemFormat, ItemRef, Location

from ..dependencies import ItemEdits, Lookup, Overview
from ..errors import error_response
from .schemas import DataOut, ItemOut, ItemResult, ItemUpdateIn, ListedItemOut, SourceStatusOut

router = APIRouter(prefix="/api", tags=["legacy"])

# The legacy API addresses items by file path; v2 uses source id + location instead.
LEGACY_FILES = {"TODO.md": Location.ACTIVE, "archive.md": Location.ARCHIVE}


@router.get("/data", response_model=DataOut, responses={404: {"description": "config.json missing"}})
def data(overview: Overview) -> DataOut | JSONResponse:
    try:
        entries = overview.overview()
    except ConfigMissingError:
        return JSONResponse({"items": [], "sources": [], "error": "config.json not found"}, status_code=404)
    items: list[ListedItemOut] = []
    sources: list[SourceStatusOut] = []
    for entry in entries:
        problem = entry.backlog.problem
        sources.append(SourceStatusOut(
            index=entry.index, project=entry.source.project, path=entry.source.path,
            count=len(entry.backlog.items),
            error=problem.message if problem else None, code=problem.code if problem else None,
        ))
        items.extend(ListedItemOut.listed(item, entry.index, entry.backlog.supports_archive(item))
                     for item in entry.backlog.items)
    return DataOut(items=items, sources=sources)


@router.post("/items/update", response_model=ItemResult)
def update_item(body: ItemUpdateIn, edits: ItemEdits, lookup: Lookup) -> ItemResult | JSONResponse:
    path = Path(body.source_file)
    location = LEGACY_FILES.get(path.name)
    if body.field in Field.EDITABLE:
        if not path.exists():
            return error_response("file_not_found", "Source file not found.", 404)
        if body.format not in {f.value for f in ItemFormat}:
            raise UnknownFormatError(body.format)
        if location is None:
            raise EntryMovedError()

    # Only files of configured sources may be written.
    source = lookup.by_folder(PurePath(path.parent))
    ref = ItemRef(body.id, location or Location.ACTIVE, body.line)
    try:
        result = edits.edit(source, ref, body.field, body.value, body.resolution)
    except OSError as exc:
        return error_response("write_failed", str(exc), 500)
    return ItemResult(item=ItemOut.of(result.item))

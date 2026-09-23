from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from todo_viewer.domain.editing import Field
from todo_viewer.domain.errors import ConfigMissingError, EntryMovedError, UnknownFormatError
from todo_viewer.domain.item import ItemFormat, ItemRef, Location
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.markdown.syntax import ARCHIVE_FILE, TODO_FILE

from ..dependencies import ItemEdits, Overview
from ..errors import error_response
from ..schemas import DataOut, ItemOut, ItemResult, ItemUpdateIn, ListedItemOut, SourceStatusOut

router = APIRouter(prefix="/api", tags=["items"])

LEGACY_FILES = {TODO_FILE: Location.ACTIVE, ARCHIVE_FILE: Location.ARCHIVE}


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
def update_item(body: ItemUpdateIn, edits: ItemEdits) -> ItemResult | JSONResponse:
    # Legacy addressing by file path; replaced by source index + item ref in API v2.
    path = Path(body.source_file)
    location = LEGACY_FILES.get(path.name)
    if body.field in Field.EDITABLE:
        if not path.exists():
            return error_response("file_not_found", "Source file not found.", 404)
        if body.format not in {f.value for f in ItemFormat}:
            raise UnknownFormatError(body.format)
        if location is None:
            raise EntryMovedError()

    source = Source(project=body.project, path=str(path.parent))
    ref = ItemRef(body.id, location or Location.ACTIVE, body.line)
    try:
        result = edits.edit(source, ref, body.field, body.value, body.resolution)
    except OSError as exc:
        return error_response("write_failed", str(exc), 500)
    return ItemResult(item=ItemOut.of(result.item))

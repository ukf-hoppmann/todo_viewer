from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body

from todo_viewer.domain.errors import ConfigMissingError
from todo_viewer.domain.trash import live

from ..dependencies import Documents, Folders, Items, Lookup, Overview, Sources, Trash, UiState
from .schemas import (
    BacklogOut,
    DocumentIn,
    DocumentOut,
    ErrorOut,
    FolderListingOut,
    HealthOut,
    IndexItemOut,
    IndexOut,
    ItemCreateIn,
    ItemEditIn,
    ItemOut,
    NotesEntryIn,
    ProblemOut,
    SourceIn,
    SourceOut,
    SourceStatusOut,
    VersionIn,
)

ERRORS: dict[int | str, dict[str, Any]] = {
    status: {"model": ErrorOut} for status in (400, 403, 404, 409)
}

router = APIRouter(prefix="/api/v2", responses=ERRORS)


@router.get("/health", tags=["meta"])
def health() -> HealthOut:
    """Cheap reachability check for agents; touches no backlog files."""
    return HealthOut(status="ok", api="2")


@router.get("/backlog", tags=["items"])
def backlog(overview: Overview) -> BacklogOut:
    """All configured sources with their items. Without a config the backlog is empty."""
    try:
        entries = overview.overview()
    except ConfigMissingError:
        entries = []
    return BacklogOut(
        sources=[SourceStatusOut(**SourceOut.of(e.source).model_dump(), item_count=len(live(e.backlog.items)),
                                 problem=ProblemOut.of(e.backlog.problem)) for e in entries],
        items=[ItemOut.of(e.source, item, e.backlog.archive_available)
               for e in entries for item in live(e.backlog.items)],
    )


@router.get("/index", tags=["items"])
def index(overview: Overview, lookup: Lookup, source_id: str | None = None) -> IndexOut:
    """Lean overview of all items (active and archived) for placing new work; optionally one source."""
    only = lookup.by_id(source_id) if source_id is not None else None
    try:
        entries = overview.overview(only)
    except ConfigMissingError:
        entries = []
    return IndexOut(items=[IndexItemOut.of(e.source, item) for e in entries for item in live(e.backlog.items)])


@router.post("/items", tags=["items"], status_code=201)
def create_item(body: ItemCreateIn, items: Items, lookup: Lookup) -> ItemOut:
    """Creates an Open item with the next free id of its type at the end of the active list."""
    source = lookup.by_id(body.source_id)
    result = items.create(source, body.type, body.fields())
    return ItemOut.of(source, result.item, result.archive_supported)


@router.get("/items/{source_id}/{item_id}", tags=["items"])
def get_item(source_id: str, item_id: str, items: Items, lookup: Lookup) -> ItemOut:
    """One item by id, active or archived."""
    source = lookup.by_id(source_id)
    result = items.get(source, item_id)
    return ItemOut.of(source, result.item, result.archive_supported)


@router.delete("/items/{source_id}/{item_id}", tags=["trash"])
def delete_item(source_id: str, item_id: str, version: str, trash: Trash, lookup: Lookup,
                cascade: bool = False) -> list[ItemOut]:
    """Moves the item in `version` to the trash and returns the items moved.

    With children the answer is 409 has_children listing them; repeat with cascade=true to move them too.
    Refused (409 item_referenced) while items outside the trash depend on it.
    """
    source = lookup.by_id(source_id)
    return [ItemOut.of(source, r.item, r.archive_supported) for r in trash.delete(source, item_id, version, cascade)]


@router.get("/trash", tags=["trash"])
def list_trash(trash: Trash, lookup: Lookup, source_id: str) -> list[ItemOut]:
    """Items in the trash of a source."""
    source = lookup.by_id(source_id)
    return [ItemOut.of(source, r.item, r.archive_supported) for r in trash.in_trash(source)]


@router.post("/trash/{source_id}/{item_id}/restore", tags=["trash"])
def restore_item(source_id: str, item_id: str, body: VersionIn, trash: Trash, lookup: Lookup) -> list[ItemOut]:
    """Takes the item and its descendants out of the trash; refused while its parent is in the trash."""
    source = lookup.by_id(source_id)
    return [ItemOut.of(source, r.item, r.archive_supported) for r in trash.restore(source, item_id, body.version)]


@router.delete("/trash/{source_id}/{item_id}", tags=["trash"])
def purge_item(source_id: str, item_id: str, version: str, trash: Trash, lookup: Lookup) -> list[ItemOut]:
    """Deletes the item and its descendants for good, with their items/<ID>/ folders; returns them."""
    source = lookup.by_id(source_id)
    return [ItemOut.of(source, r.item, r.archive_supported) for r in trash.purge(source, item_id, version)]


@router.patch("/items/{source_id}/{item_id}", tags=["items"])
def edit_item(source_id: str, item_id: str, body: ItemEditIn, items: Items, lookup: Lookup) -> ItemOut:
    """Changes one or more fields of the item in `version`; all changes are checked and written together.

    Completed/Rejected need a resolution and move the item to the archive.
    """
    source = lookup.by_id(source_id)
    result = items.edit(source, item_id, body.version, body.fields.changes(), body.resolution)
    return ItemOut.of(source, result.item, result.archive_supported)


@router.get("/items/{source_id}/{item_id}/documents/{name}", tags=["documents"])
def read_document(source_id: str, item_id: str, name: str, documents: Documents, lookup: Lookup) -> DocumentOut:
    """A notes or spec document of the item, with its version."""
    return DocumentOut.of_result(documents.read(lookup.by_id(source_id), item_id, name))


@router.put("/items/{source_id}/{item_id}/documents/{name}", tags=["documents"])
def write_document(source_id: str, item_id: str, name: str, body: DocumentIn, documents: Documents,
                   lookup: Lookup) -> DocumentOut:
    """Replaces a notes or spec document in `version` with the whole new text.

    With version null it creates `<ID>_notes.md` (first notes; the item needs a summary) or
    `<ID>_spec.md` / `<ID>_spec_<topic>.md`. New dated notes entries: POST …/notes.
    """
    result = documents.write(lookup.by_id(source_id), item_id, name, body.content, body.version, body.summary)
    return DocumentOut.of_result(result)


@router.post("/items/{source_id}/{item_id}/notes", tags=["documents"])
def append_notes(source_id: str, item_id: str, body: NotesEntryIn, documents: Documents,
                 lookup: Lookup) -> DocumentOut:
    """Appends a dated Discussed/Decided/Open entry to the item's notes (created on first use)."""
    result = documents.append_notes(lookup.by_id(source_id), item_id, body.topic, body.discussed, body.decided,
                                    body.open, body.summary)
    return DocumentOut.of_result(result)


@router.get("/sources", tags=["sources"])
def list_sources(sources: Sources) -> list[SourceOut]:
    try:
        return [SourceOut.of(s) for s in sources.all()]
    except ConfigMissingError:
        return []


@router.post("/sources", tags=["sources"])
def add_source(body: SourceIn, sources: Sources) -> SourceOut:
    return SourceOut.of(sources.add(body.path, body.project))


@router.put("/sources/{source_id}", tags=["sources"])
def update_source(source_id: str, body: SourceIn, sources: Sources) -> SourceOut:
    return SourceOut.of(sources.update(source_id, body.path, body.project))


@router.delete("/sources/{source_id}", tags=["sources"])
def remove_source(source_id: str, sources: Sources) -> SourceOut:
    return SourceOut.of(sources.remove(source_id))


@router.get("/folders", tags=["sources"])
def folders(browser: Folders, path: str | None = None) -> FolderListingOut:
    """Subfolders of a folder for the backlog folder picker."""
    return FolderListingOut.of(browser.browse(path))


@router.get("/ui-state", tags=["ui-state"])
def get_ui_state(state: UiState) -> dict[str, Any]:
    return state.get()


@router.put("/ui-state", tags=["ui-state"])
def put_ui_state(state: UiState, body: Annotated[dict[str, Any], Body()]) -> dict[str, Any]:
    state.save(body)
    return body

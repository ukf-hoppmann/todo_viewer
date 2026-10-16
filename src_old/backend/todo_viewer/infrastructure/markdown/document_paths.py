"""Where the markdown format keeps an item's documents: `items/<ID>/<name>`, relative to the backlog folder.

The rest of the application addresses documents by item id and name. A name with a `/` is a path the
backlog wrote down elsewhere; it is kept as-is and resolved relative to the backlog folder.
"""
from __future__ import annotations

from pathlib import Path

from todo_viewer.domain.editing import ID_RE
from todo_viewer.domain.errors import DocumentForbiddenError

ITEMS_FOLDER = "items"
DOCUMENT_SUFFIXES = {".md", ".markdown", ".txt"}


def name_of(item_id: str, path: str) -> str:
    """The document name for a path written in the item's Notes/Spec field."""
    prefix = f"{ITEMS_FOLDER}/{item_id}/"
    rest = path[len(prefix):] if path.startswith(prefix) else ""
    return rest if rest and "/" not in rest else path


def path_of(item_id: str, name: str) -> str:
    """The path written into the item's Notes/Spec field for a document name."""
    return name if "/" in name else f"{ITEMS_FOLDER}/{item_id}/{name}"


def item_folder(base: Path, item_id: str) -> Path:
    """`items/<ID>/` of an item; raises DocumentForbiddenError for ids that could leave it."""
    items = (base / ITEMS_FOLDER).resolve()
    if not ID_RE.match(item_id) or item_id in {".", ".."}:
        raise DocumentForbiddenError()
    folder = (items / item_id).resolve()
    if folder.parent != items:
        raise DocumentForbiddenError()
    return folder


def document_file(base: Path, item_id: str, name: str) -> Path:
    """The file of a document; only markdown/text files inside the backlog folder are allowed."""
    root = base.resolve()
    folder = item_folder(base, item_id)
    target = (root / name if "/" in name else folder / name).resolve()
    if not name or not target.is_relative_to(root) or target.suffix.lower() not in DOCUMENT_SUFFIXES:
        raise DocumentForbiddenError()
    return target

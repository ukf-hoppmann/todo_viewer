"""Domain errors. Each carries a stable `code` the frontend translates."""
from __future__ import annotations


class DomainError(Exception):
    code = "domain_error"

    def __init__(self, message: str, code: str | None = None, **details: str):
        super().__init__(message)
        if code is not None:
            self.code = code
        self.details = details

    @property
    def message(self) -> str:
        return str(self)


class NotFoundError(DomainError):
    """Something the request refers to does not exist (anymore)."""


class ForbiddenError(DomainError):
    """The request is valid but not allowed."""


class ConflictError(DomainError):
    """The request clashes with the current state (external edits, duplicates)."""


# --- items ---

class ItemNotFoundError(NotFoundError):
    code = "item_not_found"

    def __init__(self, item_id: str):
        super().__init__(f"Item '{item_id}' not found.", id=item_id)


class DuplicateItemError(ConflictError):
    code = "duplicate_item"

    def __init__(self, item_id: str):
        super().__init__(f"Item '{item_id}' exists more than once in this backlog.", id=item_id)


class VersionConflictError(ConflictError):
    code = "version_conflict"

    def __init__(self, item_id: str):
        super().__init__(f"'{item_id}' was changed in the meantime. Reload and try again.", id=item_id)


class ItemFolderExistsError(ConflictError):
    code = "item_folder_exists"

    def __init__(self, item_id: str):
        super().__init__(f"A document folder for '{item_id}' exists already.", id=item_id)


class FileChangedError(ConflictError):
    code = "file_changed"

    def __init__(self) -> None:
        super().__init__("The file was changed externally while saving. Please try again.")


class LifecycleViolationError(ConflictError):
    """A change would break a parent lifecycle or structure rule; `code` names the rule."""

    MESSAGES = {
        "epic_without_required_child": "Epic {id} needs at least one required child before it leaves Open.",
        "required_children_not_done": "Required children of {id} are not far enough: {items}.",
        "children_still_active": "{id} cannot be closed while children are active: {items}.",
        "parent_closed": "{id} cannot be active below a closed parent. Reopen {items} first (in this order, "
                         "e.g. set status 'In progress'), then retry.",
        "epic_with_parent": "Epic {id} cannot have a parent.",
        "required_for_parent_missing": "{id} has a parent but no 'Required for parent'.",
        "parent_cycle": "Parent references form a cycle: {items}.",
        "dependency_cycle": "Dependencies form a cycle: {items}.",
        "unknown_reference": "{id} refers to unknown items: {items}.",
        "summary_required_with_notes": "{id} has notes and therefore needs a summary.",
        "item_referenced": "{id} cannot be deleted while other items refer to it: {items}.",
        "has_children": "{id} has children that would be deleted too: {items}. Confirm with cascade.",
        "item_deleted": "{id} is in the trash; restore it first.",
        "item_not_deleted": "{id} is not in the trash.",
        "parent_deleted": "The parent of {id} is in the trash; restore {items} instead.",
    }

    def __init__(self, code: str, item_id: str, related: tuple[str, ...] = ()):
        items = ", ".join(related)
        message = self.MESSAGES.get(code, "Rule {code} violated by {id}.").format(id=item_id, items=items, code=code)
        super().__init__(message, code=code, id=item_id, items=items)


class NotEditableError(DomainError):
    code = "not_editable"

    def __init__(self, field: str):
        super().__init__(f"Field '{field}' is not editable.")


class InvalidValueError(DomainError):
    code = "invalid_value"

    def __init__(self, field: str, allowed: tuple[str, ...]):
        super().__init__(f"Invalid value for '{field}'; allowed: {', '.join(allowed)}.", field=field)


class ValueRequiredError(DomainError):
    code = "value_required"

    def __init__(self, field: str):
        super().__init__(f"Field '{field}' must not be empty.", field=field)


class ResolutionRequiredError(DomainError):
    code = "resolution_required"

    def __init__(self) -> None:
        super().__init__("A resolution is required for Completed/Rejected.")


# --- sources ---

class SourceGoneError(NotFoundError):
    code = "source_gone"

    def __init__(self, message: str = "Source not found (config was probably changed externally)."):
        super().__init__(message)


class ConfigMissingError(NotFoundError):
    code = "config_missing"

    def __init__(self) -> None:
        super().__init__("config.json not found")


class ProjectNotEmptyError(ConflictError):
    code = "project_not_empty"

    def __init__(self, project: str):
        super().__init__(f"Project '{project}' still has items in the database and cannot be removed.",
                         project=project)


class DuplicateSourceError(ConflictError):
    code = "duplicate"

    def __init__(self) -> None:
        super().__init__("This folder is already configured.")


class BacklogExistsError(ConflictError):
    code = "backlog_exists"

    def __init__(self) -> None:
        super().__init__("This folder already holds a TODO.md; add it as a source instead.")


class InvalidSourceError(DomainError):
    """The backlog folder is unusable; `code` says why (missing_path, not_found, not_a_dir, no_todo)."""


# --- sync ---

class SyncPathMissingError(InvalidSourceError):
    code = "sync_path_missing"

    def __init__(self) -> None:
        super().__init__("This project has no folder to sync with. Set one first.")


class SyncSameBackendError(ConflictError):
    code = "sync_same_backend"

    def __init__(self) -> None:
        super().__init__("This project is stored in markdown files; they can only be read into the database.")


class SyncSourceInvalidError(InvalidSourceError):
    code = "sync_source_invalid"

    def __init__(self, reason: str, message: str):
        super().__init__(f"Nothing was changed: {message}", reason=reason)


class SyncRequiredError(ConflictError):
    code = "sync_required"

    def __init__(self) -> None:
        super().__init__("The two sides differ. Sync them first, then switch the backend.")


class BackupFailedError(ConflictError):
    code = "backup_failed"

    def __init__(self, reason: str) -> None:
        super().__init__(f"Nothing was changed: the backup of the current primary source failed ({reason}).",
                         reason=reason)


class SyncStaleError(ConflictError):
    code = "sync_stale"

    def __init__(self) -> None:
        super().__init__("Either side changed since the preview. Request a new preview.")


# --- documents ---

class DocumentForbiddenError(ForbiddenError):
    code = "forbidden"

    def __init__(self) -> None:
        super().__init__("Only markdown files inside the backlog folder can be opened.")


class DocumentNotFoundError(NotFoundError):
    code = "file_not_found"

    def __init__(self, path: str, message: str = "File not found."):
        super().__init__(message, path=path)


# --- notes ---

class NoteNotFoundError(NotFoundError):
    code = "note_not_found"

    def __init__(self, label: str):
        super().__init__(f"Note '{label}' not found.", id=label)


class TopicNotFoundError(NotFoundError):
    code = "topic_not_found"

    def __init__(self, label: str):
        super().__init__(f"Topic '{label}' not found.", id=label)


class TopicTooDeepError(DomainError):
    code = "topic_too_deep"

    def __init__(self, label: str, max_depth: int):
        super().__init__(f"Topic '{label}' would be nested deeper than {max_depth} levels.", id=label,
                         max_depth=str(max_depth))


class TopicLoopError(DomainError):
    code = "topic_loop"

    def __init__(self, label: str):
        super().__init__(f"Topic '{label}' cannot become a child of itself or of one of its children.", id=label)

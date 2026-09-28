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
        super().__init__(f"Item '{item_id}' was changed in the meantime. Reload and try again.", id=item_id)


class FileChangedError(ConflictError):
    code = "file_changed"

    def __init__(self) -> None:
        super().__init__("The file was changed externally while saving. Please try again.")


class NotEditableError(DomainError):
    code = "not_editable"

    def __init__(self, field: str):
        super().__init__(f"Field '{field}' is not editable.")


class InvalidValueError(DomainError):
    code = "invalid_value"

    def __init__(self, field: str, allowed: tuple[str, ...]):
        super().__init__(f"Invalid value for '{field}'; allowed: {', '.join(allowed)}.", field=field)


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


class DuplicateSourceError(ConflictError):
    code = "duplicate"

    def __init__(self) -> None:
        super().__init__("This folder is already configured.")


class InvalidSourceError(DomainError):
    """The backlog folder is unusable; `code` says why (missing_path, not_found, not_a_dir, no_todo)."""


# --- documents ---

class DocumentForbiddenError(ForbiddenError):
    code = "forbidden"

    def __init__(self) -> None:
        super().__init__("Only markdown files inside the backlog folder can be opened.")


class DocumentNotFoundError(NotFoundError):
    code = "file_not_found"

    def __init__(self, path: str, message: str = "File not found."):
        super().__init__(message, path=path)

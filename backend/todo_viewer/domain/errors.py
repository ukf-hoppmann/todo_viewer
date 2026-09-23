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


# --- items ---

class EntryMovedError(DomainError):
    code = "entry_moved"

    def __init__(self, message: str = "Entry not found (file was probably changed externally)."):
        super().__init__(message)


class NotEditableError(DomainError):
    code = "not_editable"

    def __init__(self, field: str):
        super().__init__(f"Field '{field}' is not editable.")


class CheckboxStatusOnlyError(DomainError):
    code = "checkbox_status_only"

    def __init__(self) -> None:
        super().__init__("Only the status is editable for checkbox lists.")


class UnknownFormatError(DomainError):
    code = "unknown_format"

    def __init__(self, fmt: str):
        super().__init__(f"Unknown format '{fmt}'.")


class ResolutionRequiredError(DomainError):
    code = "resolution_required"

    def __init__(self) -> None:
        super().__init__("A resolution is required for Completed/Rejected.")


# --- sources ---

class SourceGoneError(NotFoundError):
    code = "source_gone"

    def __init__(self, message: str = "Source not found (config was probably changed externally)."):
        super().__init__(message)


class DuplicateSourceError(DomainError):
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

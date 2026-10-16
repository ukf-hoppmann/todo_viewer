"""Fehler des Core: stabile Codes, Umwandlung nur in den Hosts."""

from __future__ import annotations

from typing import Any


class DomainError(Exception):
    """Erwarteter Fehlschlag mit stabilem `code`; `details` ist JSON-tauglich."""

    code: str = "domain_error"

    def __init__(self, message: str, *, code: str | None = None, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code
        self.message = message
        self.details: dict[str, Any] = details if details is not None else {}


class NotFound(DomainError):
    code = "not_found"


class VersionConflict(DomainError):
    code = "version_conflict"


class InvalidInput(DomainError):
    code = "invalid_input"


class MigrationFailed(DomainError):
    code = "migration_failed"


class SchemaViolation(MigrationFailed):
    code = "schema_violation"


class DatabaseTooNew(DomainError):
    code = "database_too_new"


class PluginSetupError(Exception):
    """Die feste Plugin-Liste ist fehlerhaft; der Start wird verhindert."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("Ungültige Plugin-Liste:\n" + "\n".join(f"- {p}" for p in problems))

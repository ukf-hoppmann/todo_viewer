# Scope: <name>

<!-- Rules for one area of the project, listed in the Scopes table of
architecture.md. Always English; MUST, SHOULD, and MAY have their RFC 2119
meaning. Keep it short: say who owns what and what is mandatory, never how
(link to the interface docs for that). Applies in addition to architecture.md,
never instead of it. Stored as architecture/<name>.md. -->

## Responsibilities

<!-- One row per concern of this area. Owner: the layer or module that
provides it. Others do: what other code does with it. Others don't: what other
code must not build itself. Details: a Markdown link to the interface doc that
explains how. -->

| Concern | Owner | Others do | Others don't | Details |
|---|---|---|---|---|

## Rules

<!-- Numbered rules for this area only. A rule that can be checked
mechanically names its test, e.g. "Enforced by: tests/architecture/test_layers.py". -->

## Required on use

<!-- Optional. Files that must be read in full before new code in the paths
of this scope uses certain identifiers. Uses: identifiers in backticks,
comma-separated (letters, digits, '_', '$', '.'; matched as whole words);
Read: files relative to the project root in backticks, must exist. Example:
| `reportError` | `docs/development/interfaces/core/errors.md` | -->

| Uses | Read |
|---|---|

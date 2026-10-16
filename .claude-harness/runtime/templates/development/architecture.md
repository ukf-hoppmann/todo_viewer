# Architecture rules

<!-- Binding architecture of this project. Always English; MUST, SHOULD, and
MAY have their RFC 2119 meaning. Keep this file short: rules that apply to the
whole project only. Rules for one area go into a scope file. A rule that can
be checked mechanically names its test, e.g. "Enforced by:
tests/architecture/test_layers.py". -->

## Rules

<!-- Numbered sections of rules, e.g. "## 1. Dependency direction". -->

## Scopes

<!-- Areas with additional rules in architecture/<Scope>.md. A scope applies
in addition to this file, never instead of it. Paths: patterns relative to
the project root in backticks, comma-separated; `*` stays within one path
part, `**` spans any number of parts. Example row:
| llm-integration | `src/llm/**`, `src/prompts/*.py` | Model calls and prompts | -->

| Scope | Paths | Covers |
|---|---|---|

## Inherited rules

<!-- Only in a repository with subprojects: rules of another project that
apply here as well, e.g. the core's rules for a plugin. Project: a name from
[projects] of the root config, or root. Rules in backticks: architecture.md
(that project's main rules file) or scope names of that project; an inherited
scope applies regardless of its path patterns. Nothing is inherited further.
If an inherited rule contradicts a rule of this project, this project's rule
wins and the conflict is named. Example row:
| root | `architecture.md`, `plugin-api` | -->

| Project | Rules |
|---|---|

## Changing these rules

These rules are guidelines the project owner may deliberately break. If a
requirement or design does not fit them, the AI names the conflict and
proposes solutions, and the project owner decides (skill
`claude-harness:conflicts`). A change to this file or a scope file becomes
binding only after the project owner approves it.

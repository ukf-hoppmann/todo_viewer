---
name: harness-conflicts
description: Rules for conflicts with binding rules. Use when a requirement, a design, or a wish of the project owner conflicts with the project's binding rules or with a Claude_Harness rule, or when the harness itself causes a problem.
---

# Conflicts with rules

Applies to every project using Claude_Harness, regardless of module switches.

- **Project rules:** the rule files of the `development` suite in the project
  (e.g. `architecture.md` and its scopes). The project owner owns them.
- **Harness rules:** what the plugin defines: its skills, hooks, formats, and
  templates. They can only be changed in the Claude_Harness repository.

A conflict exists when a project or harness rule would have to be broken or
changed, or when the result the project owner asked for would change. An
implementation that follows all rules and delivers the requested result is
not a conflict; choose it without asking.

## Procedure

1. Stop. Do not implement the affected part, not even provisionally. Parts
   that are not affected may continue.
2. Tell the project owner briefly: what is requested, which rule stands in
   the way (file and section, or skill), and why it does not fit.
3. Propose solutions where useful: a one-time exception, the smallest change
   to the project rule, a different implementation of the requirement; for
   harness rules also switching off the module or suite part, or a change to
   the harness.
4. The project owner decides; follow the decision. Rules are guidelines the
   owner may deliberately break.

After the decision:

- **One-time exception:** implement it. Do not record it separately; a daily
  report mentions it only if it is worth reporting anyway.
- **Change a project rule:** show the proposed change first; it is binding
  once the owner approves it.
- **Change the harness:** hand it over (below).

Hooks enforce harness rules mechanically; you cannot grant an exception to
them. Name the config switch that turns the module or suite part off.

Raise problems with the harness itself (errors, unsuitable rules, disruptive
hooks) on your own and offer the handover.

## Handing a harness change over

Only after the project owner agrees.

1. Run `python3 ".claude-harness/runtime/scripts/harness_repo.py"` in the
   project root. It prints the harness repository on this machine, or nothing.
2. Write the task in English so it stands on its own: the owner's wish, the
   occasion in the project, the affected harness rule, the solutions already
   discussed. Tell the receiving session to load skill `harness-todo`,
   place the item by its rules, and create new items only after the owner
   approves.
3. Hand it over, first option that applies:
   - The project is the harness repository: work on the backlog directly.
   - Your environment can start a session in another directory (e.g. a task
     suggestion with a working directory in the desktop app): use it.
   - Otherwise give the owner a command to run:
     `cd <repository> && claude "<task>"`.
   - No repository found: give the task as text to carry over, and offer to
     add this machine's path to `[harness].repo` in
     `.claude-harness/config.toml`. `harness_repo.py --suggest` prints a
     candidate; show it and ask before writing.

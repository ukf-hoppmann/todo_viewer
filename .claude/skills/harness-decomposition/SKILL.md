---
name: harness-decomposition
description: Rules for splitting work into small, separately testable steps and for when tests come first (development suite). Use when planning or starting the implementation of a change, presenting an implementation plan, splitting an epic into stories, or considering whether a story should get child tasks.
---

# Decomposition

## Before you start

Read `.claude-harness/config.toml` of the project the work belongs to (with
subprojects, the session start lists each project and its folder; paths below
are relative to that folder). The rules apply only if `[modules].development`
is `true` and `[development].decomposition` is not `false`; otherwise say so
and stop.

## Why

Small steps with their own test fail early and cheaply instead of late and
expensively. A step that carries everything it needs can be implemented
without the planning session's context, even by a simpler model.

## Two levels

Work is split at two levels of very different size. Do not mix them.

### Backlog: stories and tasks (coarse)

Cut by capability first, then by session.

- **Story:** one coherent capability the owner can name and check as a
  whole ("import bank statements"), never a layer or component
  ("database infrastructure"). Its size is not limited to one session or
  one plan.
- **Task:** one delivery of a story that fits into one session and ends in
  a checkable state: it has its own test or observable check, the project
  builds, and all tests pass.

When splitting an epic:

1. List the capabilities the epic delivers; each becomes a story.
2. A story that needs more than one session gets tasks, one per
   session-sized delivery, ordered by dependencies.
3. A story that fits into one session gets no tasks.

Check before proposing:

- A story without an owner-visible result of its own is a task of the
  story it enables, or of the epic if it enables several.
- Stories that only make sense together or build the same capability
  become one story with tasks.
- An epic with more than about eight stories: check whether they bundle
  into fewer capability stories; if not, say why in the proposal.
- The layers of one feature within a session are never backlog tasks;
  they are plan sections.

Create or restructure items only as the `todo` skill allows (owner
approval). If an existing epic breaks these rules, propose a regrouping;
do not regroup on your own.

### Plan: sections (fine)

An implementation plan consists of sections. A section is cut right when all
of these hold:

- **One job.** It can be described without "and also".
- **Testable alone.** It has its own test or an observable check: a command
  and its expected result.
- **Integrable alone.** After it, the project builds and all tests pass. No
  broken intermediate state.
- **Self-contained.** It names its goal, the files or symbols it touches, its
  interface to neighbouring sections, what it must not touch, its test
  (and whether it comes first, see below), and
  when to stop and ask instead of guessing.
- **Decided.** It contains no open decision. Interfaces between sections
  (data formats, signatures, names) are fixed in the plan, not in a section.

Before a section adds a new building block (function, component, helper),
check the catalogs of reusable building blocks (skill
`harness-interfaces`, if the project keeps them) and name in the plan
what is reused. What several owners need goes into the shared layer that the
architecture names; if it names none, ask the owner before placing it.

Order sections by their dependencies: each section uses only sections that
are already implemented and tested. There is no fixed direction such as
bottom-up.

With subprojects, a plan that touches several projects names each of them;
every file follows the rules of its own project.

The last section is always **integration**: check the whole flow against the
original goal.

Do not split, or merge sections, when:

- the task has one job and one test (a bug fix, a config change): one
  section;
- a section would not be testable alone: merge it into the neighbour whose
  test covers it;
- the change is mechanical and the same across many files (a rename): one
  section;
- splitting would leave a state that does not build or fails tests.

Example: a button triggers processing whose result is stored, reloaded, and
shown. Sections: 1. persist, 2. load, 3. backend processing, 4. API
endpoint, 5. frontend button awaiting the response, 6. integration.

## Test first

Each section states whether its test is written before the code:

- **Bug fix:** yes. First a test that shows the bug and fails, then the fix.
- **New behavior with a clear interface** (function, CLI, file format,
  hook): yes. Write the test, see it fail, then implement.
- **Refactoring:** no new test. Tests pass before and after and are not
  changed in between.
- **Configuration, documentation, prototypes, UI polish:** no test first.

A test written first must fail for the expected reason before the code is
written. Nothing about the cycle is written down; the test itself is the
result.

## Running tests

Which tests to run and where they live: skill `harness-testing`.

## Dimension checklist

While splitting, go through these dimensions for the task:

persistence · loading/state · domain logic · interfaces (API, CLI, file
formats, hooks) · UI · configuration · security · error handling ·
migration/operations · tests · documentation

- Assign every touched dimension to a section, or give it one of its own.
- Tests and documentation normally belong to the section that makes the
  change, not to a section of their own.
- End the plan with one line that records the result, e.g. "Dimensions:
  persistence §1, loading §2, domain logic §3, interfaces §4, UI §5, tests
  per section, docs §6; not touched: security, migration."

## Where the plan lives

The sections belong in the implementation plan (plan mode or chat). A
backlog spec stays without a step sequence. The plan is not stored in the
backlog: it is made from the current spec when implementation starts.

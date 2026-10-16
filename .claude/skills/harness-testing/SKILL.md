---
name: harness-testing
description: Rules for where tests live, how the test folder is structured, the two test kinds, and running tests (development suite). Use when writing, placing, or running tests, or when the owner asks for a functional test.
---

# Tests

## Before you start

Read `.claude-harness/config.toml` of the project the work belongs to (with
subprojects, the session start lists each project and its folder; paths below
are relative to that folder). The rules apply only if `[modules].development`
is `true` and `[development].testing` is not `false`; otherwise say so and
stop.

The test folder is `[development].tests`, relative to the project root
(default `tests`, next to the source folder). Below it is called `<tests>`.

## Why

The owner has to find every test without searching the code, and has to be
able to check business behavior on their own without reading implementation
tests. So all tests share one place, and tests for the agent are kept apart
from tests for the owner.

## Location

- Every test lives below `<tests>`. No inline tests (doctests, test blocks in
  source files) and no test files next to the code.
- If a framework expects another place (e.g. `__tests__` next to the code for
  Jest, `#[cfg(test)]` modules in Rust), name it when it first comes up and
  let the owner decide. Do not deviate on your own.

## Structure

```
<tests>/
  implementation/
    unit/          one unit in isolation; mirrors the source folder structure
    integration/   several components together: real files, processes, local test servers
    system/        optional: the whole system end to end, started and used as its users do
  functional/
    <function>/    one folder per business function, e.g. filters/, load_cache/
      test_<scenario>
  fixtures/        test data shared by several tests
  helpers/         test code shared by several tests
  README.md        how to run the tests (see Commands)
```

- Create a folder only when something goes into it.
- File names follow the framework's convention; without one, `test_<name>`.
- Something used by one test only stays next to that test.

### System tests

`unit/` and `integration/` are the default. Add `system/` when the project
is a system that can be run as a whole (an app, a service, a CLI with its
real configuration) and a flow can only be secured end to end, e.g. install,
start, and one request through all layers. They are optional: do not create
them for every change, and do not add them to a project that has no such
system.

- They drive the system only from outside, through its real entry points
  (CLI, HTTP, UI, installed plugin), not through internal functions.
- They set up and remove what they need (temporary folders, local test
  servers, test data); never production services or real accounts.
- If they need something that is not always available (a browser, a
  container, a long start-up), keep them out of the normal test run and give
  them their own command in `<tests>/README.md`.

## Implementation tests

Written by the agent to secure its own work: test-first cycles, regression
tests, checks of a plan section. They run in the normal test run and must
pass before work is reported as done.

## Functional tests

They belong to the owner. With them the owner checks whether a business
function behaves as they want, e.g. which rows a filter setting keeps, or
whether a longer sequence after adding load and cache returns the right data.

- Write them when the owner asks. When a new business function comes up, you
  may propose one.
- They are not part of the normal test run, and they are not evidence for
  your own work; implementation tests are.
- One folder per business function, one file per scenario, named after what
  the owner cares about, not after the module.
- The first sentence of each test says which behavior it checks.
- Inputs can be set as parameters (command-line options or the framework's
  parametrization), so the owner can try several scenarios without changing
  code, e.g. every filter option of a filter. Without parameters a standard
  scenario runs.
- The test prints its inputs and the output in a readable form. Where the
  expected result is clear, it also asserts it and shows expected and actual
  data on failure.
- Keep them runnable on their own: data from `<tests>/fixtures/` or from
  parameters; say in the README what a test needs (e.g. a running service).

## Commands

`<tests>/README.md`, written in `docs.language`, states:

- the command for all implementation tests (without the functional tests);
- the command for the system tests, if they have their own;
- the command for one functional test, with its parameters and an example;
- a list of the functional tests: function, scenario, what it checks.

Update it when you add, rename, or remove a functional test or change a
command.

## Running tests

Run the tests that the change can affect, not always the whole suite. A
change to shared code, persistence, or interfaces affects more than its own
file; look for its callers.

- Run the affected tests again after the last change, however small, before
  reporting the work as done.
- Name what you did not test and why (e.g. a suite that needs a database,
  or system tests that were not run).
- Call a failing test unrelated or pre-existing only after checking it, e.g.
  by running it without your change.
- Run functional tests only when the owner asks, or to show them a result.

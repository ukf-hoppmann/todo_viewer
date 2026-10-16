---
name: harness-semver
description: Rules for release versions (SemVer) with a version file, mirrored files, and release tags. Use when a change is merged back into its base branch, when the user asks for a release, when the semver hook reminds you, or when setting up the module.
---

# Release versions

## Before you start

1. Read `.claude-harness/config.toml` of the project the work belongs to (with
   subprojects, the session start lists each project and its folder; paths
   below are relative to that folder). If `[modules].semver` is not `true`,
   these rules do not apply — say so and stop.
2. Run `python3 ".claude-harness/runtime/scripts/semver.py" status` (with
   subprojects add `--project <name>`). It prints the version file, the last
   release tag, the allowed next versions, findings, and the unreleased
   commits under `semver.paths`.

## Why

Every finished change gets at most one version step, and never more than it
needs. Steps and experiments inside one change are bundled. The version file
has one format everywhere, so a script can check it; the project's own files
(`package.json`, `Cargo.toml`, …) mirror it for their tools.

## When to release

- **After merging a worktree** into its base branch (skill
  `claude-harness:worktree`): release the merged change. All sections of one
  plan give one release; a discarded worktree gives none.
- **Without the `worktree` part:** when the owner confirms a change as
  finished.
- **When the owner asks** for a release, e.g. for direct commits. Direct commits never trigger a release on their own; the next
  release covers them.
- Never change the version file in commits that belong to a change.

## Classify

Read the unreleased commits and their diff
(`git diff <last tag>..HEAD -- <semver.paths>`). The largest effect on users
of the project decides:

- **major:** an incompatible change of a public contract (API, CLI, file
  format, configuration key, documented behavior);
- **minor:** a notable new feature that users would name on its own, e.g. a
  new module or area, a new command, skill, or standalone tool;
- **patch:** a compatible fix or improvement of existing behavior, including
  small new features inside an existing one: an extra option or setting,
  a sub-function, a new or sharper rule in an existing skill, an optional
  convention;
- **none:** only internal changes, tests, or documentation. Then there is no
  release; say so.

When in doubt between minor and patch, choose patch. Examples: a new module
with its own switch and settings is minor; an optional extra rule, filter
option, or export format for an existing feature is patch; a corrected rule
or behavior is patch.

While MAJOR is `0`, an incompatible change counts as minor. Pick the version
only from the allowed versions `status` prints. A major step at or above
`1.0.0` needs the owner's confirmation first; everything else proceeds
without questions.

## Release

1. On the branch the change was merged into, where the merge happened (the
   main checkout, or the change's worktree), write the new version into the
   version file (only `MAJOR.MINOR.PATCH` and a newline) and into every file
   in `semver.sync`, in that file's own format.
2. Rerun `status`: it must report no findings.
3. Commit only these files: `Release <tag>`.
4. Create an annotated tag on that commit:
   `git tag -a <tag> -m "<tag>: <one-line reason>"`. The tag is
   `<tag prefix><version>` as `status` shows it.
5. Do not push commit or tag.
6. Report the version, the step, and the reason. The release can be undone
   with `git tag -d <tag>` and `git revert <release commit>`.

The daily report lists the release like any other merged change;
there is no changelog.

## Setup

When the module is switched on for a project:

1. Ask which of the project's files carry the version (e.g.
   `package.json`, `Cargo.toml`, `pyproject.toml`) and add them to
   `semver.sync`; ask what belongs to the released product and set
   `semver.paths` (default: the whole project).
2. Create the version file with the version found in those files, else
   `0.1.0`.
3. Offer to tag the current commit as the starting release
   (`<tag prefix><version>`); create it only after approval.
4. Run `status` and report the result.

## When the hook reminds you

The hook reports a missing or invalid version file, a version more than one
step above (or below) the last release, and mirrored files that do not
contain the version. Fix the cause — usually a double bump or a forgotten
sync file. If the state is intended (e.g. a deliberate jump), tell the owner
instead of changing it.

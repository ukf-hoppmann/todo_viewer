# Backlog and memos between the cloud and the local viewer

How the backlog and the memos travel between a cloud session (files in the
repository, backend `files`) and the local ToDo-Viewer (database, backend
`api`). Read it when the owner prepares a cloud session, brings its branch back,
or asks why the viewer and the files differ. The rules of the two backends
stay as they are: [SKILL.md](SKILL.md) (backlog), [memos.md](memos.md) and
[memos-files.md](memos-files.md) (memos).

## How it fits together

- Locally the AI works only through the viewer's API. The viewer keeps the
  truth in its database and mirrors it into the backlog folder (`todo.path`,
  for example `docs/todo`: `TODO.md`, `archive.md`, `items/`, `memos/`, `mindmap/`). The
  mirror is how the state gets into Git.
- A cloud session cannot reach the viewer. It clones the repository, works on
  the mirror files (backend `files`, chosen automatically in the cloud) and
  leaves its changes on its own branch (`claude/<name>`).
- Git carries the files, the viewer's sync carries them into the database. The
  viewer, not the AI, decides what is a conflict.

## Prerequisites

- The backlog is registered in the viewer with a mirror folder: the backlog
  folder of the repository in the main checkout. `backlog_api.py sources`
  shows it (`Project | Folder`); exit code 4 means it is not registered
  ([api.md](api.md)).
- Auto-sync is on for the project ("On, sync automatically" in the viewer's
  project settings). The viewer then checks every 30 seconds and takes over a
  change when it is the same in two checks, so a change shows up after about a
  minute. Without auto-sync the owner starts the sync in the viewer's sync
  dialog; the AI never starts or decides a sync.
- The whole backlog folder (`TODO.md`, `archive.md`, `items/`, `memos/`, `mindmap/`) is
  committed to the repository. The cloud reads only what Git holds.

## Before the cloud session (local)

1. Let the viewer finish: no open conflicts in the viewer, and the last change
   older than a minute. You cannot see this through the API: ask the owner when
   in doubt.
2. Commit the backlog folder in the main checkout, `memos/` and `mindmap/` included, with a
   message `Backlog: …` ([SKILL.md](SKILL.md), committing backlog changes).
3. The owner pushes `main`. You never push. A cloud session started before the
   push works on old files.

## In the cloud session

- The backend is `files`: edit `TODO.md`, `archive.md`, `items/`, `memos/`, and `mindmap/`
  directly and follow [format.md](format.md) and [memos-files.md](memos-files.md);
  the checks at the end of a turn tell you what is wrong.
- A new item gets a placeholder `NEW-<name>`, a new memo `new-<name>.md`.
  Labels and uids come from the viewer's sync. Never write a label (the "next
  free number") or a `Uid` for a new entry yourself. That is what keeps parallel
  work safe: the viewer matches entries by `Uid`, so a session in the cloud and
  the local viewer that both create an item never collide; each placeholder
  becomes the next free label at the sync. An entry with a label but without a
  `Uid` is refused by the check at the end of your turn (`missing required
  field: Uid`) and by the viewer's sync (`missing_field`); a placeholder with a
  `Uid` is refused as well. Two placeholders with the same name in one backlog
  are refused too (`invalid_placeholder`): pick a name that is specific to the
  item.
- The changes to the backlog and the memos belong to the change and are
  committed on the session's branch like any other file.

## Back to the viewer (local)

1. **Branch to `main`.** The standard way is a pull request on GitHub, merged
   there. The alternative is local: `git fetch`, then merge
   `origin/claude/<name>` into `main`. The AI does not merge a pull request.
2. **Prepare the main checkout.** Commit what the API has written since the
   last commit (`Backlog: …`), then `git pull`. Without that commit the pull
   stops when the incoming change touches a changed backlog file. Text
   conflicts in the backlog files are resolved like any merge conflict; the
   owner decides when it is not obvious which side is right.
3. **Sync.** The viewer takes the files over at its next check, or the owner
   starts the sync dialog. Changes that touch different entries merge by
   themselves. Entries changed on both sides (`both_changed`, `both_created`)
   and entries missing on one side (`deleted_in_files`, `deleted_in_database`)
   stay open until the owner decides in the dialog for the database, for the
   files, or to defer. Do not decide this for the owner and do not delete
   anything to make it go away.
4. **When the sync pauses.** The auto-sync stops while a file contains Git
   merge markers (`<<<<<<<` and `>>>>>>>` at the start of a line), the folder
   is missing or unreadable, or a Git operation is running (lock file). Resolve
   the markers first (on the owner's request), finish the Git operation, then
   the next good check resumes it. A format error in `memos/` aborts the sync
   with an error code (for example `invalid_value`) naming file and line; it changes nothing
   until the file is fixed (`memos_files.py <backlog folder> --check`).
5. **Afterwards.** Placeholders now have labels and uids, files were renamed
   (`new-<name>.md` became `MEMO-<n>.md`, `NEW-<name>` became an item label).
   Read the state again through the API; do not rely on names you wrote in the
   cloud.

## Memos in the repository

With a mirror, the viewer writes `memos/` into the backlog folder, so the
memos are in Git, and in a cloud session on GitHub, whether the memos came from
the database or from files. They are not private any more; keep to
[memos-files.md](memos-files.md) on what does not belong in them. In API mode
the AI still writes memos only through `memos_api.py`, never into the files,
and commits the folder together with the rest of the backlog.

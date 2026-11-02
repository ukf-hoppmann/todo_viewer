"""Work on a backlog through the ToDo-Viewer's HTTP API (todo.backend = "api").

Usage: backlog_api.py [--project <name>] <command> [arguments]; see USAGE.
The backlog comes from the harness config of the session's project, never from a path argument.
"""
from __future__ import annotations

import re
import sys
from collections.abc import Callable
from typing import Any
from urllib.parse import quote

from notes_hint import child_in_progress_hint
from viewer_api import (
    EXIT_USAGE, NO_PARENT, Api, ApiError, Target, find_project, item_fields, print_json, print_projects,
    register_project, split_target, stdin_json, target_for, version_arg,
)

USAGE = """usage: backlog_api.py [--project <name> | --source <name>] <command> [arguments]
  --project <name>                        a registered subproject; default: the root project
  --source <name>                         another project's backlog by its exact name from 'sources'
                                          (only with the owner's explicit approval, see skill todo)
  health                                  server reachable?
  sources                                 the names of all projects the viewer knows, with their folders
  register                                register this backlog as a viewer project (only after the owner's yes)
  index [--with-trash]                    one line per item: ID | Type | Status | Area | Title | Parent;
                                          items in the trash are left out, or marked (Papierkorb) with --with-trash
  show <ID>                               item as JSON, with its version (archived items too); deleted children
                                          are marked and do not count as open work
  areas                                   the areas in use, one per line
  create                                  stdin: JSON fields (type, title, area, goal, completion_criteria, ...)
  update <ID> <version>                   stdin: JSON {"fields": {...}, "resolution": ...}
  move <ID> <version> <parent|-> [--position N]   new parent ('-' = no parent) and position among siblings
  reopen <ID>                             reopen the item and its closed ancestors (In progress)
  note <ID>                               stdin: JSON {"topic", "discussed", "decided", "open", "summary",
                                          "state", "state_version"} (state = new head, with state_version
                                          when the notes have a head)
  state <ID>                              the head (## State) of the item's notes without the log: content,
                                          stamp, state (current|stale|missing), checksum, last_entry, version
  put-state <ID> <version>                stdin: the complete new head (without heading and stamp); the server stamps it
  confirm-state <ID> <version>            the head is still current: only the stamp is renewed
  entries <ID> [--last N]                 the log entries (all, or the last N): position, day, topic, text
  doc <ID> <name>                         print a notes/spec document: 'version: <v>', blank line, content
  put-doc <ID> <name> <version|new> [--summary TEXT]   stdin: the complete new document text
  delete-doc <ID> <name> <version>        move a notes or spec document to the trash; with the notes go their head
                                          and the item's summary
  retype <ID> <version> <type>            change the type (Epic|Story|Task); the item gets a new ID
  delete <ID> <version> [--cascade]       move to the trash (with --cascade including descendants)
  trash                                   backlog items and deleted documents (kind 'document', with their 'uid') in
                                          the trash as JSON
  restore <ID|trash uid>                  restore an item (with the descendants deleted with it) or a deleted document
                                          (by the 'uid' that 'trash' shows) from the trash"""

BACKLOG_KINDS = ("epic", "story", "task")
#: What the trash lists besides the items: a notes or spec document that was deleted from an item.
DOCUMENT_KIND = "document"
LABEL = re.compile(r"[A-Z]+-\d+")
TRASH_MARK = "(Papierkorb)"
CLOSED_STATUSES = ("Completed", "Rejected")


def _item(identifier: str, suffix: str = "") -> str:
    return f"/backlog/items/{quote(identifier)}{suffix}"


def _trashed(api: Api, project: str) -> list[dict[str, Any]]:
    elements = api.call("GET", "/workspace/trash", query={"projects": project})
    return [e for e in elements if e.get("kind") in BACKLOG_KINDS]


def _index_text(text: str, trashed: set[str], with_trash: bool) -> str:
    """The index without the trashed items, or with them marked; the header line stays."""
    lines = []
    for line in text.splitlines():
        columns = [c.strip() for c in line.split("|")]
        if columns[0] in trashed:
            if not with_trash:
                continue
            line = f"{line} {TRASH_MARK}"
        lines.append(line)
    return "\n".join(lines)


def _mark_trashed_children(item: dict[str, Any]) -> list[str]:
    """Mark deleted children (they are not open work); returns the labels of those still unclosed."""
    unclosed = []
    for child in item.get("children") or []:
        if child.get("deleted"):
            child["note"] = "im Papierkorb; zählt nicht als offenes Kind"
            if child.get("status") not in CLOSED_STATUSES:
                unclosed.append(child.get("label", ""))
    return unclosed


def _hint_children_in_progress(api: Api, project: str, identifier: str) -> None:
    """After notes were written: ask on stderr whether they belong to a child in progress. Never fails the call."""
    try:
        item = api.call("GET", _item(identifier), query={"project": project})
    except ApiError:
        return
    active = [c.get("label", "") for c in item.get("children") or []
              if c.get("status") == "In progress" and not c.get("deleted")]
    hint = child_in_progress_hint(identifier, str(item.get("type", "")), active)
    if hint:
        print(hint, file=sys.stderr)


def _options(command: str, args: list[str]) -> tuple[list[str], dict[str, str | bool]]:
    """Positional arguments and the command's options (flags or options with a value)."""
    allowed = {"put-doc": {"--summary": False}, "entries": {"--last": False}, "delete": {"--cascade": True}, "index": {"--with-trash": True}, "move": {"--position": False}}
    flags = allowed.get(command, {})
    positional: list[str] = []
    options: dict[str, str | bool] = {}
    rest = iter(args)
    for arg in rest:
        if arg not in flags:
            positional.append(arg)
        elif flags[arg]:
            options[arg] = True
        else:
            value = next(rest, None)
            if value is None:
                raise ApiError(f"{arg} needs a value", EXIT_USAGE)
            options[arg] = value
    return positional, options


ARITY = {"health": 0, "sources": 0, "register": 0, "index": 0, "show": 1, "areas": 0, "create": 0, "update": 2,
         "move": 3, "reopen": 1, "note": 1, "state": 1, "put-state": 2, "confirm-state": 2, "entries": 1, "doc": 2, "put-doc": 3, "delete-doc": 3, "retype": 3, "delete": 2, "trash": 0,
         "restore": 1}
# Position of the <version> argument per command.
VERSION_AT = {"update": 1, "move": 1, "put-state": 1, "confirm-state": 1, "put-doc": 2, "delete-doc": 2, "retype": 1, "delete": 1}


def run(project_name: str, source_name: str | None, command: str, args: list[str]) -> None:
    positional, options = _options(command, args)
    if command not in ARITY or len(positional) != ARITY[command]:
        raise ApiError(USAGE, EXIT_USAGE)
    # A wrong version is a wrong call: refuse it before anything reaches the server.
    at = VERSION_AT.get(command)
    if at is not None and not (command == "put-doc" and positional[at] == "new"):
        version_arg(positional[at])
    project = find_project(project_name)
    api = Api(project.config.todo_api_url)
    if command == "health":
        print_json(api.call("GET", "/core/health"))
        return
    if command == "sources":
        print_projects(api)
        return
    if command == "register":
        if source_name is not None:
            raise ApiError("register works only on the session's own backlog", EXIT_USAGE)
        record = register_project(api, project)
        print(f"registered as viewer project {record['name']!r} (uid {record['uid']})")
        return
    target = target_for(api, project, source_name)
    _run(target, command, positional, options, _reporter(source_name))


NOTES_STATES = ("current", "stale", "missing")
_STATE_HINTS = {"notes_state_stale": "stale", "notes_state_missing": "missing"}


def _reporter(source_name: str | None) -> Callable[..., None]:
    """Machine-readable lines for the PostToolUse hook (mark_notes_state.py), which reads them from the Bash answer.

    `[harness] notes-state <ID> <state>` after a write on an item's notes, `[harness] active <ID>` when the session
    starts working on an item. Only the session's own backlog counts: nothing for another project (`--source`).
    The helper stores nothing; the hook runs in the right data folder with the right session.
    """

    def report(kind: str, identifier: str, answer: Any = None) -> None:
        if source_name is not None:
            return
        line = f"active {identifier}" if kind == "active" else f"notes-state {identifier} {_notes_state(answer)}"
        print(f"[harness] {line}", file=sys.stderr)

    return report


def _notes_state(answer: Any) -> str:
    """The state of the notes head after a write: from the answer, else from its hints (no hint: current)."""
    if not isinstance(answer, dict):
        return "current"
    for key in ("notes_state", "state"):
        if answer.get(key) in NOTES_STATES:
            return str(answer[key])
    for hint in answer.get("hints") or []:
        if isinstance(hint, dict) and hint.get("code") in _STATE_HINTS:
            return _STATE_HINTS[hint["code"]]
    return "current"


def _print_hints(answer: Any) -> None:
    """The server's hints on a notes write, one line each on stderr; they never fail the call."""
    for hint in (answer.get("hints") if isinstance(answer, dict) else None) or []:
        print(f"hint: {hint.get('message', hint.get('code', ''))}", file=sys.stderr)


def _notes_call(api: Api, method: str, path: str, body: Any = None, query: dict[str, str] | None = None) -> Any:
    """A call on the notes head; an older viewer without it answers 404."""
    try:
        return api.call(method, path, body, query)
    except ApiError as exc:
        if str(exc).startswith("HTTP 404"):
            raise ApiError("the ToDo-Viewer does not support the notes head (needs v0.9.0 or later); "
                           f"work on the notes with note and put-doc.\n{exc}") from exc
        raise


def _run(target: Target, command: str, positional: list[str], options: dict[str, str | bool],
         report: Callable[..., None]) -> None:
    api, project = target.api, target.uid
    if command == "index":
        text = api.call("GET", "/backlog/index", query={"projects": project})["text"]
        trashed = {e.get("label", "") for e in _trashed(api, project)}
        print(_index_text(text, trashed, bool(options.get("--with-trash"))))
    elif command == "show":
        item = api.call("GET", _item(positional[0]), query={"project": project})
        unclosed = _mark_trashed_children(item)
        print_json(item)
        if unclosed:
            print(f"hint: {', '.join(unclosed)} liegt im Papierkorb, ist aber nicht geschlossen; "
                  "gelöschte Kinder zählen nicht für Fortschritt und Abschluss, sie blockieren nichts.",
                  file=sys.stderr)
    elif command == "areas":
        print("\n".join(api.call("GET", "/backlog/areas", query={"project": project})["areas"]))
    elif command == "create":
        fields = stdin_json()
        item_type = fields.pop("type", None)
        body = {"project": project, "type": item_type, "fields": item_fields(target, fields)}
        print_json(api.call("POST", "/backlog/items", body))
    elif command == "update":
        identifier, version = positional[0], version_arg(positional[1])
        data = stdin_json()
        body: dict[str, Any] = {"project": project, "version": version,
                                "fields": item_fields(target, data.get("fields") or {})}
        if "resolution" in data:
            body["resolution"] = data["resolution"]
        print_json(api.call("PUT", _item(identifier), body))
        if body["fields"].get("status") == "In progress":
            report("active", identifier)
    elif command == "move":
        identifier, version, parent = positional[0], version_arg(positional[1]), positional[2]
        body = {"project": project, "version": version,
                "parent": None if parent in NO_PARENT else target.resolve(parent)}
        if "--position" in options:
            body["position"] = version_arg(str(options["--position"]))
        print_json(api.call("POST", _item(identifier, "/move"), body))
    elif command == "reopen":
        print_json(api.call("POST", _item(positional[0], "/reopen"), {"project": project}))
        report("active", positional[0])
    elif command == "note":
        answer = api.call("POST", _item(positional[0], "/notes"), {**stdin_json(), "project": project})
        print_json(answer)
        _print_hints(answer)
        report("notes", positional[0], answer)
        _hint_children_in_progress(api, project, positional[0])
    elif command == "state":
        print_json(_notes_call(api, "GET", _item(positional[0], "/notes/state"), query={"project": project}))
    elif command == "entries":
        query = {"project": project}
        if "--last" in options:
            query["last"] = str(version_arg(str(options["--last"])))
        print_json(_notes_call(api, "GET", _item(positional[0], "/notes/entries"), query=query))
    elif command == "put-state":
        body = {"project": project, "content": sys.stdin.read(), "version": version_arg(positional[1])}
        answer = _notes_call(api, "PUT", _item(positional[0], "/notes/state"), body)
        print_json(answer)
        _print_hints(answer)
        report("notes", positional[0], answer)
    elif command == "confirm-state":
        body = {"project": project, "version": version_arg(positional[1])}
        answer = _notes_call(api, "POST", _item(positional[0], "/notes/state/confirm"), body)
        print_json(answer)
        _print_hints(answer)
        report("notes", positional[0], answer)
    elif command == "doc":
        identifier, name = positional
        document = api.call("GET", _item(identifier, f"/documents/{quote(name)}"), query={"project": project})
        sys.stdout.write(f"version: {document['version']}\n\n{document['content']}")
        if name.endswith("_spec.md"):
            report("active", identifier)
    elif command == "put-doc":
        identifier, name, version = positional
        body = {"project": project, "content": sys.stdin.read(),
                "version": None if version == "new" else version_arg(version)}
        if "--summary" in options:
            body["summary"] = options["--summary"]
        document = api.call("PUT", _item(identifier, f"/documents/{quote(name)}"), body)
        print(f"{document['name']}: saved, version {document['version']}")
        if name.endswith("_notes.md"):
            _print_hints(document)
            report("notes", identifier, document)
            _hint_children_in_progress(api, project, identifier)
    elif command == "delete-doc":
        identifier, name, version = positional
        query = {"project": project, "version": str(version_arg(version))}
        print_json(api.call("DELETE", _item(identifier, f"/documents/{quote(name)}"), query=query))
    elif command == "retype":
        identifier, version, new_type = positional
        body = {"project": project, "version": version_arg(version), "type": new_type}
        print_json(api.call("POST", _item(identifier, "/retype"), body))
    elif command == "delete":
        identifier, version = positional
        query = {"version": str(version_arg(version)), **({"cascade": "true"} if options.get("--cascade") else {})}
        print_json(api.call("DELETE", f"/workspace/elements/{quote(target.resolve(identifier))}", query=query))
    elif command == "trash":
        elements = api.call("GET", "/workspace/trash", query={"projects": project})
        print_json([e for e in elements if e.get("kind") in (*BACKLOG_KINDS, DOCUMENT_KIND)])
    elif command == "restore":
        identifier = positional[0]
        uid = target.resolve(identifier) if LABEL.fullmatch(identifier) else identifier
        print_json(api.call("POST", "/workspace/trash/restore", {"uids": [uid]}))


def main(argv: list[str]) -> int:
    args = argv[1:]
    try:
        project_name, source_name, args = split_target(args)
        if not args:
            print(USAGE, file=sys.stderr)
            return EXIT_USAGE
        run(project_name, source_name, args[0], args[1:])
    except ApiError as exc:
        print(exc if exc.exit_code == EXIT_USAGE and str(exc) == USAGE else f"error: {exc}", file=sys.stderr)
        return exc.exit_code
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

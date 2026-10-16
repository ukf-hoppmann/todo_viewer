"""Work on notes and topics through the ToDo-Viewer's HTTP API (part of the todo module).

Usage: notes_api.py [--project <name>] <command> [arguments]; see USAGE.
The project and the server come from the harness config of the session's project, never from a path argument.
Notes live only in the viewer's database: there is no file access, and no command removes anything for good.
"""
from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from viewer_api import (
    EXIT_USAGE, Api, ApiError, find_project, named_source, print_json, print_sources, source_folder,
    source_record, split_target, stdin_json,
)

USAGE = """usage: notes_api.py [--project <name> | --source <name>] <command> [arguments]
  --project <name>                        a registered subproject; default: the root project
  --source <name>                         another project's notes by its exact name from 'sources'
                                          (only with the owner's explicit approval, see skill todo, notes.md)
  health                                  server reachable?
  sources                                 the names of all projects the viewer knows, with their folders
Reading (labels are NOTE-001 / TOPIC-001; the lean index comes first, then the one note you need):
  index [--topic L] [--status S] [--due] [--archived] [--linked-item ID] [--all-projects]
                                          lean index: topics and notes without long texts
  due                                     all due notes of all projects with reason, triggers, actions
  show <NOTE>                             one note as JSON with its version, triggers, open notices
  topics [--deleted]                      topics of the project as JSON
  topic <TOPIC>                           one topic as JSON
  links <NOTE> | backlinks <NOTE>         links of a note | notes pointing to it
  notes-of-item <ID> | notes-of-topic <TOPIC>   notes that point to a backlog item | sit in a topic
  docs <NOTE>                             long-form documents of a note
  doc <NOTE> <name>                       print a document: 'version: <v>', blank line, content
  notices <NOTE|ITEM-ID> [--side note|item] [--open]   notices about changed links of one note (default) or item
  trash                                   topics and notes in the trash as JSON
  settings                                max_topic_depth and review_days (read only)
Writing (JSON on stdin; a note's <version> is the one you read last):
  create                                  {summary, body?, topic?, review_at?, trigger_mode?}
  update <NOTE> <version>                 {summary?, body?, topic?, review_at?, trigger_mode?}; null clears
  keep <NOTE> <version>                   keep it: only the review date moves on
  snooze <NOTE> <version>                 optional {review_at?, trigger?}: wait again
  finish <NOTE> <version> <done|dropped>  close it into the archive
  move <NOTE> <version> <project> [--topic L]   move to another project (new label, old one to the trash)
  delete <NOTE> | restore <NOTE>          to the trash | back from the trash or archive
  trigger-add <NOTE>                      {kind: time|event|topic_due, at?, target?, target_project?, target_status?}
  trigger-remove <NOTE> <trigger-id>
  link-add <NOTE>                         {kind: item|topic|note, target, target_project?, role?: reference|origin}
  link-remove <NOTE> <link-id>
  put-doc <NOTE> <name> <version|new>    stdin: the complete document text
  note-entry <NOTE>                       dated entry {topic, discussed?, decided?, open?}
  decide <notice-id>                      {decision: keep|detach|drop|promote|acknowledge, version?, promotion?}
  promote <NOTE>                          {version, item_type, area, goal, completion_criteria, title?, ...}
  demote <ITEM-ID>                        {version, topic?}: an open item without children becomes a note
  topic-create                            {name, parent?, due_at?}
  topic-update <TOPIC>                    {name?, due_at?}; due_at null removes the date
  topic-move <TOPIC>                      {parent}; null moves to the top
  topic-delete <TOPIC> [--cascade]        to the trash (a topic with content needs --cascade)
  topic-restore <TOPIC>"""


@dataclass
class Context:
    api: Api
    project: str
    source_id: str
    positional: list[str]
    options: dict[str, str | bool]

    def path(self, suffix: str) -> str:
        return f"/projects/{quote(self.project)}{suffix}"

    def note(self, suffix: str = "") -> str:
        return self.path(f"/notes/{quote(self.positional[0])}{suffix}")

    def topic(self, suffix: str = "") -> str:
        return self.path(f"/topics/{quote(self.positional[0])}{suffix}")

    def call(self, method: str, path: str, body: Any = None, query: dict[str, str] | None = None) -> None:
        print_json(self.api.call(method, path, body, query))


@dataclass
class Command:
    positional: int
    handler: Callable[[Context], None]
    # Option name -> True for a flag, False for an option with a value.
    options: dict[str, bool] | None = None


def _index(ctx: Context) -> None:
    query: dict[str, str] = {}
    if not ctx.options.get("--all-projects"):
        query["project"] = ctx.project
    for option, name in (("--topic", "topic"), ("--status", "status"), ("--linked-item", "linked_item")):
        if option in ctx.options:
            query[name] = str(ctx.options[option])
    for option, name in (("--due", "due"), ("--archived", "archived")):
        if ctx.options.get(option):
            query[name] = "true"
    index = ctx.api.call("GET", "/notes/index", query=query)
    show_project = bool(ctx.options.get("--all-projects"))
    print("Topics: Label | Path | Due at | Due | Notes")
    for topic in index["topics"]:
        prefix = f"{topic['project']} " if show_project else ""
        print(f"{prefix}{topic['label']} | {' / '.join(topic['path'])} | {topic['due_at'] or '-'} "
              f"| {'yes' if topic['due'] else 'no'} | {topic['note_count']}")
    print("Notes: Label | Status | Reason | Review at | Topic | Summary")
    for note in index["notes"]:
        prefix = f"{note['project']} " if show_project else ""
        print(f"{prefix}{note['label']} | {note['status']} | {note['reason'] or '-'} | {note['review_at'] or '-'} "
              f"| {note['topic'] or '-'} | {note['summary']}")


def _finish(ctx: Context) -> None:
    label, version, status = ctx.positional
    if status not in ("done", "dropped"):
        raise ApiError("finish needs the status done or dropped", EXIT_USAGE)
    ctx.call("POST", ctx.path(f"/notes/{quote(label)}/finish"), {"version": version, "status": status})


def _snooze(ctx: Context) -> None:
    ctx.call("POST", ctx.note("/snooze"), {"version": ctx.positional[1], **stdin_json(required=False)})


def _move(ctx: Context) -> None:
    label, version, target = ctx.positional
    body: dict[str, Any] = {"version": version, "project": target}
    if "--topic" in ctx.options:
        body["topic"] = ctx.options["--topic"]
    ctx.call("POST", ctx.path(f"/notes/{quote(label)}/move"), body)


def _doc(ctx: Context) -> None:
    label, name = ctx.positional
    document = ctx.api.call("GET", ctx.path(f"/notes/{quote(label)}/documents/{quote(name)}"))
    sys.stdout.write(f"version: {document['version']}\n\n{document['content']}")


def _put_doc(ctx: Context) -> None:
    label, name, version = ctx.positional
    body = {"content": sys.stdin.read(), "version": None if version == "new" else version}
    document = ctx.api.call("PUT", ctx.path(f"/notes/{quote(label)}/documents/{quote(name)}"), body)
    print(f"{document['name']}: saved, version {document['version']}")


def _notices(ctx: Context) -> None:
    query = {"project": ctx.project, "label": ctx.positional[0]}
    if "--side" in ctx.options:
        query["side"] = str(ctx.options["--side"])
    if ctx.options.get("--open"):
        query["open"] = "true"
    ctx.call("GET", "/notices", query=query)


def _demote(ctx: Context) -> None:
    ctx.call("POST", f"/items/{quote(ctx.source_id)}/{quote(ctx.positional[0])}/demote", stdin_json())


def _topic_delete(ctx: Context) -> None:
    query = {"cascade": "true"} if ctx.options.get("--cascade") else None
    ctx.call("DELETE", ctx.topic(), query=query)


COMMANDS: dict[str, Command] = {
    "index": Command(0, _index, {"--topic": False, "--status": False, "--linked-item": False, "--due": True,
                                 "--archived": True, "--all-projects": True}),
    "due": Command(0, lambda c: c.call("GET", "/notes/due")),
    "show": Command(1, lambda c: c.call("GET", c.note())),
    "topics": Command(0, lambda c: c.call("GET", c.path("/topics"),
                                          query={"include_deleted": "true"} if c.options.get("--deleted") else None),
                      {"--deleted": True}),
    "topic": Command(1, lambda c: c.call("GET", c.topic())),
    "links": Command(1, lambda c: c.call("GET", c.note("/links"))),
    "backlinks": Command(1, lambda c: c.call("GET", c.note("/backlinks"))),
    "notes-of-item": Command(1, lambda c: c.call("GET", c.path(f"/items/{quote(c.positional[0])}/notes"))),
    "notes-of-topic": Command(1, lambda c: c.call("GET", c.topic("/notes"))),
    "docs": Command(1, lambda c: c.call("GET", c.note("/documents"))),
    "doc": Command(2, _doc),
    "notices": Command(1, _notices, {"--side": False, "--open": True}),
    "trash": Command(0, lambda c: c.call("GET", c.path("/trash"))),
    "settings": Command(0, lambda c: c.call("GET", "/notes/settings")),
    "create": Command(0, lambda c: c.call("POST", c.path("/notes"), stdin_json())),
    "update": Command(2, lambda c: c.call("PATCH", c.note(), {"version": c.positional[1], **stdin_json()})),
    "keep": Command(2, lambda c: c.call("POST", c.note("/keep"), {"version": c.positional[1]})),
    "snooze": Command(2, _snooze),
    "finish": Command(3, _finish),
    "move": Command(3, _move, {"--topic": False}),
    "delete": Command(1, lambda c: c.call("DELETE", c.note())),
    "restore": Command(1, lambda c: c.call("POST", c.note("/restore"))),
    "trigger-add": Command(1, lambda c: c.call("POST", c.note("/triggers"), stdin_json())),
    "trigger-remove": Command(2, lambda c: c.call("DELETE", c.note(f"/triggers/{quote(c.positional[1])}"))),
    "link-add": Command(1, lambda c: c.call("POST", c.note("/links"), stdin_json())),
    "link-remove": Command(2, lambda c: c.call("DELETE", c.note(f"/links/{quote(c.positional[1])}"))),
    "put-doc": Command(3, _put_doc),
    "note-entry": Command(1, lambda c: c.call("POST", c.note("/notes"), stdin_json())),
    "decide": Command(1, lambda c: c.call("POST", f"/notices/{quote(c.positional[0])}/decision", stdin_json())),
    "promote": Command(1, lambda c: c.call("POST", f"/notes/{quote(c.project)}/{quote(c.positional[0])}/promote",
                                           stdin_json())),
    "demote": Command(1, _demote),
    "topic-create": Command(0, lambda c: c.call("POST", c.path("/topics"), stdin_json())),
    "topic-update": Command(1, lambda c: c.call("PATCH", c.topic(), stdin_json())),
    "topic-move": Command(1, lambda c: c.call("POST", c.topic("/move"), stdin_json())),
    "topic-delete": Command(1, _topic_delete, {"--cascade": True}),
    "topic-restore": Command(1, lambda c: c.call("POST", c.topic("/restore"))),
}


def _split(command: Command, args: list[str]) -> tuple[list[str], dict[str, str | bool]]:
    allowed = command.options or {}
    positional: list[str] = []
    options: dict[str, str | bool] = {}
    iterator = iter(args)
    for arg in iterator:
        if not arg.startswith("--"):
            positional.append(arg)
        elif arg not in allowed:
            raise ApiError(USAGE, EXIT_USAGE)
        elif allowed[arg]:
            options[arg] = True
        else:
            value = next(iterator, None)
            if value is None:
                raise ApiError(f"{arg} needs a value", EXIT_USAGE)
            options[arg] = value
    if len(positional) != command.positional:
        raise ApiError(USAGE, EXIT_USAGE)
    return positional, options


def run(project_name: str, source_name: str | None, name: str, args: list[str]) -> None:
    local = {"health", "sources"}
    if name not in local and name not in COMMANDS:
        raise ApiError(USAGE, EXIT_USAGE)
    command = Command(0, lambda c: None) if name in local else COMMANDS[name]
    positional, options = _split(command, args)
    project = find_project(project_name, "todo")
    if not project.config.notes_enabled():
        raise ApiError(
            f"notes need todo.backend = \"api\" in project {project.name}: they live only in the ToDo-Viewer",
            EXIT_USAGE,
        )
    api = Api(project.config.todo_api_url)
    if name == "health":
        print_json(api.call("GET", "/health"))
        return
    if name == "sources":
        print_sources(api)
        return
    # The notes of a project are addressed by the project name the viewer knows its backlog by.
    if source_name is not None:
        record = named_source(api, source_name)
    else:
        record = source_record(api, source_folder(project), project)
    command.handler(Context(api, record["project"], record["id"], positional, options))


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

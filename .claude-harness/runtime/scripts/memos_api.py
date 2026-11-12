"""Work on memos and topics through the ToDo-Viewer's HTTP API (part of the todo module).

Usage: memos_api.py [--project <name>] <command> [arguments]; see USAGE.
The project and the server come from the harness config of the session's project, never from a path argument.
Memos live only in the viewer's database: there is no file access, and no command removes anything for good.
"""
from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from viewer_api import (
    EXIT_USAGE, Api, ApiError, Target, find_project, item_fields, named_target, print_json, print_projects,
    split_target, stdin_json, target_for, version_arg,
)

USAGE = """usage: memos_api.py [--project <name> | --source <name>] <command> [arguments]
  --project <name>                        a registered subproject; default: the root project
  --source <name>                         another project's memos by its exact name from 'sources'
                                          (only with the owner's explicit approval, see skill todo, memos.md)
  health                                  server reachable?
  sources                                 the names of all projects the viewer knows, with their folders
Reading (labels are MEMO-001 / TOPIC-001; the lean index comes first, then the one memo you need):
  index [--status S] [--due] [--archived] [--query Q] [--all-projects]
                                          lean index: topics and memos without long texts
  due                                     all due memos of all projects with reason, triggers, hints
  show <MEMO>                             one memo as JSON with its version, triggers, open hints
  topics                                  topics of the project as JSON
  topic <TOPIC>                           sub-topics and memos of one topic
  links <MEMO> | backlinks <MEMO>         links of a memo | elements pointing to it
  memos-of-item <ID>                      memos that point to a backlog item
  docs <MEMO>                             long-form documents of a memo
  doc <MEMO> <name>                       print a document: 'version: <v>', blank line, content
  hints <MEMO> | hints <ID> --side item   open hints of one memo | of one backlog item
  trash                                   topics and memos in the trash as JSON
  settings                                max_topic_depth and review_days (read only)
Writing (JSON on stdin; <version> is the number you read last):
  create                                  {summary, body?, topic?, review_at?, trigger_mode?}
  update <MEMO> <version>                 {summary?, body?, topic?, review_at?, trigger_mode?}; null clears
  keep <MEMO> <version>                   keep it: only the review date moves on
  snooze <MEMO> <version>                 optional {review_at?, trigger?}: wait again
  finish <MEMO> <version> <done|dropped>  close it into the archive
  move <MEMO> <version> <project> [--topic L]   move to another project (new label, old one to the trash)
  delete <MEMO> <version>                 to the trash
  restore <MEMO> <version>                back from the trash or the archive
  trigger-add <MEMO>                      {kind: event|topic_date, target?, target_project?, status?}
  trigger-remove <trigger-uid>
  link-add <MEMO>                         {target, target_project?, role?: reference|origin}
  link-remove <link-uid>
  put-doc <MEMO> <name> <version|new>    stdin: the complete document text
  memo-entry <MEMO>                       dated entry {topic, discussed?, decided?, open?}
  decide <hint-uid>                     {decision: keep|detach|drop|promote|acknowledge, version?, type?, fields?}
  promote <MEMO>                          {version, type, fields: {area, goal, completion_criteria, title?, ...}}
  demote <ITEM-ID>                        {version, topic?}: an open item without children becomes a memo
  topic-create                            {name, parent?, due_at?}
  topic-update <TOPIC> <version>          {name?, due_at?}; due_at null removes the date
  topic-move <TOPIC> <version>            {parent}; null moves to the top
  topic-archive <TOPIC> <version>         optional {keep_archived?, active_memos?: move|archive, move_to?}
  topic-reactivate <TOPIC> <version>
  topic-delete <TOPIC> <version>          to the trash; optional {keep_archived?, active_memos?: move|delete, move_to?}
  topic-restore <TOPIC>                   back from the trash"""

MEMO_KINDS = ("memo", "topic")
ARCHIVED = "done,dropped,promoted"
OPEN = "waiting,due,snoozed"
# Older names of trigger kinds and fields, still accepted.
TRIGGER_KIND_ALIASES = {"topic_due": "topic_date"}


@dataclass
class Context:
    target: Target
    positional: list[str]
    options: dict[str, str | bool]

    @property
    def api(self) -> Api:
        return self.target.api

    @property
    def project(self) -> str:
        return self.target.uid

    def version(self, at: int = 1) -> int:
        return version_arg(self.positional[at])

    def memo(self, suffix: str = "") -> str:
        return f"/memos/memos/{quote(self.positional[0])}{suffix}"

    def topic(self, suffix: str = "") -> str:
        return f"/memos/topics/{quote(self.positional[0])}{suffix}"

    def get(self, path: str, query: dict[str, str] | None = None) -> Any:
        return self.api.call("GET", path, query=query if query is not None else {"project": self.project})

    def post(self, path: str, body: dict[str, Any]) -> None:
        print_json(self.api.call("POST", path, {"project": self.project, **body}))

    def put(self, path: str, body: dict[str, Any]) -> None:
        print_json(self.api.call("PUT", path, {"project": self.project, **body}))

    def links(self, label: str) -> dict[str, Any]:
        return self.api.call("GET", f"/workspace/elements/{quote(self.target.resolve(label))}/links")


@dataclass
class Command:
    positional: int
    handler: Callable[[Context], None]
    # Option name -> True for a flag, False for an option with a value.
    options: dict[str, bool] | None = None
    # Positions of <version> arguments, checked before anything is sent.
    versions: tuple[int, ...] = ()


def _index(ctx: Context) -> None:
    query: dict[str, str] = {} if ctx.options.get("--all-projects") else {"projects": ctx.project}
    statuses = [str(ctx.options["--status"])] if "--status" in ctx.options else []
    if ctx.options.get("--due"):
        statuses.append("due")
    if ctx.options.get("--archived"):
        statuses.append(ARCHIVED)
    # Without a filter the server lists every status; the lean index shows open memos only.
    query["statuses"] = ",".join(statuses) if statuses else OPEN
    if "--query" in ctx.options:
        query["query"] = str(ctx.options["--query"])
    index = ctx.api.call("GET", "/memos/index/lines", query=query)
    print(f"Topics: {index['topics']}")
    print(f"Memos: {index['memos']}")


def _finish(ctx: Context) -> None:
    status = ctx.positional[2]
    if status not in ("done", "dropped"):
        raise ApiError("finish needs the status done or dropped", EXIT_USAGE)
    ctx.post(ctx.memo("/finish"), {"version": ctx.version(), "status": status})


def _move(ctx: Context) -> None:
    body: dict[str, Any] = {"version": ctx.version(), "target_project": named_target(ctx.api, ctx.positional[2]).uid}
    if "--topic" in ctx.options:
        body["topic"] = ctx.options["--topic"]
    ctx.post(ctx.memo("/move"), body)


def _delete(ctx: Context) -> None:
    uid = ctx.target.resolve(ctx.positional[0])
    print_json(ctx.api.call("DELETE", f"/workspace/elements/{quote(uid)}", query={"version": str(ctx.version())}))


def _restore(ctx: Context) -> None:
    """From the trash through workspace, from the archive through memos."""
    element = ctx.api.call(
        "GET", f"/workspace/projects/{quote(ctx.project)}/labels/{quote(ctx.positional[0])}"
    )
    if element.get("deleted"):
        print_json(ctx.api.call("POST", "/workspace/trash/restore", {"uids": [element["uid"]]}))
    else:
        ctx.post(ctx.memo("/restore"), {"version": ctx.version()})


def _untrash(ctx: Context) -> None:
    print_json(ctx.api.call("POST", "/workspace/trash/restore", {"uids": [ctx.target.resolve(ctx.positional[0])]}))


def _trigger_add(ctx: Context) -> None:
    body = stdin_json()
    kind = TRIGGER_KIND_ALIASES.get(body.get("kind"), body.get("kind"))
    if kind == "time":
        raise ApiError("time triggers are gone: set an alarm instead (alarms_api.py create, see skill todo, "
                       "alarms.md)", EXIT_USAGE)
    out: dict[str, Any] = {"kind": kind}
    status = body.get("status", body.get("target_status"))
    if status is not None:
        out["status"] = status
    if body.get("target") is not None:
        project = body.get("target_project")
        # The server resolves labels of the memo's own project; another project's item goes by its uid.
        out["target"] = body["target"] if not project else named_target(ctx.api, project).resolve(body["target"])
    ctx.post(ctx.memo("/triggers"), out)


def _link_add(ctx: Context) -> None:
    body = stdin_json()
    if not body.get("target"):
        raise ApiError("link-add needs a target label", EXIT_USAGE)
    project = body.get("target_project")
    owner = ctx.target if not project else named_target(ctx.api, project)
    link = {"from_uid": ctx.target.resolve(ctx.positional[0]), "to_uid": owner.resolve(body["target"]),
            "role": body.get("role", "reference")}
    print_json(ctx.api.call("POST", "/workspace/links", link))


def _memos_of_item(ctx: Context) -> None:
    print_json([e for e in ctx.links(ctx.positional[0])["incoming"] if e.get("kind") == "memo"])


def _doc(ctx: Context) -> None:
    document = ctx.get(ctx.memo(f"/documents/{quote(ctx.positional[1])}"))
    sys.stdout.write(f"version: {document['version']}\n\n{document['content']}")


def _put_doc(ctx: Context) -> None:
    name, version = ctx.positional[1], ctx.positional[2]
    body = {"project": ctx.project, "content": sys.stdin.read(),
            "version": None if version == "new" else version_arg(version)}
    document = ctx.api.call("PUT", ctx.memo(f"/documents/{quote(name)}"), body)
    print(f"{document['name']}: saved, version {document['version']}")


def _hints(ctx: Context) -> None:
    if ctx.options.get("--side") == "item":
        print_json(ctx.get(f"/memos/items/{quote(ctx.positional[0])}/hints"))
    elif ctx.options.get("--side", "memo") == "memo":
        print_json(ctx.get(ctx.memo()).get("hints", []))
    else:
        raise ApiError("--side is memo or item", EXIT_USAGE)


def _promote(ctx: Context) -> None:
    body = stdin_json()
    body["fields"] = item_fields(ctx.target, body.get("fields") or {})
    ctx.post(ctx.memo("/promote"), body)


def _trash(ctx: Context) -> None:
    elements = ctx.api.call("GET", "/workspace/trash", query={"projects": ctx.project})
    print_json([e for e in elements if e.get("kind") in MEMO_KINDS])


def _topics(ctx: Context) -> None:
    print_json(ctx.api.call("GET", "/memos/index", query={"projects": ctx.project})["topics"])


COMMANDS: dict[str, Command] = {
    "index": Command(0, _index, {"--status": False, "--due": True, "--archived": True, "--query": False,
                                 "--all-projects": True}),
    "due": Command(0, lambda c: print_json(c.api.call("GET", "/memos/due"))),
    "show": Command(1, lambda c: print_json(c.get(c.memo()))),
    "topics": Command(0, _topics),
    "topic": Command(1, lambda c: print_json(c.get(c.topic("/content")))),
    "links": Command(1, lambda c: print_json(c.links(c.positional[0])["outgoing"])),
    "backlinks": Command(1, lambda c: print_json(c.links(c.positional[0])["incoming"])),
    "memos-of-item": Command(1, _memos_of_item),
    "docs": Command(1, lambda c: print_json(c.get(c.memo("/documents")))),
    "doc": Command(2, _doc),
    "hints": Command(1, _hints, {"--side": False}),
    "trash": Command(0, _trash),
    "settings": Command(0, lambda c: print_json(c.api.call("GET", "/memos/settings"))),
    "create": Command(0, lambda c: c.post("/memos/memos", {"fields": stdin_json()})),
    "update": Command(2, lambda c: c.put(c.memo(), {"version": c.version(), "fields": stdin_json()}), versions=(1,)),
    "keep": Command(2, lambda c: c.post(c.memo("/keep"), {"version": c.version()}), versions=(1,)),
    "snooze": Command(2, lambda c: c.post(c.memo("/snooze"), {"version": c.version(), **stdin_json(required=False)}),
                      versions=(1,)),
    "finish": Command(3, _finish, versions=(1,)),
    "move": Command(3, _move, {"--topic": False}, versions=(1,)),
    "delete": Command(2, _delete, versions=(1,)),
    "restore": Command(2, _restore, versions=(1,)),
    "trigger-add": Command(1, _trigger_add),
    "trigger-remove": Command(1, lambda c: print_json(c.api.call("DELETE", f"/memos/triggers/{quote(c.positional[0])}"))),
    "link-add": Command(1, _link_add),
    "link-remove": Command(1, lambda c: print_json(c.api.call("DELETE", f"/workspace/links/{quote(c.positional[0])}"))),
    "put-doc": Command(3, _put_doc),
    "memo-entry": Command(1, lambda c: c.post(c.memo("/entries"), stdin_json())),
    "decide": Command(1, lambda c: print_json(
        c.api.call("POST", f"/memos/hints/{quote(c.positional[0])}/decide", stdin_json()))),
    "promote": Command(1, _promote),
    "demote": Command(1, lambda c: c.post(f"/memos/items/{quote(c.positional[0])}/demote", stdin_json())),
    "topic-create": Command(0, lambda c: c.post("/memos/topics", stdin_json())),
    "topic-update": Command(2, lambda c: c.put(c.topic(), {"version": c.version(), "fields": stdin_json()}),
                            versions=(1,)),
    "topic-move": Command(2, lambda c: c.post(c.topic("/move"), {"version": c.version(), **stdin_json()}),
                          versions=(1,)),
    "topic-archive": Command(2, lambda c: c.post(c.topic("/archive"),
                                                 {"version": c.version(), **stdin_json(required=False)}),
                             versions=(1,)),
    "topic-reactivate": Command(2, lambda c: c.post(c.topic("/reactivate"), {"version": c.version()}),
                                versions=(1,)),
    "topic-delete": Command(2, lambda c: c.post(c.topic("/delete"),
                                                {"version": c.version(), **stdin_json(required=False)}),
                            versions=(1,)),
    "topic-restore": Command(1, _untrash),
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
    if command.handler is _put_doc and positional[2] != "new":
        version_arg(positional[2])
    for at in command.versions:
        version_arg(positional[at])
    return positional, options


def run(project_name: str, source_name: str | None, name: str, args: list[str]) -> None:
    local = {"health", "sources"}
    if name not in local and name not in COMMANDS:
        raise ApiError(USAGE, EXIT_USAGE)
    command = Command(0, lambda c: None) if name in local else COMMANDS[name]
    positional, options = _split(command, args)
    project = find_project(project_name, "todo")
    if not project.config.viewer_memos_enabled():
        raise ApiError(
            f"memos need todo.backend = \"api\" in project {project.name}: they live only in the ToDo-Viewer",
            EXIT_USAGE,
        )
    api = Api(project.config.todo_api_url)
    if name == "health":
        print_json(api.call("GET", "/core/health"))
        return
    if name == "sources":
        print_projects(api)
        return
    command.handler(Context(target_for(api, project, source_name), positional, options))


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

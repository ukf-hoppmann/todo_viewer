"""Work on a backlog through the ToDo-Viewer's HTTP API (todo.backend = "api").

Usage: backlog_api.py [--project <name>] <command> [arguments]; see USAGE.
The backlog comes from the harness config of the session's project, never from a path argument.
"""
from __future__ import annotations

import sys
from typing import Any
from urllib.parse import quote

from viewer_api import (
    EXIT_USAGE, Api, ApiError, find_project, named_source, print_json, print_sources, source_folder,
    source_id, split_target, stdin_json,
)

USAGE = """usage: backlog_api.py [--project <name> | --source <name>] <command> [arguments]
  --project <name>                        a registered subproject; default: the root project
  --source <name>                         another project's backlog by its exact name from 'sources'
                                          (only with the owner's explicit approval, see skill todo)
  health                                  server reachable?
  sources                                 the names of all backlogs the viewer knows, with their folders
  index                                   one line per item: ID | Type | Status | Area | Title | Parent
  show <ID>                               item as JSON, with its version (archived items too)
  create                                  stdin: JSON fields (type, title, area, goal, completion_criteria, ...)
  update <ID> <version>                   stdin: JSON {"fields": {...}, "resolution": ...}
  note <ID>                               stdin: JSON {"topic", "discussed", "decided", "open", "summary"}
  doc <ID> <name>                         print a notes/spec document: 'version: <v>', blank line, content
  put-doc <ID> <name> <version|new> [--summary TEXT]   stdin: the complete new document text
  retype <ID> <version> <type>            change the type (Epic|Story|Task); the item gets a new ID
  delete <ID> <version> [--cascade]       move to the trash (with --cascade including descendants)
  trash                                   items in the trash as JSON
  restore <ID> <version>                  restore an item from the trash"""


def _item(sid: str, identifier: str, suffix: str = "") -> str:
    return f"/items/{quote(sid)}/{quote(identifier)}{suffix}"


def run(project_name: str, source_name: str | None, command: str, args: list[str]) -> None:
    arity = {"health": 0, "sources": 0, "index": 0, "show": 1, "create": 0, "update": 2, "note": 1, "doc": 2,
             "put-doc": 3, "retype": 3, "delete": 2, "trash": 0, "restore": 2}
    options = {"put-doc": "--summary", "delete": "--cascade"}
    flag = options.get(command)
    positional = list(args)
    option_value: str | bool | None = None
    if flag == "--cascade" and flag in positional:
        positional.remove(flag)
        option_value = True
    elif flag == "--summary" and flag in positional:
        at = positional.index(flag)
        if at + 1 >= len(positional):
            raise ApiError("--summary needs a text", EXIT_USAGE)
        option_value = positional[at + 1]
        del positional[at:at + 2]
    if command not in arity or len(positional) != arity[command]:
        raise ApiError(USAGE, EXIT_USAGE)
    project = find_project(project_name)
    api = Api(project.config.todo_api_url)
    if command == "health":
        print_json(api.call("GET", "/health"))
        return
    if command == "sources":
        print_sources(api)
        return
    if source_name is not None:
        sid = named_source(api, source_name)["id"]
    else:
        sid = source_id(api, source_folder(project), project)

    if command == "index":
        items = api.call("GET", "/index", query={"source_id": sid})["items"]
        print("ID | Type | Status | Area | Title | Parent")
        for item in items:
            print(f"{item['id']} | {item['type']} | {item['status']} | {item['area']} "
                  f"| {item['title']} | {item['parent'] or '-'}")
    elif command == "show":
        print_json(api.call("GET", _item(sid, positional[0])))
    elif command == "create":
        print_json(api.call("POST", "/items", {**stdin_json(), "source_id": sid}))
    elif command == "update":
        identifier, version = positional
        body = stdin_json()
        print_json(api.call("PATCH", _item(sid, identifier), {"version": version, **body}))
    elif command == "note":
        print_json(api.call("POST", _item(sid, positional[0], "/notes"), stdin_json()))
    elif command == "doc":
        identifier, name = positional
        document = api.call("GET", _item(sid, identifier, f"/documents/{quote(name)}"))
        sys.stdout.write(f"version: {document['version']}\n\n{document['content']}")
    elif command == "put-doc":
        identifier, name, version = positional
        body: dict[str, Any] = {"content": sys.stdin.read(), "version": None if version == "new" else version}
        if option_value is not None:
            body["summary"] = option_value
        document = api.call("PUT", _item(sid, identifier, f"/documents/{quote(name)}"), body)
        print(f"{document['name']}: saved, version {document['version']}")
    elif command == "retype":
        identifier, version, new_type = positional
        print_json(api.call("POST", _item(sid, identifier, "/retype"), {"version": version, "type": new_type}))
    elif command == "delete":
        identifier, version = positional
        query = {"version": version, **({"cascade": "true"} if option_value else {})}
        print_json(api.call("DELETE", _item(sid, identifier), query=query))
    elif command == "trash":
        print_json(api.call("GET", "/trash", query={"source_id": sid}))
    elif command == "restore":
        identifier, version = positional
        print_json(api.call("POST", f"/trash/{quote(sid)}/{quote(identifier)}/restore", {"version": version}))


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

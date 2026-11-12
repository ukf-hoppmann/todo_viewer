"""Work on alarms through the ToDo-Viewer's HTTP API (part of the todo module).

Usage: alarms_api.py [--project <name>] <command> [arguments]; see USAGE.
The project and the server come from the harness config of the session's project, never from a path argument.
An alarm fires in the viewer at its time, as long as the viewer runs; finished and expired ones are removed
by the viewer after 24 hours.
"""
from __future__ import annotations

import sys
from typing import Any
from urllib.parse import quote

from viewer_api import (
    EXIT_USAGE, Api, ApiError, Target, find_project, named_target, print_json, split_target, stdin_json, target_for,
    version_arg,
)

USAGE = """usage: alarms_api.py [--project <name> | --source <name>] <command> [arguments]
  --project <name>                        a registered subproject; default: the root project
  --source <name>                         another project's alarms by its exact name (owner's approval, skill todo)
  list [--due] [--all-projects]           alarms of the project as JSON (--due: only those ringing now)
  show <ALARM>                            one alarm with its version, targets, status
  create                                  stdin: {at, text?, targets?: [LABEL | project:LABEL, ...]}
  update <ALARM> <version>                stdin: any of {at, text, targets}; targets [] detaches all
  snooze <ALARM> <version> [--until T]    ring again later (default: in one hour)
  finish <ALARM> <version>                done
  reopen <ALARM> <version>                undo finish
  delete <ALARM> <version>                to the trash
  restore <ALARM>                         back from the trash"""

# Command -> (positional arguments, options: name -> True for a flag, False for one with a value).
COMMANDS: dict[str, tuple[int, dict[str, bool]]] = {
    "list": (0, {"--due": True, "--all-projects": True}), "show": (1, {}), "create": (0, {}), "update": (2, {}),
    "snooze": (2, {"--until": False}), "finish": (2, {}), "reopen": (2, {}), "delete": (2, {}), "restore": (1, {}),
}


def _split(name: str, args: list[str]) -> tuple[list[str], dict[str, str | bool]]:
    count, allowed = COMMANDS[name]
    positional: list[str] = []
    options: dict[str, str | bool] = {}
    rest = iter(args)
    for arg in rest:
        if not arg.startswith("--"):
            positional.append(arg)
        elif arg not in allowed:
            raise ApiError(USAGE, EXIT_USAGE)
        elif allowed[arg]:
            options[arg] = True
        else:
            value = next(rest, None)
            if value is None:
                raise ApiError(f"{arg} needs a value", EXIT_USAGE)
            options[arg] = value
    if len(positional) != count:
        raise ApiError(USAGE, EXIT_USAGE)
    if count == 2:
        version_arg(positional[1])
    return positional, options


def _targets(target: Target, fields: dict[str, Any]) -> dict[str, Any]:
    """Own labels go to the server as they are; `project:LABEL` of another project goes by its uid."""
    if not isinstance(fields.get("targets"), list):
        return fields
    out = []
    for ref in fields["targets"]:
        project, _, label = str(ref).rpartition(":")
        out.append(named_target(target.api, project).resolve(label) if project else ref)
    return {**fields, "targets": out}


def _alarm(label: str, suffix: str = "") -> str:
    return f"/alarms/alarms/{quote(label)}{suffix}"


def _run(target: Target, name: str, positional: list[str], options: dict[str, str | bool]) -> None:
    api, project = target.api, target.uid
    version = version_arg(positional[1]) if len(positional) == 2 else None
    if name == "list":
        query = {} if options.get("--all-projects") else {"projects": project}
        if options.get("--due"):
            query["due_only"] = "true"
        print_json(api.call("GET", "/alarms/alarms", query=query))
    elif name == "show":
        print_json(api.call("GET", _alarm(positional[0]), query={"project": project}))
    elif name == "create":
        print_json(api.call("POST", "/alarms/alarms", {"project": project, "fields": _targets(target, stdin_json())}))
    elif name == "update":
        body = {"project": project, "version": version, "fields": _targets(target, stdin_json())}
        print_json(api.call("PUT", _alarm(positional[0]), body))
    elif name in ("snooze", "finish", "reopen"):
        body: dict[str, Any] = {"project": project, "version": version}
        if "--until" in options:
            body["until"] = options["--until"]
        print_json(api.call("POST", _alarm(positional[0], f"/{name}"), body))
    elif name == "delete":
        uid = target.resolve(positional[0])
        print_json(api.call("DELETE", f"/workspace/elements/{quote(uid)}", query={"version": str(version)}))
    elif name == "restore":
        print_json(api.call("POST", "/workspace/trash/restore", {"uids": [target.resolve(positional[0])]}))


def run(project_name: str, source_name: str | None, name: str, args: list[str]) -> None:
    if name not in COMMANDS:
        raise ApiError(USAGE, EXIT_USAGE)
    positional, options = _split(name, args)
    project = find_project(project_name, "todo")
    if not project.config.viewer_memos_enabled():
        raise ApiError(
            f"alarms need todo.backend = \"api\" in project {project.name}: they live only in the ToDo-Viewer",
            EXIT_USAGE,
        )
    api = Api(project.config.todo_api_url)
    _run(target_for(api, project, source_name), name, positional, options)


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

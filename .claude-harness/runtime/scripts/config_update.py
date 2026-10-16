"""Complete a project's .claude-harness/config.toml from the plugin's config template.

Usage: config_update.py <folder> [--subproject] [--set KEY=VALUE ...] [--write]
  Compares <folder>/.claude-harness/config.toml with the template and adds
  missing sections, keys, modules, and template comments; existing lines stay.
  A missing key gets the value that applies while it is absent. Decisions:
  new modules, todo.backend while todo is on, harness.repo (root project
  only), and comments that differ from the template.
  --subproject  the folder is a registered subproject (no [harness] and no [cloud] table)
  --set         one decision: modules.<name>=true|false, todo.backend=api|files,
                harness.repo=<path or TOML list of paths>,
                comment:<place>=keep|replace
  --write       write the result; every decision must be set
Output: one "decision:" line per decision (pending or set, with its choices;
comment decisions add "project:" and "template:" lines), "changes: <n>",
the unified diff, and "written: <path>" after --write.
Exit codes: 0 ok, 1 invalid config or pending decisions, 2 usage.
"""

from __future__ import annotations

import difflib
import json
import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from harness_config import CONFIG_RELATIVE_PATH, ConfigError, parse_config

# The plugin's own template; it always sits at this place next to the scripts.
TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "config.toml"
# Tables that are not completed in a subproject config.
_ROOT_ONLY = ("harness", "cloud")
TOP = "top"
_HEADER = re.compile(r"\s*\[([A-Za-z0-9_.-]+)\]\s*(#.*)?$")
_KEY = re.compile(r"\s*([A-Za-z0-9_-]+)\s*=")


@dataclass(frozen=True)
class Decision:
    key: str
    value: str  # TOML value, or keep/replace for comments
    choices: str
    pending: bool
    project: str = ""  # comment decisions: the project's text
    template: str = ""  # comment decisions: the template's text


@dataclass(frozen=True)
class Result:
    text: str
    decisions: tuple[Decision, ...]
    changes: int = 0


@dataclass
class _Entry:
    start: int
    end: int  # exclusive; more than one line for multi-line arrays


@dataclass
class _Section:
    name: str
    anchor: int  # header line; for the top section the first key line
    end: int  # exclusive: where the next section's comment block starts
    keys: dict[str, _Entry] = field(default_factory=dict)


def _split_comment(line: str) -> tuple[str, str | None]:
    """Code part (right-stripped) and the '#' comment of a line, respecting strings."""
    quote = None
    i = 0
    while i < len(line):
        char = line[i]
        if quote:
            if char == "\\" and quote == '"':
                i += 1
            elif char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char == "#":
            return line[:i].rstrip(), line[i:].rstrip()
        i += 1
    return line.rstrip(), None


def _is_comment(line: str) -> bool:
    return line.lstrip().startswith("#")


def _layout(lines: list[str]) -> dict[str, _Section]:
    sections: dict[str, _Section] = {}
    current: _Section | None = None
    i = 0
    while i < len(lines):
        code, _ = _split_comment(lines[i])
        header = _HEADER.match(lines[i])
        key = _KEY.match(code)
        if header:
            current = sections[header.group(1)] = _Section(header.group(1), i, len(lines))
        elif key:
            start = i
            depth = code.count("[") - code.count("]")
            while depth > 0 and i + 1 < len(lines):
                i += 1
                inner, _ = _split_comment(lines[i])
                depth += inner.count("[") - inner.count("]")
            if current is None:
                current = sections[TOP] = _Section(TOP, start, len(lines))
            current.keys[key.group(1)] = _Entry(start, i + 1)
        i += 1
    ordered = sorted(sections.values(), key=lambda s: s.anchor)
    for section, following in zip(ordered, ordered[1:]):
        section.end = _block_start(lines, following.anchor)
    return sections


def _block_start(lines: list[str], anchor: int) -> int:
    """First line of the comment block directly above anchor."""
    start = anchor
    while start > 0 and _is_comment(lines[start - 1]):
        start -= 1
    return start


def _last_code_line(lines: list[str], section: _Section) -> int:
    last = section.anchor
    for index in range(section.anchor, section.end):
        if lines[index].strip():
            last = index
    return last


def _toml(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(_toml(item) for item in value) + "]"
    return json.dumps(value, ensure_ascii=False)


def _with_comment(code: str, comment: str | None, template_line: str) -> str:
    if not comment:
        return code
    column = template_line.find("#")
    if column > 0 and len(code) + 2 <= column:
        return code.ljust(column) + comment
    return f"{code}  {comment}"


class _Planner:
    def __init__(self, project: str, template: str, subproject: bool, choices: dict[str, str]):
        self.lines = project.splitlines()
        self.tlines = template.splitlines()
        self.subproject = subproject
        self.choices = dict(choices)
        self.decisions: list[Decision] = []
        self.edits: list[tuple[int, int, list[str]]] = []
        try:
            self.data = tomllib.loads(project)
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(f"{CONFIG_RELATIVE_PATH}: invalid TOML: {exc}") from exc
        parse_config(self.data, subproject=subproject)
        self.template_data = tomllib.loads(template)

    # Decisions ------------------------------------------------------------

    def _decide(self, key: str, default: str, choices: str, **texts: str) -> str:
        chosen = self.choices.pop(key, None)
        value = default if chosen is None else self._check(key, chosen)
        self.decisions.append(Decision(key, value, choices, chosen is None, **texts))
        return value

    @staticmethod
    def _check(key: str, raw: str) -> str:
        if key.startswith("comment:"):
            allowed = ("keep", "replace")
        elif key.startswith("modules."):
            allowed = ("true", "false")
        elif key == "todo.backend":
            if raw.strip('"') in ("api", "files"):
                return _toml(raw.strip('"'))
            allowed = ("api", "files")
        else:  # harness.repo
            try:
                value = tomllib.loads(f"v = {raw}")["v"]
            except tomllib.TOMLDecodeError:
                value = [raw]
            if isinstance(value, str):
                value = [value]
            if isinstance(value, list) and all(isinstance(item, str) for item in value):
                return _toml(value)
            raise ConfigError(f"harness.repo must be a path or a list of paths, got {raw!r}")
        if raw not in allowed:
            raise ConfigError(f"{key} must be one of {', '.join(allowed)}, got {raw!r}")
        return raw

    def _value(self, table: str, key: str) -> str | None:
        """The value to write for a missing key, or None to use the template line as it is."""
        if table == "modules":
            return self._decide(f"modules.{key}", "false", "true|false")
        if table == "todo" and key == "backend" and self._todo_on():
            return self._decide("todo.backend", _toml(self.template_data["todo"]["backend"]), "api|files")
        if table == "harness" and key == "repo":
            return self._decide("harness.repo", "[]", "a path or a TOML list of paths")
        return None

    def _todo_on(self) -> bool:
        if "todo" in self.data.get("modules", {}):
            return self.data["modules"]["todo"] is True
        return self.choices.get("modules.todo") == "true" or any(
            d.key == "modules.todo" and d.value == "true" for d in self.decisions
        )

    # Lines ----------------------------------------------------------------

    def _key_lines(self, table: str, key: str, entry: _Entry) -> list[str]:
        lines = self.tlines[entry.start:entry.end]
        value = self._value(table, key)
        if value is None:
            return lines
        _, comment = _split_comment(lines[-1])
        return [_with_comment(f"{key} = {value}", comment, lines[-1])]

    def _comment_block(self, name: str, lines: list[str], anchor: int, tanchor: int) -> None:
        start = _block_start(lines, anchor)
        tstart = _block_start(self.tlines, tanchor)
        own = [line.strip() for line in lines[start:anchor]]
        wanted = [line.strip() for line in self.tlines[tstart:tanchor]]
        if not wanted or own == wanted:
            return
        if not own:
            self.edits.append((anchor, anchor, self.tlines[tstart:tanchor]))
            return
        choice = self._decide(f"comment:{name}", "keep", "keep|replace",
                              project="\n".join(own), template="\n".join(wanted))
        if choice == "replace":
            self.edits.append((start, anchor, self.tlines[tstart:tanchor]))

    def _inline_comment(self, place: str, entry: _Entry, tentry: _Entry) -> None:
        tline = self.tlines[tentry.end - 1]
        _, wanted = _split_comment(tline)
        index = entry.end - 1
        code, own = _split_comment(self.lines[index])
        if not wanted or own == wanted:
            return
        if own is not None:
            if self._decide(f"comment:{place}", "keep", "keep|replace", project=own, template=wanted) == "keep":
                return
        self.edits.append((index, index + 1, [_with_comment(code, wanted, tline)]))

    # Plan -----------------------------------------------------------------

    def run(self) -> Result:
        project = _layout(self.lines)
        template = _layout(self.tlines)
        previous = project[TOP]
        for name, tsection in template.items():
            if name in _ROOT_ONLY and self.subproject:
                continue
            section = project.get(name)
            if section is None:
                block = self.tlines[_block_start(self.tlines, tsection.anchor):tsection.anchor + 1]
                for key, tentry in tsection.keys.items():
                    block += self._key_lines(name, key, tentry)
                position = _last_code_line(self.lines, previous) + 1
                self.edits.append((position, position, ["", *block]))
                continue
            self._comment_block(name, self.lines, section.anchor, tsection.anchor)
            after = section.anchor if name != TOP else section.anchor - 1
            for key, tentry in tsection.keys.items():
                entry = section.keys.get(key)
                if entry is None:
                    self.edits.append((after + 1, after + 1, self._key_lines(name, key, tentry)))
                else:
                    self._inline_comment(key if name == TOP else f"{name}.{key}", entry, tentry)
                    after = entry.end - 1
            previous = section
        if self.choices:
            raise ConfigError(f"not a decision here: {', '.join(sorted(self.choices))}")
        text = self._apply()
        try:
            parse_config(tomllib.loads(text), subproject=self.subproject)
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(f"completed config is not valid TOML: {exc}") from exc
        return Result(text, tuple(self.decisions), len(self.edits))

    def _apply(self) -> str:
        if not self.edits:
            return "\n".join(self.lines) + "\n" if self.lines else ""
        lines = list(self.lines)
        ordered = sorted(enumerate(self.edits), key=lambda e: (e[1][0], e[0]), reverse=True)
        for _, (start, end, new) in ordered:
            lines[start:end] = new
        return "\n".join(lines) + "\n"


def complete(project: str, template: str, *, subproject: bool = False,
             choices: dict[str, str] | None = None) -> Result:
    """The project config completed from the template, and the decisions this needs."""
    result = _Planner(project, template, subproject, choices or {}).run()
    if result.text.rstrip("\n") == project.rstrip("\n"):
        return Result(project, result.decisions)
    return result


def _report(result: Result, before: str) -> None:
    for decision in result.decisions:
        state = "pending" if decision.pending else "set"
        print(f"decision: {decision.key} = {decision.value} ({state}; {decision.choices})")
        for label in ("project", "template"):
            for line in getattr(decision, label).splitlines():
                print(f"  {label}: {line}")
    print(f"changes: {result.changes}")
    path = str(CONFIG_RELATIVE_PATH)
    diff = difflib.unified_diff(before.splitlines(), result.text.splitlines(), f"a/{path}", f"b/{path}", lineterm="")
    for line in diff:
        print(line)


def main(argv: list[str]) -> int:
    folder, subproject, write, choices = None, False, False, {}
    args = iter(argv)
    for arg in args:
        if arg == "--subproject":
            subproject = True
        elif arg == "--write":
            write = True
        elif arg == "--set":
            key, sep, value = next(args, "").partition("=")
            if not sep or not key:
                print(__doc__.strip(), file=sys.stderr)
                return 2
            choices[key] = value
        elif folder is None and not arg.startswith("-"):
            folder = Path(arg)
        else:
            print(__doc__.strip(), file=sys.stderr)
            return 2
    if folder is None:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    path = folder / CONFIG_RELATIVE_PATH
    if not path.is_file():
        print(f"error: no {CONFIG_RELATIVE_PATH} in {folder}", file=sys.stderr)
        return 1
    before = path.read_text(encoding="utf-8")
    try:
        result = complete(before, TEMPLATE.read_text(encoding="utf-8"), subproject=subproject, choices=choices)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    _report(result, before)
    if not write or not result.changes:
        return 0
    pending = [d.key for d in result.decisions if d.pending]
    if pending:
        print(f"error: decisions not set: {', '.join(pending)}", file=sys.stderr)
        return 1
    path.write_text(result.text, encoding="utf-8")
    print(f"written: {CONFIG_RELATIVE_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Check relative Markdown links (and #anchors) in the documents of a project.

Shared by the session start hook and the Stop hook (STORY-055). Only the standard library, no network.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

from harness_config import README, HarnessConfig

_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)")
_DEFINITION = re.compile(r"^ {0,3}\[([^\]\n]+)\]:\s*(<[^>\n]*>|\S+)")
_HEADING = re.compile(r"^ {0,3}#{1,6}(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
_SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
_ANCHOR_TAG = re.compile(r"""<a\s[^>]*?\b(?:id|name)\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
_SCHEME = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.\-]*:|//)")
_NOT_SLUG = re.compile(r"[^\w\- ]", re.UNICODE)
_MARKUP_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")


def _visible_lines(text: str) -> list[tuple[int, str]]:
    """(line number, line) outside fenced code blocks; fence lines and their content are left out."""
    lines: list[tuple[int, str]] = []
    fence: str | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        match = _FENCE.match(line)
        if fence is None:
            if match:
                fence = match.group(1)
                continue
            lines.append((number, line))
        elif match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence) and not line.strip().strip(fence[0]):
            fence = None
    return lines


def _blank_code(line: str) -> str:
    return _INLINE_CODE.sub(lambda m: " " * len(m.group(0)), line)


def _opening_bracket(line: str, close: int) -> int | None:
    """Index of the `[` that belongs to the `]` at `close`, or None."""
    depth = 0
    for index in range(close, -1, -1):
        char = line[index]
        if char == "]" and (index == 0 or line[index - 1] != "\\"):
            depth += 1
        elif char == "[" and (index == 0 or line[index - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return index
        elif char == "[":  # escaped
            continue
    return None


def _inline_target(line: str, start: int) -> str:
    """The link target that begins at `start` (just after `](`)."""
    if line.startswith("<", start):
        end = line.find(">", start)
        return line[start + 1 : end] if end != -1 else ""
    depth = 0
    index = start
    while index < len(line):
        char = line[index]
        if char.isspace():
            break
        if char == "(":
            depth += 1
        elif char == ")":
            if depth == 0:
                break
            depth -= 1
        index += 1
    return line[start:index]


def find_links(text: str) -> list[tuple[int, str]]:
    """(line number, target) of the inline links, images, and reference definitions outside code."""
    found: list[tuple[int, str]] = []
    for number, raw in _visible_lines(text):
        line = _blank_code(raw)
        definition = _DEFINITION.match(line)
        if definition and not definition.group(1).startswith("^"):
            target = definition.group(2)
            found.append((number, target[1:-1] if target.startswith("<") else target))
            continue
        position = 0
        while (at := line.find("](", position)) != -1:
            position = at + 2
            if _opening_bracket(line, at) is None:
                continue
            target = _inline_target(line, at + 2)
            if target:
                found.append((number, target))
    return found


def _slug(heading: str) -> str:
    heading = _MARKUP_LINK.sub(r"\1", heading)
    heading = re.sub(r"[`*]|<[^>]*>", "", heading)
    return _NOT_SLUG.sub("", heading.strip().lower()).replace(" ", "-")


def heading_slugs(text: str) -> set[str]:
    """The anchors a Markdown file offers: heading slugs as GitHub builds them, plus explicit <a id|name>."""
    slugs: set[str] = set()
    counts: dict[str, int] = {}

    def add(heading: str) -> None:
        base = _slug(heading)
        count = counts.get(base, 0)
        counts[base] = count + 1
        slugs.add(base if count == 0 else f"{base}-{count}")

    previous = ""
    for _, raw in _visible_lines(text):
        slugs.update(m.group(1).lower() for m in _ANCHOR_TAG.finditer(raw))
        heading = _HEADING.match(raw)
        if heading:
            add(heading.group(1) or "")
        elif _SETEXT.match(raw) and previous.strip() and not _HEADING.match(previous) and not _SETEXT.match(previous):
            add(previous)
        previous = raw
    return slugs


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def check_file(root: Path, rel: PurePosixPath, _slugs: dict[PurePosixPath, set[str] | None] | None = None) -> list[str]:
    """Dead links of the file `rel` (relative to the project root): `<file>:<line>: <target>: <reason>`."""
    text = _read(root / rel)
    if text is None:
        return []
    slugs = _slugs if _slugs is not None else {}
    problems: list[str] = []

    def anchors_of(target: PurePosixPath) -> set[str] | None:
        if target not in slugs:
            content = text if target == rel else _read(root / target)
            slugs[target] = None if content is None else heading_slugs(content)
        return slugs[target]

    for number, raw in find_links(text):
        if _SCHEME.match(raw):
            continue
        path_part, _, anchor = raw.partition("#")
        path_part = unquote(path_part.partition("?")[0])
        anchor = unquote(anchor).lower()

        def problem(reason: str, number: int = number, raw: str = raw) -> None:
            problems.append(f"{rel}:{number}: {raw}: {reason}")

        if not path_part:
            target = rel
        elif path_part.startswith("/"):
            target = PurePosixPath(os.path.normpath(path_part.lstrip("/")))
        else:
            target = PurePosixPath(os.path.normpath(str(rel.parent / path_part)))
        if target.is_absolute() or target.parts[:1] == ("..",):
            problem("target lies outside the project")
        elif not (root / target).exists():
            problem("target does not exist")
        elif anchor and target.suffix.lower() == ".md" and (root / target).is_file():
            offered = anchors_of(target)
            if offered is not None and anchor not in offered:
                problem(f"anchor not found in {target}")
    return problems


def doc_files(root: Path, config: HarnessConfig) -> list[PurePosixPath]:
    """The documents whose links are checked: README.md and techdocs (module techdocs), development (part architecture)."""
    folders: list[PurePosixPath] = []
    files: list[PurePosixPath] = []
    if config.enabled("techdocs"):
        if (root / README).is_file():
            files.append(README)
        folders.append(config.techdocs_path)
    if config.part_enabled("architecture"):
        folders.append(config.development_path)
    for folder in folders:
        base = root / folder
        if base.is_dir():
            files += sorted(PurePosixPath(p.relative_to(root).as_posix()) for p in base.rglob("*.md") if p.is_file())
    return files


def is_doc_file(config: HarnessConfig, rel: PurePosixPath) -> bool:
    """True when `rel` (relative to the project root) belongs to the documents doc_files lists."""
    if config.enabled("techdocs") and (rel == README or (rel.is_relative_to(config.techdocs_path) and rel.suffix == ".md")):
        return True
    return config.part_enabled("architecture") and rel.is_relative_to(config.development_path) and rel.suffix == ".md"


def check_project(
    root: Path,
    config: HarnessConfig,
    files: list[PurePosixPath] | None = None,
    prefix: PurePosixPath = PurePosixPath("."),
) -> list[str]:
    """Dead links of `files` (default: all of doc_files); messages are prefixed with the project's folder."""
    slugs: dict[PurePosixPath, set[str] | None] = {}
    problems: list[str] = []
    for rel in doc_files(root, config) if files is None else files:
        for message in check_file(root, rel, slugs):
            problems.append(message if prefix == PurePosixPath(".") else f"{prefix}/{message}")
    return problems


def main(argv: list[str]) -> int:
    """Manual check: `doclinks.py [project root]` prints the dead links of the project's documents."""
    from harness_config import load_config

    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    config = load_config(root)
    if config is None:
        print(f"error: no harness configuration in {root}", file=sys.stderr)
        return 2
    problems = check_project(root, config)
    print("\n".join(problems) if problems else "No dead links.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""Find the Claude_Harness repository on this machine.

Usage: harness_repo.py [--suggest]
  (no option)  print the first path from [harness].repo that exists here and is
               the Claude_Harness repository; print nothing if none is
  --suggest    print a candidate from Claude Code's directory marketplaces
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from harness_config import ConfigError, HarnessConfig, load_config, project_root

PLUGIN_NAME = "claude-harness"
PLUGIN_MANIFEST = Path("plugin/.claude-plugin/plugin.json")


def marketplaces_file() -> Path:
    # Owned by Claude Code; used only to suggest a path, never at runtime.
    return Path.home() / ".claude/plugins/known_marketplaces.json"


def is_harness_repo(path: Path) -> bool:
    try:
        manifest = json.loads((path / PLUGIN_MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(manifest, dict) and manifest.get("name") == PLUGIN_NAME


def configured_repo(config: HarnessConfig) -> Path | None:
    for entry in config.harness_repos:
        path = Path(entry).expanduser()
        if is_harness_repo(path):
            return path
    return None


def suggested_repo(marketplaces: Path) -> Path | None:
    try:
        data = json.loads(marketplaces.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    for entry in data.values():
        source = entry.get("source") if isinstance(entry, dict) else None
        if not isinstance(source, dict) or source.get("source") != "directory":
            continue
        path = source.get("path")
        if isinstance(path, str) and is_harness_repo(Path(path).expanduser()):
            return Path(path).expanduser()
    return None


def main(argv: list[str]) -> int:
    if argv == ["--suggest"]:
        repo = suggested_repo(marketplaces_file())
    elif not argv:
        try:
            config = load_config(project_root())
        except ConfigError:
            return 0
        repo = configured_repo(config) if config else None
    else:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if repo:
        print(repo)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

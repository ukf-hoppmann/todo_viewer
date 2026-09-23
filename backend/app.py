from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from parser import (
    ARCHIVE_FILE,
    EDITABLE_FIELDS,
    TODO_FILE,
    archive_supported,
    item_to_dict,
    parse_file,
    update_item_field,
)
from todo_viewer.domain.errors import DomainError

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = Path(os.environ.get("CONFIG_DIR", BASE_DIR / "configs"))
CONFIG_PATH = CONFIG_DIR / "config.json"
STATE_PATH = CONFIG_DIR / "ui_state.json"
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__, static_folder=None)

CONFIG_LOCK = threading.RLock()


def error(code: str, message: str, status: int = 400, **extra):
    return jsonify({"error": message, "code": code, **extra}), status


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(CONFIG_PATH)


def load_config() -> dict:
    """Loads config.json; sources that still point to a file are migrated to its folder."""
    with CONFIG_LOCK:
        with CONFIG_PATH.open(encoding="utf-8") as f:
            config = json.load(f)
        changed = False
        for source in config.get("sources", []):
            path = Path(source.get("path", ""))
            if path.suffix.lower() in {".md", ".markdown", ".txt"}:
                source["path"] = str(path.parent)
                changed = True
        if changed:
            save_config(config)
        return config


def source_dir(path: str) -> Path:
    folder = Path(path).expanduser()
    return folder if folder.is_absolute() else BASE_DIR / folder


def check_source_dir(path: str) -> tuple[str, str] | None:
    """(code, message) if the configured backlog folder is unusable, else None."""
    folder = source_dir(path)
    if not folder.exists():
        return "not_found", "Folder not found."
    if not folder.is_dir():
        return "not_a_dir", "Path is not a folder."
    if not (folder / TODO_FILE).is_file():
        return "no_todo", f"No {TODO_FILE} in this folder."
    return None


def suggest_project_name(folder: Path) -> str:
    """Name of the enclosing git repository, falling back to the folder name."""
    for candidate in [folder, *folder.parents]:
        if (candidate / ".git").exists():
            return candidate.name
    return folder.name


def collect_items() -> dict:
    config = load_config()
    all_items = []
    sources = []
    for index, source in enumerate(config.get("sources", [])):
        project = source["project"]
        entry = {"index": index, "project": project, "path": source["path"], "count": 0,
                 "error": None, "code": None}
        sources.append(entry)

        problem = check_source_dir(source["path"])
        if problem:
            entry["code"], entry["error"] = problem
            continue

        folder = source_dir(source["path"])
        for name in (TODO_FILE, ARCHIVE_FILE):
            path = folder / name
            if not path.is_file():
                continue
            try:
                items = parse_file(path, project)
            except Exception as exc:  # surfaced to the UI instead of crashing
                entry["code"], entry["error"] = "parse_error", f"{name}: {exc}"
                continue
            entry["count"] += len(items)
            for item in items:
                data = item_to_dict(item)
                data["source_index"] = index
                data["in_archive"] = name == ARCHIVE_FILE
                data["archive_supported"] = archive_supported(path, item.format)
                all_items.append(data)
    return {"items": all_items, "sources": sources}


@app.get("/api/data")
def api_data():
    try:
        return jsonify(collect_items())
    except FileNotFoundError:
        return jsonify({"items": [], "sources": [], "error": "config.json not found"}), 404


@app.get("/api/config")
def api_config():
    return jsonify(load_config())


def _source_from_request(data):
    if not isinstance(data, dict):
        return None, ("bad_request", "expected a JSON object")
    path = str(data.get("path") or "").strip().rstrip("/") or ""
    if not path:
        return None, ("missing_path", "Path is missing.")
    problem = check_source_dir(path)
    if problem:
        return None, problem
    project = str(data.get("project") or "").strip() or suggest_project_name(source_dir(path))
    return {"project": project, "path": path}, None


@app.post("/api/sources")
def api_add_source():
    source, problem = _source_from_request(request.get_json(silent=True))
    if problem:
        return error(*problem)
    with CONFIG_LOCK:
        config = load_config() if CONFIG_PATH.exists() else {"sources": []}
        sources = config.setdefault("sources", [])
        if any(s.get("path") == source["path"] for s in sources):
            return error("duplicate", "This folder is already configured.")
        sources.append(source)
        save_config(config)
    return jsonify({"source": source})


@app.put("/api/sources/<int:index>")
def api_update_source(index: int):
    source, problem = _source_from_request(request.get_json(silent=True))
    if problem:
        return error(*problem)
    with CONFIG_LOCK:
        config = load_config()
        sources = config.get("sources", [])
        if not 0 <= index < len(sources):
            return error("source_gone", "Source not found (config was probably changed externally).", 404)
        if any(i != index and s.get("path") == source["path"] for i, s in enumerate(sources)):
            return error("duplicate", "This folder is already configured.")
        sources[index] = {**sources[index], **source}
        save_config(config)
    return jsonify({"source": sources[index]})


@app.delete("/api/sources/<int:index>")
def api_delete_source(index: int):
    expected_path = request.args.get("path")
    with CONFIG_LOCK:
        config = load_config()
        sources = config.get("sources", [])
        if not 0 <= index < len(sources) or (expected_path and sources[index].get("path") != expected_path):
            return error("source_gone", "Source not found (config was probably changed externally).", 404)
        removed = sources.pop(index)
        save_config(config)
    return jsonify({"removed": removed})


def default_browse_dir() -> Path:
    env = os.environ.get("BROWSE_START")
    if env and Path(env).is_dir():
        return Path(env)
    return Path.home()


@app.get("/api/browse")
def api_browse():
    """Lists the subfolders of a folder for the backlog folder picker."""
    raw = (request.args.get("path") or "").strip()
    target = Path(raw).expanduser() if raw else default_browse_dir()
    if not target.is_absolute():
        target = BASE_DIR / target
    # Fall back to the nearest existing ancestor (e.g. for a broken source path).
    while not target.is_dir() and target != target.parent:
        target = target.parent
    target = target.resolve()

    dirs = []
    listing_error = None
    try:
        for entry in sorted(target.iterdir(), key=lambda e: e.name.lower()):
            if entry.name.startswith("."):
                continue
            try:
                if entry.is_dir():
                    dirs.append({"name": entry.name, "has_todo": (entry / TODO_FILE).is_file()})
            except OSError:
                continue
    except OSError as exc:
        listing_error = str(exc)

    return jsonify({
        "path": str(target),
        "parent": str(target.parent) if target != target.parent else None,
        "has_todo": (target / TODO_FILE).is_file(),
        "dirs": dirs,
        "error": listing_error,
    })


@app.get("/api/itemfile")
def api_item_file():
    """Returns a notes/spec markdown file; only files inside the backlog folder are served."""
    try:
        index = int(request.args.get("source", ""))
    except ValueError:
        return error("bad_request", "source is missing")
    rel = request.args.get("path") or ""
    sources = load_config().get("sources", [])
    if not 0 <= index < len(sources):
        return error("source_gone", "Source not found.", 404)
    base = source_dir(sources[index]["path"]).resolve()
    target = (base / rel).resolve()
    if not target.is_relative_to(base) or target.suffix.lower() not in {".md", ".markdown", ".txt"}:
        return error("forbidden", "Only markdown files inside the backlog folder can be opened.", 403)
    if not target.is_file():
        return error("file_not_found", "File not found.", 404, path=rel)
    return jsonify({"path": rel, "content": target.read_text(encoding="utf-8", errors="replace")})


@app.get("/api/state")
def api_get_state():
    if not STATE_PATH.exists():
        return jsonify({})
    try:
        with STATE_PATH.open(encoding="utf-8") as f:
            return jsonify(json.load(f))
    except (json.JSONDecodeError, OSError):
        return jsonify({})


@app.post("/api/state")
def api_save_state():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "expected a JSON object"}), 400
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})


@app.post("/api/items/update")
def api_update_item():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("bad_request", "expected a JSON object")

    source_file = data.get("source_file")
    line = data.get("line")
    item_id = data.get("id")
    project = data.get("project")
    fmt = data.get("format")
    field = data.get("field")
    value = data.get("value")
    resolution = data.get("resolution")

    if not all([source_file, isinstance(line, int), item_id, project, fmt, field]) or value is None:
        return error("bad_request", "missing required fields")
    if field not in EDITABLE_FIELDS:
        return error("not_editable", f"Field '{field}' is not editable.")

    path = Path(source_file)
    if not path.exists():
        return error("file_not_found", "Source file not found.", 404)

    try:
        final_path = update_item_field(path, line, item_id, fmt, field, value, resolution)
    except DomainError as exc:
        return error(exc.code, str(exc))
    except OSError as exc:
        return error("write_failed", str(exc), 500)

    items = parse_file(final_path, project)
    updated = next((i for i in items if i.id == item_id), None)
    if updated is None:
        return error("entry_moved", "Entry not found after saving.", 500)
    return jsonify({"item": item_to_dict(updated)})


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:filename>")
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5411"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug)

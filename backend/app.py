from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

from todo_viewer.bootstrap import Container, Settings, build_container
from todo_viewer.domain.editing import Field
from todo_viewer.domain.errors import (
    ConfigMissingError,
    DomainError,
    EntryMovedError,
    ForbiddenError,
    NotFoundError,
    UnknownFormatError,
)
from todo_viewer.domain.item import Item, ItemFormat, ItemRef, Location
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.markdown.syntax import ARCHIVE_FILE, TODO_FILE


def item_to_dict(item: Item) -> dict[str, Any]:
    return {
        "id": item.id,
        "title": item.title,
        "source_file": item.source_file,
        "project": item.project,
        "line": item.line,
        "format": item.format.value,
        "type": item.item_type,
        "status": item.status,
        "parent": item.parent,
        "required_for_parent": item.required_for_parent,
        "dependencies": item.dependencies,
        "created": item.created,
        "area": item.area,
        "priority": item.priority,
        "goal": item.goal,
        "completion_criteria": item.completion_criteria,
        "summary": item.summary,
        "resolution": item.resolution,
        "notes": item.notes,
        "spec": item.spec,
        "extra_fields": item.extra_fields,
    }


def source_to_dict(source: Source) -> dict[str, Any]:
    return {"project": source.project, "path": source.path, **source.extra}


def error(code: str, message: str, status: int = 400, **extra: Any):
    return jsonify({"error": message, "code": code, **extra}), status


def domain_error(exc: DomainError):
    status = 404 if isinstance(exc, NotFoundError) else 403 if isinstance(exc, ForbiddenError) else 400
    return error(exc.code, exc.message, status, **exc.details)


def create_app(container: Container, frontend_dir: Path) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.register_error_handler(DomainError, domain_error)

    @app.get("/api/data")
    def api_data():
        try:
            overview = container.overview.overview()
        except ConfigMissingError:
            return jsonify({"items": [], "sources": [], "error": "config.json not found"}), 404
        items, sources = [], []
        for entry in overview:
            problem = entry.backlog.problem
            sources.append({"index": entry.index, "project": entry.source.project, "path": entry.source.path,
                            "count": len(entry.backlog.items),
                            "error": problem.message if problem else None,
                            "code": problem.code if problem else None})
            for item in entry.backlog.items:
                items.append({**item_to_dict(item),
                              "source_index": entry.index,
                              "in_archive": item.location is Location.ARCHIVE,
                              "archive_supported": entry.backlog.supports_archive(item)})
        return jsonify({"items": items, "sources": sources})

    @app.get("/api/config")
    def api_config():
        return jsonify({"sources": [source_to_dict(s) for s in container.sources.all()]})

    def source_body() -> tuple[str, str | None] | None:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return None
        return str(data.get("path") or ""), str(data.get("project") or "")

    @app.post("/api/sources")
    def api_add_source():
        body = source_body()
        if body is None:
            return error("bad_request", "expected a JSON object")
        return jsonify({"source": source_to_dict(container.sources.add(*body))})

    @app.put("/api/sources/<int:index>")
    def api_update_source(index: int):
        body = source_body()
        if body is None:
            return error("bad_request", "expected a JSON object")
        return jsonify({"source": source_to_dict(container.sources.update(index, *body))})

    @app.delete("/api/sources/<int:index>")
    def api_delete_source(index: int):
        removed = container.sources.remove(index, request.args.get("path"))
        return jsonify({"removed": source_to_dict(removed)})

    @app.get("/api/browse")
    def api_browse():
        listing = container.folders.browse(request.args.get("path"))
        return jsonify({
            "path": listing.path,
            "parent": listing.parent,
            "has_todo": listing.has_todo,
            "dirs": [{"name": d.name, "has_todo": d.has_todo} for d in listing.dirs],
            "error": listing.error,
        })

    @app.get("/api/itemfile")
    def api_item_file():
        """Returns a notes/spec markdown file; only files inside the backlog folder are served."""
        try:
            index = int(request.args.get("source", ""))
        except ValueError:
            return error("bad_request", "source is missing")
        rel = request.args.get("path") or ""
        return jsonify({"path": rel, "content": container.documents.read(index, rel)})

    @app.get("/api/state")
    def api_get_state():
        return jsonify(container.ui_state.get())

    @app.post("/api/state")
    def api_save_state():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "expected a JSON object"}), 400
        container.ui_state.save(data)
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
        if not all([source_file, isinstance(line, int), item_id, project, fmt, field]) or value is None:
            return error("bad_request", "missing required fields")

        # Legacy addressing by file path; replaced by source index + item ref in API v2.
        path = Path(source_file)
        location = {TODO_FILE: Location.ACTIVE, ARCHIVE_FILE: Location.ARCHIVE}.get(path.name)
        if field in Field.EDITABLE:
            if not path.exists():
                return error("file_not_found", "Source file not found.", 404)
            if fmt not in {f.value for f in ItemFormat}:
                raise UnknownFormatError(fmt)
            if location is None:
                raise EntryMovedError()

        source = Source(project=project, path=str(path.parent))
        ref = ItemRef(item_id, location or Location.ACTIVE, line)
        try:
            result = container.item_edits.edit(source, ref, field, value, data.get("resolution"))
        except OSError as exc:
            return error("write_failed", str(exc), 500)
        return jsonify({"item": item_to_dict(result.item)})

    @app.get("/")
    def index():
        return send_from_directory(frontend_dir, "index.html")

    @app.get("/<path:filename>")
    def static_files(filename):
        return send_from_directory(frontend_dir, filename)

    return app


if __name__ == "__main__":
    settings = Settings.from_env()
    app = create_app(build_container(settings), settings.frontend_dir)
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5411"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug)

"""Erzeugt aus den Operationen der Plugins FastAPI-Routen (Plugins schreiben keine Router)."""

from __future__ import annotations

import dataclasses
import inspect
import re
from collections.abc import Callable
from typing import Annotated, Any, get_type_hints

from fastapi import FastAPI, Query
from pydantic import Field, create_model

from viewer.core.api.errors import ErrorBody
from viewer.core.application.plugin import PluginHost
from viewer.core.domain.errors import PluginSetupError
from viewer.core.domain.operations import Operation

_BODY_METHODS = {"POST", "PUT", "PATCH"}
_PATH_PARAM = re.compile(r"\{(\w+)\}")


def register_operations(app: FastAPI, host: PluginHost) -> None:
    for plugin in host.plugins:
        owner = plugin.definition.id
        for op in plugin.definition.operations:
            if op.http is None:
                continue
            endpoint = _make_endpoint(host, owner, op)
            app.add_api_route(
                f"/api/{owner}{op.http.path}",
                endpoint,
                methods=[op.http.method],
                response_model=op.output,
                summary=op.summary,
                operation_id=f"{owner}_{op.name}",
                tags=[owner],
                responses={"4XX": {"model": ErrorBody}},
            )


def _make_endpoint(host: PluginHost, owner: str, op: Operation) -> Callable[..., Any]:
    assert op.http is not None
    if not dataclasses.is_dataclass(op.input):
        raise PluginSetupError([f"Input von '{owner}.{op.name}' ist keine Dataclass"])
    fields = dataclasses.fields(op.input)
    hints = get_type_hints(op.input, include_extras=True)
    path_names = set(_PATH_PARAM.findall(op.http.path))
    missing = path_names - {f.name for f in fields}
    if missing:
        raise PluginSetupError([f"Pfadparameter {sorted(missing)} von '{owner}.{op.name}' fehlen im Input"])

    other = [f for f in fields if f.name not in path_names]
    params: list[inspect.Parameter] = []
    for f in fields:
        if f.name in path_names:
            params.append(_param(f.name, hints[f.name], inspect.Parameter.empty))
    body_names: list[str] = []
    if op.http.method in _BODY_METHODS:
        if other:
            body_names = [f.name for f in other]
            model = create_model(  # type: ignore[call-overload]
                _camel(owner, op.name, "Body"),
                **{f.name: (hints[f.name], _field_default(f)) for f in other},
            )
            params.append(_param("body", model, inspect.Parameter.empty))
    else:
        for f in other:
            params.append(_param(f.name, Annotated[hints[f.name], Query()], _plain_default(f)))

    path_values = [f.name for f in fields if f.name in path_names]
    query_values = [] if body_names else [f.name for f in other]

    async def endpoint(**kwargs: Any) -> Any:
        values = {name: kwargs[name] for name in path_values + query_values}
        body = kwargs.get("body")
        for name in body_names:
            values[name] = getattr(body, name)
        return await host.call(owner, op.name, op.input(**values))

    endpoint.__name__ = f"{owner}_{op.name}"
    endpoint.__signature__ = inspect.Signature(params)  # type: ignore[attr-defined]
    return endpoint


def _param(name: str, annotation: Any, default: Any) -> inspect.Parameter:
    return inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY, default=default, annotation=annotation)


def _plain_default(f: dataclasses.Field[Any]) -> Any:
    if f.default is not dataclasses.MISSING:
        return f.default
    if f.default_factory is not dataclasses.MISSING:
        return f.default_factory()
    return inspect.Parameter.empty


def _field_default(f: dataclasses.Field[Any]) -> Any:
    if f.default is not dataclasses.MISSING:
        return f.default
    if f.default_factory is not dataclasses.MISSING:
        return Field(default_factory=f.default_factory)
    return ...


def _camel(*parts: str) -> str:
    return "".join(w.capitalize() for p in parts for w in re.split(r"[-_]", p))

"""Beispiel-Plugin nur für Tests: deckt Query, Pfad + Body, Listen, Fehler und Ereignisse ab."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from viewer.core.application.plugin import PluginContext, PluginDefinition
from viewer.core.domain.errors import NotFound, VersionConflict
from viewer.core.domain.events import Event
from viewer.core.domain.operations import HttpBinding, Operation


@dataclass(frozen=True)
class Greet:
    name: str
    shout: bool = False


@dataclass(frozen=True)
class Greeting:
    text: str


@dataclass(frozen=True)
class ListItems:
    pass


@dataclass(frozen=True)
class Item:
    uid: str
    title: str
    version: int


@dataclass(frozen=True)
class Retitle:
    uid: str
    title: str
    version: int
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Nothing:
    pass


@dataclass(frozen=True)
class Ping:
    message: str


class ExampleServices:
    def __init__(self, context: PluginContext) -> None:
        self.context = context
        self.items = {"i1": Item("i1", "Erstes", 1)}

    def greet(self, data: Greet) -> Greeting:
        text = f"Hallo {data.name}"
        return Greeting(text.upper() if data.shout else text)

    def list_items(self, data: ListItems) -> list[Item]:
        return list(self.items.values())

    async def retitle(self, data: Retitle) -> Item:
        item = self.items.get(data.uid)
        if item is None:
            raise NotFound(f"Item {data.uid} gibt es nicht", details={"uid": data.uid})
        if item.version != data.version:
            raise VersionConflict("Zwischenzeitlich geändert", details={"current": item.version})
        updated = Item(item.uid, data.title, item.version + 1)
        self.items[data.uid] = updated
        return updated

    def crash(self, data: Nothing) -> Nothing:
        raise RuntimeError("unerwartet")

    def ping(self, data: Ping) -> Nothing:
        self.context.events.publish(Event("example.ping", {"message": data.message}, public=True))
        self.context.events.publish(Event("example.secret", {"message": data.message}, public=False))
        return Nothing()


def _build(context: PluginContext) -> ExampleServices:
    return ExampleServices(context)


def _call(method: str) -> Any:
    return lambda services, data: getattr(services, method)(data)


EXAMPLE_PLUGIN = PluginDefinition(
    id="example",
    build=_build,
    operations=(
        Operation("greet", "Grüßt jemanden", "read", Greet, Greeting, _call("greet"), HttpBinding("GET", "/greet")),
        Operation(
            "list_items",
            "Listet Items",
            "read",
            ListItems,
            list[Item],
            _call("list_items"),
            HttpBinding("GET", "/items"),
        ),
        Operation(
            "retitle",
            "Benennt ein Item um",
            "write",
            Retitle,
            Item,
            _call("retitle"),
            HttpBinding("PUT", "/items/{uid}"),
        ),
        Operation(
            "crash",
            "Wirft einen unerwarteten Fehler",
            "read",
            Nothing,
            Nothing,
            _call("crash"),
            HttpBinding("GET", "/crash"),
            mcp=False,
        ),
        Operation(
            "ping", "Veröffentlicht Ereignisse", "write", Ping, Nothing, _call("ping"), HttpBinding("POST", "/ping")
        ),
    ),
)

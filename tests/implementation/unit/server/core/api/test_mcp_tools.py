from __future__ import annotations

from dataclasses import dataclass

from fakes import FixedClock, NullBackups, NullDatabase, NullScheduler
from viewer.core.api.mcp import build_tools
from viewer.core.application.plugin import PluginDefinition, PluginHost
from viewer.core.domain.operations import Operation
from viewer.core.domain.settings import Settings
from viewer.core.infrastructure.event_bus import InProcessEventBus


@dataclass(frozen=True)
class In:
    uid: str
    count: int = 1


@dataclass(frozen=True)
class Out:
    text: str


def host(*operations: Operation, plugin_id: str = "my-plugin") -> PluginHost:
    return PluginHost(
        [PluginDefinition(plugin_id, lambda c: None, operations=operations)],
        clock=FixedClock(),
        events=InProcessEventBus(),
        scheduler=NullScheduler(),
        database=NullDatabase(),
        backups=NullBackups(),
        settings=Settings(),
    )


def op(name: str, kind: str = "read", mcp: bool = True) -> Operation:
    return Operation(name, f"Summary {name}", kind, In, Out, lambda s, i: Out("x"), mcp=mcp)  # type: ignore[arg-type]


def test_tools_are_named_owner_underscore_name_with_dashes_replaced() -> None:
    assert list(build_tools(host(op("list_things")))) == ["my_plugin_list_things"]


def test_only_mcp_operations_become_tools() -> None:
    assert list(build_tools(host(op("a"), op("b", mcp=False)))) == ["my_plugin_a"]


def test_description_schema_and_read_only_hint() -> None:
    tools = build_tools(host(op("a", "read"), op("b", "write")))
    a, b = tools["my_plugin_a"].describe(), tools["my_plugin_b"].describe()
    assert a.description == "Summary a"
    assert a.input_schema["properties"].keys() == {"uid", "count"} and a.input_schema["required"] == ["uid"]
    assert a.annotations is not None and a.annotations.read_only_hint is True
    assert b.annotations is not None and b.annotations.read_only_hint is False

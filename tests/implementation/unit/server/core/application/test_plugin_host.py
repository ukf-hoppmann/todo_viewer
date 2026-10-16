import asyncio
from dataclasses import dataclass
from typing import Any

import pytest
from fakes import FixedClock
from viewer.core.application.plugin import PluginContext, PluginDefinition, PluginHost
from viewer.core.domain.errors import NotFound, PluginSetupError
from viewer.core.domain.events import Event
from viewer.core.domain.operations import Operation
from viewer.core.domain.plugin import Subscription
from viewer.core.domain.settings import Settings
from viewer.core.infrastructure.event_bus import InProcessEventBus


@dataclass
class Nothing:
    pass


class NullScheduler:
    def schedule(self, owner: str, at: Any, callback: Any) -> None:
        pass


def host(defs: list[PluginDefinition], settings: Settings | None = None) -> tuple[PluginHost, InProcessEventBus]:
    bus = InProcessEventBus()
    return PluginHost(
        defs, clock=FixedClock(), events=bus, scheduler=NullScheduler(), settings=settings or Settings()
    ), bus


def test_builds_in_dependency_order_and_hands_required_services_over() -> None:
    contexts: dict[str, PluginContext] = {}

    def build(name: str):  # type: ignore[no-untyped-def]
        def _build(ctx: PluginContext) -> str:
            contexts[name] = ctx
            return f"services-{name}"

        return _build

    h, _ = host([PluginDefinition("b", build("b"), requires=("a",)), PluginDefinition("a", build("a"))])
    assert [p.definition.id for p in h.plugins] == ["a", "b"]
    assert contexts["b"].required == {"a": "services-a"}
    assert contexts["a"].required == {}
    assert h.services("b") == "services-b"


def test_plugin_settings_come_from_the_plugins_section() -> None:
    seen: list[Any] = []
    defn = PluginDefinition("a", lambda ctx: seen.append(dict(ctx.settings)))
    host([defn], Settings(plugins={"a": {"x": 1}}))
    assert seen == [{"x": 1}]


def test_invalid_list_prevents_start_with_all_problems() -> None:
    with pytest.raises(PluginSetupError) as err:
        host([PluginDefinition("a", lambda c: None, requires=("zzz",)), PluginDefinition("a", lambda c: None)])
    assert "verlangt unbekanntes Plugin 'zzz'" in str(err.value)
    assert "Plugin-ID 'a' kommt 2-mal vor" in str(err.value)


def test_call_runs_sync_and_async_handlers_with_services() -> None:
    sync_op = Operation("sync", "s", "read", Nothing, Nothing, lambda svc, i: (svc, i))

    async def ahandler(svc: Any, i: Any) -> tuple[Any, Any]:
        return (svc, i)

    async_op = Operation("asynch", "a", "read", Nothing, Nothing, ahandler)
    h, _ = host([PluginDefinition("a", lambda c: "svc", operations=(sync_op, async_op))])
    arg = Nothing()
    assert asyncio.run(h.call("a", "sync", arg)) == ("svc", arg)
    assert asyncio.run(h.call("a", "asynch", arg)) == ("svc", arg)


def test_unknown_operation_is_not_found() -> None:
    h, _ = host([PluginDefinition("a", lambda c: None)])
    with pytest.raises(NotFound):
        h.operation("a", "nope")
    with pytest.raises(NotFound):
        h.operation("zzz", "nope")


def test_subscriptions_are_wired_with_services() -> None:
    seen: list[tuple[Any, str]] = []
    sub = Subscription("x.*", lambda svc, ev: seen.append((svc, ev.topic)))
    _, bus = host([PluginDefinition("a", lambda c: "svc", subscriptions=(sub,))])
    bus.publish(Event("x.done"))
    bus.publish(Event("y.done"))
    assert seen == [("svc", "x.done")]

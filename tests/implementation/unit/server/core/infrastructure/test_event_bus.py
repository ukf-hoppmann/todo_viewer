from viewer.core.domain.events import Event
from viewer.core.infrastructure.event_bus import InProcessEventBus


def collect(bus: InProcessEventBus, topic: str) -> list[str]:
    seen: list[str] = []
    bus.subscribe(topic, lambda e: seen.append(e.topic))
    return seen


def test_exact_prefix_and_wildcard_subscriptions() -> None:
    bus = InProcessEventBus()
    exact = collect(bus, "a.changed")
    prefix = collect(bus, "a.*")
    everything = collect(bus, "*")
    bus.publish(Event("a.changed"))
    bus.publish(Event("a.other"))
    bus.publish(Event("b.changed"))
    assert exact == ["a.changed"]
    assert prefix == ["a.changed", "a.other"]
    assert everything == ["a.changed", "a.other", "b.changed"]


def test_unsubscribe_stops_delivery() -> None:
    bus = InProcessEventBus()
    seen: list[str] = []
    unsubscribe = bus.subscribe("*", lambda e: seen.append(e.topic))
    bus.publish(Event("a.x"))
    unsubscribe()
    unsubscribe()
    bus.publish(Event("a.y"))
    assert seen == ["a.x"]


def test_failing_subscriber_does_not_stop_others() -> None:
    bus = InProcessEventBus()

    def boom(event: Event) -> None:
        raise RuntimeError("kaputt")

    bus.subscribe("*", boom)
    seen = collect(bus, "*")
    bus.publish(Event("a.x"))
    assert seen == ["a.x"]

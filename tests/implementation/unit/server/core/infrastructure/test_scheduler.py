import asyncio
from collections.abc import Callable, Coroutine
from datetime import timedelta
from typing import Any

from fakes import FixedClock
from viewer.core.infrastructure.scheduler import AsyncioScheduler


def run(coro_factory: Callable[[], Coroutine[Any, Any, list[str]]]) -> list[str]:
    return asyncio.run(coro_factory())


def test_fires_once_after_delay_computed_from_the_clock() -> None:
    async def scenario() -> list[str]:
        clock = FixedClock()
        scheduler = AsyncioScheduler(clock)
        scheduler.start(asyncio.get_running_loop())
        fired: list[str] = []
        scheduler.schedule("alarms", clock.now() + timedelta(milliseconds=30), lambda: fired.append("a"))
        assert scheduler.pending_at("alarms") == clock.now() + timedelta(milliseconds=30)
        await asyncio.sleep(0.15)
        assert scheduler.pending_at("alarms") is None
        return fired

    assert run(scenario) == ["a"]


def test_new_schedule_replaces_the_old_one() -> None:
    async def scenario() -> list[str]:
        clock = FixedClock()
        scheduler = AsyncioScheduler(clock)
        scheduler.start(asyncio.get_running_loop())
        fired: list[str] = []
        scheduler.schedule("o", clock.now() + timedelta(milliseconds=30), lambda: fired.append("old"))
        scheduler.schedule("o", clock.now() + timedelta(milliseconds=60), lambda: fired.append("new"))
        await asyncio.sleep(0.2)
        return fired

    assert run(scenario) == ["new"]


def test_none_deletes_the_appointment_and_owners_are_independent() -> None:
    async def scenario() -> list[str]:
        clock = FixedClock()
        scheduler = AsyncioScheduler(clock)
        scheduler.start(asyncio.get_running_loop())
        fired: list[str] = []
        scheduler.schedule("a", clock.now() + timedelta(milliseconds=20), lambda: fired.append("a"))
        scheduler.schedule("b", clock.now() + timedelta(milliseconds=20), lambda: fired.append("b"))
        scheduler.schedule("a", None, lambda: fired.append("never"))
        await asyncio.sleep(0.15)
        return fired

    assert run(scenario) == ["b"]


def test_past_time_fires_immediately_and_failing_callback_is_contained() -> None:
    async def scenario() -> list[str]:
        clock = FixedClock()
        scheduler = AsyncioScheduler(clock)
        scheduler.start(asyncio.get_running_loop())
        fired: list[str] = []

        def boom() -> None:
            raise RuntimeError("x")

        scheduler.schedule("bad", clock.now() - timedelta(hours=1), boom)
        scheduler.schedule("ok", clock.now() - timedelta(hours=1), lambda: fired.append("ok"))
        await asyncio.sleep(0.05)
        return fired

    assert run(scenario) == ["ok"]


def test_appointments_set_before_start_fire_after_start() -> None:
    async def scenario() -> list[str]:
        clock = FixedClock()
        scheduler = AsyncioScheduler(clock)
        fired: list[str] = []
        scheduler.schedule("o", clock.now() + timedelta(milliseconds=10), lambda: fired.append("o"))
        await asyncio.sleep(0.05)
        assert fired == []
        scheduler.start(asyncio.get_running_loop())
        await asyncio.sleep(0.1)
        return fired

    assert run(scenario) == ["o"]


def test_stop_cancels_pending_timers() -> None:
    async def scenario() -> list[str]:
        clock = FixedClock()
        scheduler = AsyncioScheduler(clock)
        scheduler.start(asyncio.get_running_loop())
        fired: list[str] = []
        scheduler.schedule("o", clock.now() + timedelta(milliseconds=50), lambda: fired.append("o"))
        scheduler.stop()
        await asyncio.sleep(0.15)
        return fired

    assert run(scenario) == []

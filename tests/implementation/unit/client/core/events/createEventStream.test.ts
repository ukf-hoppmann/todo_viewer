import { beforeEach, describe, expect, it, vi } from "vitest";
import { createEventStream } from "../../../../../../client/src/core/events/createEventStream";
import { FakeEventSource, manualSchedule } from "../../../../../helpers/client/fakeEventSource";

function setup(topics: string[] = ["backlog.changed", "core.sync.state"]) {
	const onEvent = vi.fn();
	const onReconnected = vi.fn();
	const onProblem = vi.fn();
	const timers = manualSchedule();
	const stream = createEventStream({
		url: "/api/core/events",
		topics: () => topics,
		onEvent,
		onReconnected,
		onProblem,
		createSource: (url) => new FakeEventSource(url),
		schedule: timers.schedule,
		backoff: { initialMs: 1_000, maxMs: 8_000 },
	});
	return { stream, onEvent, onReconnected, onProblem, timers };
}

beforeEach(() => FakeEventSource.reset());

describe("createEventStream: events", () => {
	it("opens the address and listens for the topics of the handlers", () => {
		const { stream } = setup();

		stream.start();

		expect(FakeEventSource.instances).toHaveLength(1);
		expect(FakeEventSource.last.url).toBe("/api/core/events");
		expect(FakeEventSource.last.topics).toEqual(["backlog.changed", "core.sync.state"]);
	});

	it("hands a parsed event to the callback", () => {
		const { stream, onEvent } = setup();
		stream.start();
		FakeEventSource.last.open();

		FakeEventSource.last.send("backlog.changed", { project: "p1", uid: "u1" });

		expect(onEvent).toHaveBeenCalledExactlyOnceWith("backlog.changed", { project: "p1", uid: "u1" });
	});

	it("takes an empty payload as an empty object", () => {
		const { stream, onEvent } = setup();
		stream.start();

		FakeEventSource.last.send("core.sync.state", "");

		expect(onEvent).toHaveBeenCalledWith("core.sync.state", {});
	});

	it("reports an unreadable payload and goes on", () => {
		const { stream, onEvent, onProblem } = setup();
		stream.start();

		FakeEventSource.last.send("backlog.changed", "{kaputt");
		FakeEventSource.last.send("backlog.changed", { ok: true });

		expect(onProblem).toHaveBeenCalledTimes(1);
		expect(onEvent).toHaveBeenCalledExactlyOnceWith("backlog.changed", { ok: true });
	});

	it("starts only once", () => {
		const { stream } = setup();

		stream.start();
		stream.start();

		expect(FakeEventSource.instances).toHaveLength(1);
	});
});

describe("createEventStream: reconnecting", () => {
	it("does not report a reconnect for the first connection", () => {
		const { stream, onReconnected } = setup();
		stream.start();

		FakeEventSource.last.open();

		expect(onReconnected).not.toHaveBeenCalled();
	});

	it("closes the failed connection, waits with a growing delay, and reports the reconnect once it is open again", () => {
		const { stream, onReconnected, timers } = setup();
		stream.start();
		FakeEventSource.last.open();

		FakeEventSource.last.fail();
		expect(FakeEventSource.instances[0]!.closed).toBe(true);
		expect(timers.waits()).toEqual([1_000]);

		timers.runNext();
		expect(FakeEventSource.instances).toHaveLength(2);
		FakeEventSource.last.fail(); // the server is still away
		expect(timers.waits()).toEqual([1_000, 2_000]);

		timers.runNext();
		FakeEventSource.last.open();
		expect(onReconnected).toHaveBeenCalledTimes(1);
	});

	it("doubles the delay up to the maximum and starts again from the beginning after a success", () => {
		const { stream, timers } = setup();
		stream.start();
		for (let attempt = 0; attempt < 5; attempt++) {
			FakeEventSource.last.fail();
			timers.runNext();
		}
		expect(timers.waits()).toEqual([1_000, 2_000, 4_000, 8_000, 8_000]);

		FakeEventSource.last.open();
		FakeEventSource.last.fail();

		expect(timers.waits().at(-1)).toBe(1_000);
	});

	it("reports a reconnect only once for one interruption", () => {
		const { stream, onReconnected, timers } = setup();
		stream.start();
		FakeEventSource.last.fail();
		timers.runNext();
		FakeEventSource.last.open();
		FakeEventSource.last.open();

		expect(onReconnected).toHaveBeenCalledTimes(1);
	});

	it("reads the topics anew at each connection", () => {
		let topics = ["a.one"];
		const timers = manualSchedule();
		const stream = createEventStream({
			url: "/x",
			topics: () => topics,
			onEvent: vi.fn(),
			onReconnected: vi.fn(),
			createSource: (url) => new FakeEventSource(url),
			schedule: timers.schedule,
		});
		stream.start();
		topics = ["a.one", "b.two"];
		FakeEventSource.last.fail();
		timers.runNext();

		expect(FakeEventSource.last.topics).toEqual(["a.one", "b.two"]);
	});

	it("ignores events and errors of a connection that was replaced", () => {
		const { stream, onEvent, timers } = setup();
		stream.start();
		const old = FakeEventSource.last;
		old.fail();
		timers.runNext();

		old.send("backlog.changed", {});
		old.fail();

		expect(onEvent).not.toHaveBeenCalled();
		expect(timers.waits()).toEqual([1_000]);
	});
});

describe("createEventStream: stopping", () => {
	it("closes the connection and does not reconnect", () => {
		const { stream, timers } = setup();
		stream.start();
		FakeEventSource.last.fail();

		stream.stop();

		expect(timers.jobs.every((job) => job.cancelled)).toBe(true);
		expect(FakeEventSource.instances).toHaveLength(1);
	});

	it("closes an open connection", () => {
		const { stream } = setup();
		stream.start();

		stream.stop();

		expect(FakeEventSource.last.closed).toBe(true);
	});
});

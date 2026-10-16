import { describe, expect, it, vi } from "vitest";
import { createEventRouter, reconnectedTopic } from "../../../../../../client/src/core/events/createEventRouter";
import { startEvents } from "../../../../../../client/src/core/events/startEvents";
import { createLogging } from "../../../../../../client/src/core/logging/createLogging";
import { MemorySink } from "../../../../../../client/src/core/logging/MemorySink";
import { definePlugin } from "../../../../../../client/src/core/plugins/definePlugin";
import type { ActivePlugin, EventHandler } from "../../../../../../client/src/core/plugins/types";
import { FakeEventSource, manualSchedule } from "../../../../../helpers/client/fakeEventSource";

const i18n = { de: {}, en: {} };
const plugin = (id: string, eventHandlers?: Record<string, EventHandler>, api?: ActivePlugin["definition"]["api"]): ActivePlugin => ({
	id,
	definition: definePlugin({ i18n, eventHandlers, api }),
});

function logger() {
	const logging = createLogging();
	const sink = new MemorySink();
	logging.addSink(sink, { level: "debug" });
	logging.configure({});
	return { logger: logging.forOrigin("core"), sink };
}

describe("createEventRouter", () => {
	it("lists the topics of all handlers once, without the reconnect topic", () => {
		const router = createEventRouter(
			[plugin("a", { "x.one": vi.fn(), [reconnectedTopic]: vi.fn() }), plugin("b", { "x.one": vi.fn(), "y.two": vi.fn() }), plugin("c")],
			vi.fn(),
			logger().logger,
		);

		expect(router.topics()).toEqual(["x.one", "y.two"]);
	});

	it("calls the handlers of the plugins that declared the topic, with payload, dispatch and the own api", () => {
		const dispatch = vi.fn();
		const handlerA = vi.fn();
		const handlerB = vi.fn();
		const api = { reducerPath: "a.api", reducer: () => ({}), middleware: () => () => () => {} } as never;
		const router = createEventRouter([plugin("a", { "x.one": handlerA }, api), plugin("b", { "y.two": handlerB })], dispatch, logger().logger);

		router.handle("x.one", { n: 1 });

		expect(handlerA).toHaveBeenCalledExactlyOnceWith({ n: 1 }, { dispatch, api });
		expect(handlerB).not.toHaveBeenCalled();
	});

	it("logs a failing handler and still calls the others", () => {
		const { logger: log, sink } = logger();
		const good = vi.fn();
		const router = createEventRouter(
			[
				plugin("a", {
					"x.one": () => {
						throw new Error("kaputt");
					},
				}),
				plugin("b", { "x.one": good }),
			],
			vi.fn(),
			log,
		);

		router.handle("x.one", {});

		expect(good).toHaveBeenCalledTimes(1);
		const entries = sink.entries.filter((entry) => entry.level === "error");
		expect(entries).toHaveLength(1);
		expect(entries[0]!.message).toContain("plugin 'a' failed to handle 'x.one'");
	});
});

describe("startEvents", () => {
	it("opens the stream with the topics of the plugins and routes events and the reconnect to them", () => {
		FakeEventSource.reset();
		const onEvent = vi.fn();
		const onReconnect = vi.fn();
		const timers = manualSchedule();

		const events = startEvents({
			active: [plugin("a", { "x.one": onEvent, [reconnectedTopic]: onReconnect })],
			dispatch: vi.fn(),
			logger: logger().logger,
			stream: { createSource: (url) => new FakeEventSource(url), schedule: timers.schedule },
		});

		expect(FakeEventSource.last.url).toBe("/api/core/events");
		expect(FakeEventSource.last.topics).toEqual(["x.one"]);
		FakeEventSource.last.open();
		FakeEventSource.last.send("x.one", { v: 1 });
		expect(onEvent).toHaveBeenCalledWith({ v: 1 }, expect.anything());

		FakeEventSource.last.fail();
		timers.runNext();
		FakeEventSource.last.open();
		expect(onReconnect).toHaveBeenCalledTimes(1);

		events.stop();
		expect(FakeEventSource.last.closed).toBe(true);
	});
});

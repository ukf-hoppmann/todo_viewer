import { afterEach, describe, expect, it, vi } from "vitest";
import { createLogging } from "../../../../../src/core/logging/createLogging";
import { MemorySink } from "../../../../../src/core/logging/MemorySink";
import type { LogSink } from "../../../../../src/core/logging/types";

function setup(level: "debug" | "info" | "warn" | "error" = "debug") {
	const logging = createLogging();
	const sink = new MemorySink();
	logging.addSink(sink, { level });
	return { logging, sink };
}

afterEach(() => {
	vi.restoreAllMocks();
});

describe("createLogging: entries", () => {
	it("writes level, origin and the given fields into the entry", () => {
		const { logging, sink } = setup();
		const error = new Error("boom");
		const data = { form: 1 };

		logging.forOrigin("core").error({
			element: "core.save-button",
			action: "click",
			message: "POST failed",
			data,
			error,
		});

		expect(sink.entries).toHaveLength(1);
		expect(sink.entries[0]).toMatchObject({
			level: "error",
			origin: "core",
			element: "core.save-button",
			action: "click",
			message: "POST failed",
		});
		expect(sink.entries[0].data).toBe(data);
		expect(sink.entries[0].error).toBe(error);
	});

	it("accepts a plain string as message", () => {
		const { logging, sink } = setup();

		logging.forOrigin("core").info("Plugins geladen");

		expect(sink.entries[0]).toMatchObject({ level: "info", message: "Plugins geladen" });
	});

	it("adds id, time, session id and route automatically", () => {
		const { logging, sink } = setup();
		window.history.pushState({}, "", "/some/route");

		logging.forOrigin("core").warn("x");

		const [entry] = sink.entries;
		expect(entry.id).toMatch(/^[0-9a-f]{8}$/);
		expect(entry.sessionId).toMatch(/^[0-9a-f]{32}$/);
		expect(new Date(entry.time).toISOString()).toBe(entry.time);
		expect(entry.route).toBe("/some/route");
	});

	it("uses the same session id and different entry ids for all entries", () => {
		const { logging, sink } = setup();
		const log = logging.forOrigin("core");

		log.info("a");
		log.info("b");
		logging.forOrigin("variant-filter").info("c");

		expect(new Set(sink.entries.map((entry) => entry.sessionId)).size).toBe(1);
		expect(new Set(sink.entries.map((entry) => entry.id)).size).toBe(3);
	});

	it("uses a different session id per logging object", () => {
		const first = setup();
		const second = setup();

		first.logging.forOrigin("core").info("a");
		second.logging.forOrigin("core").info("a");

		expect(first.sink.entries[0].sessionId).not.toBe(second.sink.entries[0].sessionId);
	});

	it("returns the entry from every log method, even when no sink receives it", () => {
		const { logging, sink } = setup("error");
		const log = logging.forOrigin("core");

		const entry = log.debug("quiet");

		expect(entry).toMatchObject({ level: "debug", message: "quiet" });
		expect(entry.id).toMatch(/^[0-9a-f]{8}$/);
		expect(sink.entries).toHaveLength(0);
		expect(log.error("loud")).toBe(sink.entries[0]);
	});

	it("provides debug, info, warn and error with the matching level", () => {
		const { logging, sink } = setup();
		const log = logging.forOrigin("core");

		log.debug("a");
		log.info("b");
		log.warn("c");
		log.error("d");

		expect(sink.entries.map((entry) => entry.level)).toEqual(["debug", "info", "warn", "error"]);
	});
});

describe("createLogging: origin", () => {
	it("sets the origin per logger", () => {
		const { logging, sink } = setup();

		logging.forOrigin("core").info("a");
		logging.forOrigin("variant-filter").info("b");

		expect(sink.entries.map((entry) => entry.origin)).toEqual(["core", "variant-filter"]);
	});

	it("returns the same logger for the same origin", () => {
		const { logging } = setup();

		expect(logging.forOrigin("variant-filter")).toBe(logging.forOrigin("variant-filter"));
		expect(logging.forOrigin("variant-filter")).not.toBe(logging.forOrigin("core"));
	});

	it.each(["", "Core", "my_plugin", "-a", "a-", "a--b", "a b"])(
		"rejects the invalid origin %j",
		(origin) => {
			const { logging } = setup();

			expect(() => logging.forOrigin(origin)).toThrow();
		},
	);

	it("accepts kebab-case origins with digits", () => {
		const { logging } = setup();

		expect(() => logging.forOrigin("plugin-2a")).not.toThrow();
	});
});

describe("createLogging: levels", () => {
	it("passes entries at or above the level of the sink", () => {
		const { logging, sink } = setup("warn");
		const log = logging.forOrigin("core");

		log.debug("a");
		log.info("b");
		log.warn("c");
		log.error("d");

		expect(sink.entries.map((entry) => entry.message)).toEqual(["c", "d"]);
	});

	it("has a separate level per sink", () => {
		const logging = createLogging();
		const verbose = new MemorySink("verbose");
		const quiet = new MemorySink("quiet");
		logging.addSink(verbose, { level: "debug" });
		logging.addSink(quiet, { level: "error" });

		logging.forOrigin("core").warn("x");

		expect(verbose.entries).toHaveLength(1);
		expect(quiet.entries).toHaveLength(0);
	});

	it("lowers the level for one origin", () => {
		const logging = createLogging();
		const sink = new MemorySink();
		logging.addSink(sink, { level: "warn", origins: { "variant-filter": "debug" } });

		logging.forOrigin("variant-filter").debug("shown");
		logging.forOrigin("core").debug("hidden");
		logging.forOrigin("core").warn("shown too");

		expect(sink.entries.map((entry) => entry.message)).toEqual(["shown", "shown too"]);
	});

	it("raises the level for one origin", () => {
		const logging = createLogging();
		const sink = new MemorySink();
		logging.addSink(sink, { level: "debug", origins: { noisy: "error" } });

		logging.forOrigin("noisy").warn("hidden");
		logging.forOrigin("noisy").error("shown");
		logging.forOrigin("core").debug("shown too");

		expect(sink.entries.map((entry) => entry.message)).toEqual(["shown", "shown too"]);
	});

	it("reports the effective level with and without an origin override", () => {
		const logging = createLogging();
		logging.addSink(new MemorySink(), { level: "warn", origins: { "variant-filter": "debug" } });

		expect(logging.effectiveLevel("memory", "core")).toBe("warn");
		expect(logging.effectiveLevel("memory", "variant-filter")).toBe("debug");
	});

	it("reports no effective level for an unknown sink", () => {
		const { logging } = setup();

		expect(logging.effectiveLevel("backend", "core")).toBeUndefined();
	});
});

describe("createLogging: sinks", () => {
	it("hands the effective level and toLoggable to the sink", () => {
		const logging = createLogging();
		const write = vi.fn();
		logging.addSink({ name: "spy", write }, { level: "warn", origins: { a: "debug" } });

		logging.forOrigin("a").debug("x");

		const [, context] = write.mock.calls[0];
		expect(context.level).toBe("debug");
		expect(context.toLoggable({ n: 1 })).toEqual({ n: 1 });
	});

	it("stops writing to a removed sink", () => {
		const { logging, sink } = setup();
		logging.forOrigin("core").info("a");

		logging.removeSink("memory");
		logging.forOrigin("core").info("b");

		expect(sink.entries).toHaveLength(1);
		expect(logging.effectiveLevel("memory", "core")).toBeUndefined();
	});

	it("rejects a second sink with the same name", () => {
		const { logging } = setup();

		expect(() => logging.addSink(new MemorySink(), { level: "debug" })).toThrow();
	});

	it("does not let a throwing sink disturb the call or the other sinks", () => {
		const logging = createLogging();
		const error = vi.spyOn(console, "error").mockImplementation(() => {});
		const failing: LogSink = {
			name: "failing",
			write: () => {
				throw new Error("sink down");
			},
		};
		const memory = new MemorySink();
		logging.addSink(failing, { level: "debug" });
		logging.addSink(memory, { level: "debug" });

		expect(() => logging.forOrigin("core").info("a")).not.toThrow();

		expect(memory.entries).toHaveLength(1);
		expect(error).toHaveBeenCalledTimes(1);
	});

	it("reports a failing sink only once", () => {
		const logging = createLogging();
		const error = vi.spyOn(console, "error").mockImplementation(() => {});
		logging.addSink(
			{
				name: "failing",
				write: () => {
					throw new Error("sink down");
				},
			},
			{ level: "debug" },
		);

		logging.forOrigin("core").info("a");
		logging.forOrigin("core").info("b");

		expect(error).toHaveBeenCalledTimes(1);
	});
});

describe("MemorySink", () => {
	it("keeps entries and clears them", () => {
		const { logging, sink } = setup();
		logging.forOrigin("core").info("a");

		expect(sink.entries).toHaveLength(1);
		sink.clear();

		expect(sink.entries).toHaveLength(0);
	});

	it("has the name memory by default and accepts another name", () => {
		expect(new MemorySink().name).toBe("memory");
		expect(new MemorySink("other").name).toBe("other");
	});
});

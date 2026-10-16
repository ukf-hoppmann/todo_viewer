import { describe, expect, it } from "vitest";
import { createLogging } from "../../../../../../client/src/core/logging/createLogging";
import { MemorySink } from "../../../../../../client/src/core/logging/MemorySink";

describe("logging.configure", () => {
	it("replaces level and origin levels of a named sink", () => {
		const logging = createLogging();
		logging.addSink(new MemorySink(), { level: "warn", origins: { a: "debug" } });

		logging.configure({ outputs: { memory: { level: "info", origins: { b: "error" } } } });

		expect(logging.effectiveLevel("memory", "core")).toBe("info");
		expect(logging.effectiveLevel("memory", "a")).toBe("info");
		expect(logging.effectiveLevel("memory", "b")).toBe("error");
	});

	it("keeps sinks that the config does not name", () => {
		const logging = createLogging();
		logging.addSink(new MemorySink("one"), { level: "warn" });
		logging.addSink(new MemorySink("two"), { level: "error" });

		logging.configure({ outputs: { one: { level: "debug" } } });

		expect(logging.effectiveLevel("one", "core")).toBe("debug");
		expect(logging.effectiveLevel("two", "core")).toBe("error");
	});

	it("applies the configuration to later entries", () => {
		const logging = createLogging();
		const sink = new MemorySink();
		logging.addSink(sink, { level: "error" });
		logging.configure({});

		logging.configure({ outputs: { memory: { level: "debug" } } });
		logging.forOrigin("core").debug("now visible");

		expect(sink.entries).toHaveLength(1);
	});

	it("remembers the level for a sink that is added later", () => {
		const logging = createLogging();
		logging.configure({ outputs: { backend: { level: "error", origins: { a: "warn" } } } });

		logging.addSink(new MemorySink("backend"), { level: "debug" });

		expect(logging.effectiveLevel("backend", "core")).toBe("error");
		expect(logging.effectiveLevel("backend", "a")).toBe("warn");
	});

	it("applies the limits to what sinks receive through toLoggable", () => {
		const logging = createLogging();
		let converted: unknown;
		logging.addSink(
			{
				name: "spy",
				write: (entry, context) => {
					converted = context.toLoggable(entry.data);
				},
			},
			{ level: "debug" },
		);

		logging.configure({ limits: { entries: 1 } });
		logging.forOrigin("core").info({ data: [1, 2, 3] });

		expect(converted).toEqual([1, "[truncated]"]);
	});

	it("keeps the limits when a later configuration does not name them", () => {
		const logging = createLogging();
		let converted: unknown;
		logging.addSink(
			{
				name: "spy",
				write: (entry, context) => {
					converted = context.toLoggable(entry.data);
				},
			},
			{ level: "debug" },
		);
		logging.configure({ limits: { entries: 1 } });

		logging.configure({ outputs: { spy: { level: "debug" } } });
		logging.forOrigin("core").info({ data: [1, 2, 3] });

		expect(converted).toEqual([1, "[truncated]"]);
	});
});

describe("buffer before the first configure", () => {
	it("delivers remembered entries that the new level reaches, in order", () => {
		const logging = createLogging();
		const sink = new MemorySink();
		logging.addSink(sink, { level: "warn" });
		const log = logging.forOrigin("core");

		log.debug("d");
		log.warn("w");
		log.info("i");
		logging.configure({ outputs: { memory: { level: "debug" } } });

		// "w" was delivered at once; "d" and "i" follow in their original order.
		expect(sink.entries.map((entry) => entry.message)).toEqual(["w", "d", "i"]);
	});

	it("does not deliver an entry twice", () => {
		const logging = createLogging();
		const sink = new MemorySink();
		logging.addSink(sink, { level: "warn" });
		const log = logging.forOrigin("core");

		log.warn("once");
		log.debug("later");
		logging.configure({ outputs: { memory: { level: "debug" } } });

		expect(sink.entries.map((entry) => entry.message)).toEqual(["once", "later"]);
	});

	it("delivers only entries the new level reaches", () => {
		const logging = createLogging();
		const sink = new MemorySink();
		logging.addSink(sink, { level: "error" });
		const log = logging.forOrigin("core");

		log.debug("d");
		log.warn("w");
		logging.configure({ outputs: { memory: { level: "warn" } } });

		expect(sink.entries.map((entry) => entry.message)).toEqual(["w"]);
	});

	it("respects origin levels of the new configuration", () => {
		const logging = createLogging();
		const sink = new MemorySink();
		logging.addSink(sink, { level: "error" });
		logging.forOrigin("a").debug("from a");
		logging.forOrigin("b").debug("from b");

		logging.configure({ outputs: { memory: { level: "error", origins: { a: "debug" } } } });

		expect(sink.entries.map((entry) => entry.message)).toEqual(["from a"]);
	});

	it("serves each sink separately", () => {
		const logging = createLogging();
		const console = new MemorySink("console");
		const backend = new MemorySink("backend");
		logging.addSink(console, { level: "warn" });
		logging.addSink(backend, { level: "error" });
		logging.forOrigin("core").warn("w");

		logging.configure({ outputs: { backend: { level: "warn" } } });

		expect(console.entries).toHaveLength(1);
		expect(backend.entries.map((entry) => entry.message)).toEqual(["w"]);
	});

	it("keeps at most 500 entries and drops the oldest", () => {
		const logging = createLogging();
		const sink = new MemorySink();
		logging.addSink(sink, { level: "error" });
		const log = logging.forOrigin("core");

		for (let i = 0; i < 502; i++) log.debug(String(i));
		logging.configure({ outputs: { memory: { level: "debug" } } });

		expect(sink.entries).toHaveLength(500);
		expect(sink.entries[0].message).toBe("2");
		expect(sink.entries[499].message).toBe("501");
	});

	it("does not remember anything after the first configure", () => {
		const logging = createLogging();
		const sink = new MemorySink();
		logging.addSink(sink, { level: "error" });
		logging.configure({});

		logging.forOrigin("core").debug("lost");
		logging.configure({ outputs: { memory: { level: "debug" } } });

		expect(sink.entries).toHaveLength(0);
	});

	it("remembers entries that no sink received yet", () => {
		const logging = createLogging();
		logging.forOrigin("core").error("early");
		const sink = new MemorySink();
		logging.addSink(sink, { level: "debug" });

		logging.configure({});

		expect(sink.entries.map((entry) => entry.message)).toEqual(["early"]);
	});

	it("does not deliver remembered entries to a sink added after the first configure", () => {
		const logging = createLogging();
		logging.addSink(new MemorySink("console"), { level: "error" });
		logging.forOrigin("core").debug("early");
		logging.configure({});

		const backend = new MemorySink("backend");
		logging.addSink(backend, { level: "debug" });
		logging.configure({ outputs: { backend: { level: "debug" } } });

		expect(backend.entries).toHaveLength(0);
	});
});

import { afterEach, describe, expect, it, vi } from "vitest";
import { ConsoleSink } from "../../../../../../client/src/core/logging/ConsoleSink";
import { createLogging } from "../../../../../../client/src/core/logging/createLogging";
import type { LogLevel } from "../../../../../../client/src/core/logging/types";

function setup(level: LogLevel, origins?: Record<string, LogLevel>) {
	const spies = {
		debug: vi.spyOn(console, "debug").mockImplementation(() => {}),
		info: vi.spyOn(console, "info").mockImplementation(() => {}),
		warn: vi.spyOn(console, "warn").mockImplementation(() => {}),
		error: vi.spyOn(console, "error").mockImplementation(() => {}),
	};
	const logging = createLogging();
	logging.addSink(new ConsoleSink(), { level, origins });
	return { logging, spies };
}

afterEach(() => {
	vi.restoreAllMocks();
});

describe("ConsoleSink", () => {
	it("is named console", () => {
		expect(new ConsoleSink().name).toBe("console");
	});

	it.each(["debug", "info", "warn", "error"] as const)(
		"writes %s entries with the console method of the same name",
		(level) => {
			const { logging, spies } = setup("debug");

			logging.forOrigin("core")[level]("text");

			for (const [name, spy] of Object.entries(spies)) {
				expect(spy).toHaveBeenCalledTimes(name === level ? 1 : 0);
			}
		},
	);

	it("writes time, level, origin, element, action and message in the first line", () => {
		const { logging, spies } = setup("debug");

		logging.forOrigin("variant-filter").info({
			element: "variant-filter.apply",
			action: "click",
			message: "applied",
		});

		expect(spies.info.mock.calls[0][0]).toMatch(
			/^\d{2}:\d{2}:\d{2}\.\d{3} INFO variant-filter \| variant-filter\.apply \| click \| applied$/,
		);
	});

	it("leaves out empty parts", () => {
		const { logging, spies } = setup("debug");

		logging.forOrigin("core").warn("only message");
		logging.forOrigin("core").warn({ action: "load-config" });

		expect(spies.warn.mock.calls[0][0]).toMatch(/ WARN core \| only message$/);
		expect(spies.warn.mock.calls[1][0]).toMatch(/ WARN core \| load-config$/);
	});

	it("writes the entry id after the first line", () => {
		const { logging, spies } = setup("debug");

		const entry = logging.forOrigin("core").info("a");

		expect(spies.info.mock.calls[0][1]).toBe(`id=${entry.id}`);
	});

	it("always passes the error object", () => {
		const { logging, spies } = setup("error");
		const error = new Error("boom");

		logging.forOrigin("core").error({ message: "failed", error });

		expect(spies.error.mock.calls[0]).toContain(error);
	});

	it("passes no data at a level above debug", () => {
		const { logging, spies } = setup("info");

		logging.forOrigin("core").error({ message: "failed", data: { secret: 1 } });

		expect(spies.error.mock.calls[0]).toHaveLength(2);
	});

	it("passes a converted copy of data at level debug, also for warn and error entries", () => {
		const { logging, spies } = setup("debug");
		const data: Record<string, unknown> = { a: 1 };
		data.self = data;

		logging.forOrigin("core").warn({ data });
		data.a = 2;

		const copy = spies.warn.mock.calls[0][2];
		expect(copy).toEqual({ a: 1, self: "[Circular]" });
		expect(copy).not.toBe(data);
	});

	it("decides about data per origin from the effective level", () => {
		const { logging, spies } = setup("warn", { "variant-filter": "debug" });

		logging.forOrigin("variant-filter").error({ data: { x: 1 } });
		logging.forOrigin("core").error({ data: { x: 1 } });

		expect(spies.error.mock.calls[0][2]).toEqual({ x: 1 });
		expect(spies.error.mock.calls[1]).toHaveLength(2);
	});

	it("does not write entries below its level", () => {
		const { logging, spies } = setup("warn");

		logging.forOrigin("core").info("hidden");

		expect(spies.info).not.toHaveBeenCalled();
	});
});

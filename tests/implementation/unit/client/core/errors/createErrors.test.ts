import { describe, expect, it, vi } from "vitest";
import { createErrors } from "../../../../../../client/src/core/errors/createErrors";
import { createLogging } from "../../../../../../client/src/core/logging/createLogging";
import { MemorySink } from "../../../../../../client/src/core/logging/MemorySink";
import type { LogLevel } from "../../../../../../client/src/core/logging/types";
import { createModals } from "../../../../../../client/src/core/modals/createModals";
import type { DetailRow } from "../../../../../../client/src/core/modals/types";

function setup(consoleLevel: LogLevel = "warn", consoleOrigins?: Record<string, LogLevel>) {
	const logging = createLogging();
	const sink = new MemorySink("console");
	logging.addSink(sink, { level: consoleLevel, origins: consoleOrigins });
	const modals = createModals();
	return { logging, sink, modals, errors: createErrors({ logging, modals }) };
}

function shownAlert(modals: ReturnType<typeof createModals>) {
	const pending = modals.getSnapshot();
	if (pending?.kind !== "alert") throw new Error("no alert pending");
	return pending;
}

function detail(rows: DetailRow[] | undefined, key: string) {
	return rows?.find((row) => typeof row.label !== "string" && row.label.key === `reportError.details.${key}`)?.value;
}

describe("reportError: one call, one entry, one alert", () => {
	it("writes exactly one log entry and shows exactly one alert", async () => {
		const { errors, sink, modals } = setup("debug");

		void errors.forOrigin("core")({ userMessage: { key: "x.y" } });

		expect(sink.entries).toHaveLength(1);
		const pending = shownAlert(modals);
		pending.close();
		expect(modals.getSnapshot()).toBeUndefined();
	});

	it("writes the entry with origin and level error by default", () => {
		const { errors, sink } = setup();

		void errors.forOrigin("variant-filter")({ userMessage: "Text" });

		expect(sink.entries[0]).toMatchObject({ origin: "variant-filter", level: "error" });
	});

	it("uses level warn and the severity warning for a warning", () => {
		const { errors, sink, modals } = setup("debug");

		void errors.forOrigin("core")({ userMessage: "Text", severity: "warning" });

		expect(sink.entries[0].level).toBe("warn");
		expect(shownAlert(modals).request.severity).toBe("warning");
	});

	it("uses the severity error for the alert by default", () => {
		const { errors, modals } = setup();

		void errors.forOrigin("core")({ userMessage: "Text" });

		expect(shownAlert(modals).request.severity).toBe("error");
	});
});

describe("reportError: log entry", () => {
	it("takes over element, action, error and data", () => {
		const { errors, sink } = setup();
		const error = new Error("boom");
		const data = { form: 1 };

		void errors.forOrigin("core")({
			element: "core.save-button",
			action: "click",
			userMessage: "Text",
			message: "POST failed",
			error,
			data,
		});

		const [entry] = sink.entries;
		expect(entry).toMatchObject({ element: "core.save-button", action: "click", message: "POST failed" });
		expect(entry.error).toBe(error);
		expect(entry.data).toBe(data);
	});

	it("stores the i18n key of the user message", () => {
		const { errors, sink } = setup();

		void errors.forOrigin("core")({ userMessage: { key: "process-manager:errors.save", params: { n: 1 } } });

		expect(sink.entries[0].userMessage).toBe("process-manager:errors.save");
	});

	it("stores a finished user message as text", () => {
		const { errors, sink } = setup();

		void errors.forOrigin("core")({ userMessage: "Server says no" });

		expect(sink.entries[0].userMessage).toBe("Server says no");
	});

	it("uses the key or text of the user message as message when none is given", () => {
		const { errors, sink } = setup();

		void errors.forOrigin("core")({ userMessage: { key: "a.b" } });
		void errors.forOrigin("core")({ userMessage: "Finished text" });

		expect(sink.entries.map((entry) => entry.message)).toEqual(["a.b", "Finished text"]);
	});
});

describe("reportError: alert", () => {
	it("passes title and user message on, as keys or finished texts", () => {
		const { errors, modals } = setup();

		void errors.forOrigin("core")({
			title: { key: "modals.close" },
			userMessage: { key: "x.y", params: { n: 2 } },
		});

		expect(shownAlert(modals).request).toMatchObject({
			title: { key: "modals.close" },
			message: { key: "x.y", params: { n: 2 } },
		});
	});

	it("leaves the title open so that the default title of the severity applies", () => {
		const { errors, modals } = setup();

		void errors.forOrigin("core")({ userMessage: "x" });

		expect(shownAlert(modals).request.title).toBeUndefined();
	});

	it("shows time, error id and session id of the log entry", () => {
		const { errors, sink, modals } = setup();

		void errors.forOrigin("core")({ userMessage: "x", error: new Error("boom") });

		const [entry] = sink.entries;
		const rows = shownAlert(modals).request.details;
		const time = new Date(entry.time);
		const pad = (value: number) => String(value).padStart(2, "0");
		expect(detail(rows, "errorId")).toBe(entry.id);
		expect(detail(rows, "sessionId")).toBe(entry.sessionId);
		expect(detail(rows, "time")).toBe(
			`${time.getFullYear()}-${pad(time.getMonth() + 1)}-${pad(time.getDate())} ${pad(time.getHours())}:${pad(time.getMinutes())}:${pad(time.getSeconds())}`,
		);
		expect(detail(rows, "error")).toBe("Error: boom");
	});

	it("shows an error that is not an Error object as text", () => {
		const { errors, modals } = setup();

		void errors.forOrigin("core")({ userMessage: "x", error: "plain" });

		expect(detail(shownAlert(modals).request.details, "error")).toBe("plain");
	});

	it("leaves out the error line without an error", () => {
		const { errors, modals } = setup();

		void errors.forOrigin("core")({ userMessage: "x" });

		expect(detail(shownAlert(modals).request.details, "error")).toBeUndefined();
	});
});

describe("reportError: stack trace", () => {
	it("is left out while the console level is above debug", () => {
		const { errors, modals } = setup("warn");

		void errors.forOrigin("core")({ userMessage: "x", error: new Error("boom") });

		expect(detail(shownAlert(modals).request.details, "stack")).toBeUndefined();
	});

	it("is shown while the console level is debug", () => {
		const { errors, modals } = setup("debug");
		const error = new Error("boom");

		void errors.forOrigin("core")({ userMessage: "x", error });

		expect(detail(shownAlert(modals).request.details, "stack")).toBe(error.stack);
	});

	it("follows the console level of the origin of the error", () => {
		const { errors, modals } = setup("warn", { "variant-filter": "debug" });
		const error = new Error("boom");

		void errors.forOrigin("core")({ userMessage: "x", error });
		expect(detail(shownAlert(modals).request.details, "stack")).toBeUndefined();
		shownAlert(modals).close();

		void errors.forOrigin("variant-filter")({ userMessage: "x", error });
		expect(detail(shownAlert(modals).request.details, "stack")).toBe(error.stack);
	});

	it("is left out when there is no console output", () => {
		const logging = createLogging();
		const modals = createModals();
		const errors = createErrors({ logging, modals });

		void errors.forOrigin("core")({ userMessage: "x", error: new Error("boom") });

		expect(detail(shownAlert(modals).request.details, "stack")).toBeUndefined();
	});
});

describe("reportError: result and origin", () => {
	it("resolves only when the user closes the alert", async () => {
		const { errors, modals } = setup();
		const done = vi.fn();

		const promise = errors.forOrigin("core")({ userMessage: "x" }).then(done);
		await Promise.resolve();
		expect(done).not.toHaveBeenCalled();

		shownAlert(modals).close();
		await promise;

		expect(done).toHaveBeenCalledTimes(1);
	});

	it("queues several reports as separate alerts without merging them", () => {
		const { errors, sink, modals } = setup();
		const report = errors.forOrigin("core");

		void report({ userMessage: "same" });
		void report({ userMessage: "same" });

		expect(sink.entries).toHaveLength(2);
		shownAlert(modals).close();
		expect(shownAlert(modals).request.message).toBe("same");
	});

	it("returns the same function for the same origin", () => {
		const { errors } = setup();

		expect(errors.forOrigin("variant-filter")).toBe(errors.forOrigin("variant-filter"));
		expect(errors.forOrigin("variant-filter")).not.toBe(errors.forOrigin("core"));
	});

	it.each(["", "Core", "my_plugin", "a b"])("rejects the invalid origin %j", (origin) => {
		const { errors } = setup();

		expect(() => errors.forOrigin(origin)).toThrow();
	});
});

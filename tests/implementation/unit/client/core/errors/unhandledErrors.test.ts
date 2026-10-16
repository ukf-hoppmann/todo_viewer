import { afterEach, describe, expect, it, vi } from "vitest";
import { createErrors } from "../../../../../../client/src/core/errors/createErrors";
import { createUnhandledErrors } from "../../../../../../client/src/core/errors/createUnhandledErrors";
import { installGlobalErrorHandlers } from "../../../../../../client/src/core/errors/installGlobalErrorHandlers";
import { createLogging } from "../../../../../../client/src/core/logging/createLogging";
import { MemorySink } from "../../../../../../client/src/core/logging/MemorySink";
import { createModals } from "../../../../../../client/src/core/modals/createModals";

function setup() {
	const logging = createLogging();
	const sink = new MemorySink("memory");
	logging.addSink(sink, { level: "debug" });
	const modals = createModals();
	const unhandled = createUnhandledErrors({ errors: createErrors({ logging, modals }), logging });
	return { logging, sink, modals, unhandled };
}

function closeAlert(modals: ReturnType<typeof createModals>) {
	const pending = modals.getSnapshot();
	if (pending?.kind !== "alert") throw new Error("no alert pending");
	pending.close();
}

async function settle() {
	await Promise.resolve();
	await Promise.resolve();
}

function dispatchRejection(reason: unknown) {
	const event = new Event("unhandledrejection");
	Object.assign(event, { reason });
	window.dispatchEvent(event);
}

describe("unhandled errors: one error, one log entry, one hint", () => {
	it("logs the error with origin, action and data and shows one hint", () => {
		const { unhandled, sink, modals } = setup();
		const error = new Error("kaputt");

		unhandled.report(error, { origin: "variant-filter", action: "render", data: { componentStack: "at X" } });

		expect(sink.entries).toHaveLength(1);
		expect(sink.entries[0]).toMatchObject({
			level: "error",
			origin: "variant-filter",
			action: "render",
			error,
			data: { componentStack: "at X" },
			userMessage: "errors.unexpected",
		});
		const pending = modals.getSnapshot();
		expect(pending).toMatchObject({ kind: "alert", request: { message: { key: "errors.unexpected" } } });
	});

	it("uses the origin core without one", () => {
		const { unhandled, sink } = setup();

		unhandled.report(new Error("x"), { action: "unhandled-error" });

		expect(sink.entries[0]?.origin).toBe("core");
	});

	it("reports the same error object only once, also by another way", () => {
		const { unhandled, sink, modals } = setup();
		const error = new Error("doppelt");

		unhandled.report(error, { action: "render" });
		closeAlert(modals);
		unhandled.report(error, { action: "unhandled-error" });

		expect(sink.entries).toHaveLength(1);
		expect(modals.getSnapshot()).toBeUndefined();
	});

	it("only logs further errors while a hint is open", () => {
		const { unhandled, sink, modals } = setup();

		unhandled.report(new Error("eins"), { action: "unhandled-error" });
		unhandled.report(new Error("zwei"), { action: "unhandled-error" });
		unhandled.report(new Error("drei"), { action: "unhandled-error" });

		expect(sink.entries).toHaveLength(3);
		expect(sink.entries.every((entry) => entry.level === "error")).toBe(true);
		closeAlert(modals);
		expect(modals.getSnapshot()).toBeUndefined();
	});

	it("shows a hint again after the previous one was closed", async () => {
		const { unhandled, sink, modals } = setup();

		unhandled.report(new Error("eins"), { action: "unhandled-error" });
		closeAlert(modals);
		await settle();
		unhandled.report(new Error("zwei"), { action: "unhandled-error" });

		expect(sink.entries).toHaveLength(2);
		expect(modals.getSnapshot()?.kind).toBe("alert");
	});

	it("still reports values that are no objects, each time", () => {
		const { unhandled, sink } = setup();

		unhandled.report("text", { action: "unhandled-rejection" });
		unhandled.report("text", { action: "unhandled-rejection" });

		expect(sink.entries).toHaveLength(2);
	});
});

describe("installGlobalErrorHandlers", () => {
	let remove: (() => void) | undefined;

	afterEach(() => {
		remove?.();
		remove = undefined;
	});

	it("reports an error event with the error object once", () => {
		const { unhandled, sink, modals } = setup();
		remove = installGlobalErrorHandlers(unhandled);
		const error = new Error("im Handler");

		window.dispatchEvent(new ErrorEvent("error", { error, message: "im Handler" }));

		expect(sink.entries).toHaveLength(1);
		expect(sink.entries[0]).toMatchObject({ origin: "core", action: "unhandled-error", error });
		expect(modals.getSnapshot()?.kind).toBe("alert");
	});

	it("keeps message, file and line of an error event without an error object", () => {
		const { unhandled, sink } = setup();
		remove = installGlobalErrorHandlers(unhandled);

		window.dispatchEvent(new ErrorEvent("error", { message: "Script error.", filename: "app.js", lineno: 12, colno: 3 }));

		expect(sink.entries).toHaveLength(1);
		expect(sink.entries[0]).toMatchObject({
			action: "unhandled-error",
			data: { message: "Script error.", filename: "app.js", lineno: 12, colno: 3 },
		});
	});

	it("reports a rejected promise once", () => {
		const { unhandled, sink, modals } = setup();
		remove = installGlobalErrorHandlers(unhandled);
		const reason = new Error("abgelehnt");

		dispatchRejection(reason);

		expect(sink.entries).toHaveLength(1);
		expect(sink.entries[0]).toMatchObject({ origin: "core", action: "unhandled-rejection", error: reason });
		expect(modals.getSnapshot()?.kind).toBe("alert");
	});

	it("reports the same error object from both events only once", () => {
		const { unhandled, sink } = setup();
		remove = installGlobalErrorHandlers(unhandled);
		const error = new Error("zweimal");

		window.dispatchEvent(new ErrorEvent("error", { error }));
		dispatchRejection(error);

		expect(sink.entries).toHaveLength(1);
	});

	it("removes exactly the listeners it added", () => {
		const { unhandled } = setup();
		const add = vi.spyOn(window, "addEventListener");
		const removeListener = vi.spyOn(window, "removeEventListener");

		installGlobalErrorHandlers(unhandled)();

		const added = add.mock.calls.map(([type, listener]) => [type, listener]);
		const removed = removeListener.mock.calls.map(([type, listener]) => [type, listener]);
		expect(added.map(([type]) => type)).toEqual(["error", "unhandledrejection"]);
		expect(removed).toEqual(added);
		vi.restoreAllMocks();
	});

	it("stops reporting a rejected promise after the listeners were removed", () => {
		const { unhandled, sink } = setup();

		installGlobalErrorHandlers(unhandled)();
		dispatchRejection(new Error("y"));

		expect(sink.entries).toHaveLength(0);
	});
});

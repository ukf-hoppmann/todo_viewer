import { afterEach, describe, expect, it, vi } from "vitest";
import { ConfigError } from "../../../../../src/core/config/ConfigError";
import { loadPluginSelection } from "../../../../../src/core/config/loadPluginSelection";
import type { ConfigSource } from "../../../../../src/core/config/types";
import { createErrors } from "../../../../../src/core/errors/createErrors";
import { createLogging } from "../../../../../src/core/logging/createLogging";
import { MemorySink } from "../../../../../src/core/logging/MemorySink";
import { createModals } from "../../../../../src/core/modals/createModals";

function setup(source: ConfigSource) {
	const logging = createLogging();
	const sink = new MemorySink("console");
	logging.addSink(sink, { level: "warn" });
	const modals = createModals();
	const errors = createErrors({ logging, modals });
	return { sink, modals, run: () => loadPluginSelection({ source, errors }) };
}

const valid = (selection: unknown): ConfigSource => ({ load: async () => selection });
const failing = (error: unknown): ConfigSource => ({ load: async () => Promise.reject(error) });

function shownAlert(modals: ReturnType<typeof createModals>) {
	const pending = modals.getSnapshot();
	if (pending?.kind !== "alert") throw new Error("no alert pending");
	return pending.request;
}

describe("loadPluginSelection: valid selection", () => {
	afterEach(() => {
		vi.unstubAllGlobals();
	});

	it("returns the selection and shows no dialog", async () => {
		const selection = { plugins: { example: { enabled: true } }, navigation: { start: "example/overview" } };
		const { run, modals } = setup(valid(selection));

		await expect(run()).resolves.toEqual(selection);

		expect(modals.getSnapshot()).toBeUndefined();
	});

	it("requests /plugins.json without a cache by default", async () => {
		const fetchMock = vi.fn(async () => new Response(JSON.stringify({ plugins: {} }), { status: 200 }));
		vi.stubGlobal("fetch", fetchMock);

		await expect(loadPluginSelection()).resolves.toEqual({ plugins: {} });

		expect(fetchMock).toHaveBeenCalledWith("/plugins.json", { cache: "no-store" });
	});
});

describe("loadPluginSelection: selection that cannot be used", () => {
	it("returns nothing, so that the application does not start", async () => {
		await expect(setup(valid({ plugins: 5 })).run()).resolves.toBeUndefined();
	});

	it("reports an invalid selection once with the action load-plugin-selection: one log entry with code and details, one alert", async () => {
		const { run, sink, modals } = setup(valid({ plugins: { example: {} } }));

		await run();

		expect(sink.entries).toHaveLength(1);
		const entry = sink.entries[0];
		expect(entry).toMatchObject({
			level: "error",
			origin: "core",
			action: "load-plugin-selection",
			userMessage: "config.invalid",
			data: [{ path: "/plugins/example", message: "must have required property 'enabled'" }],
		});
		expect((entry?.error as ConfigError).code).toBe("config-invalid");
		expect(shownAlert(modals)).toMatchObject({ severity: "error", message: { key: "config.invalid" } });
	});

	it("reports an unreachable source with its code", async () => {
		const { run, sink, modals } = setup(failing(new ConfigError("config-unreachable", "HTTP 404")));

		await expect(run()).resolves.toBeUndefined();

		expect((sink.entries[0]?.error as ConfigError).code).toBe("config-unreachable");
		expect(shownAlert(modals).message).toEqual({ key: "config.invalid" });
	});

	it("reports a source that is no JSON with its code", async () => {
		const { run, sink } = setup(failing(new ConfigError("config-not-json", "no json")));

		await run();

		expect((sink.entries[0]?.error as ConfigError).code).toBe("config-not-json");
	});

	it("does not wait for the user to close the alert", async () => {
		const { run, modals } = setup(valid({}));

		await run();

		expect(modals.getSnapshot()?.kind).toBe("alert");
	});
});

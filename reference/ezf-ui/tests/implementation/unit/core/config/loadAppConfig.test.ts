import { describe, expect, it, vi } from "vitest";
import { ConfigError } from "../../../../../src/core/config/ConfigError";
import { loadAppConfig } from "../../../../../src/core/config/loadAppConfig";
import type { ConfigSource } from "../../../../../src/core/config/types";
import { createErrors } from "../../../../../src/core/errors/createErrors";
import { createLogging } from "../../../../../src/core/logging/createLogging";
import { MemorySink } from "../../../../../src/core/logging/MemorySink";
import { createModals } from "../../../../../src/core/modals/createModals";

function setup(source: ConfigSource) {
	const logging = createLogging();
	const sink = new MemorySink("console");
	logging.addSink(sink, { level: "warn" });
	const configure = vi.spyOn(logging, "configure");
	const modals = createModals();
	const errors = createErrors({ logging, modals });
	return { logging, sink, configure, modals, run: () => loadAppConfig({ source, logging, errors }) };
}

const api = { url: "https://backend.et.localhost" };
const valid = (config: unknown): ConfigSource => ({ load: async () => config });
const failing = (error: unknown): ConfigSource => ({ load: async () => Promise.reject(error) });

function shownAlert(modals: ReturnType<typeof createModals>) {
	const pending = modals.getSnapshot();
	if (pending?.kind !== "alert") throw new Error("no alert pending");
	return pending.request;
}

describe("loadAppConfig: valid config", () => {
	it("returns the config", async () => {
		const config = { api };

		await expect(setup(valid(config)).run()).resolves.toEqual(config);
	});

	it("hands the section logging to logging.configure", async () => {
		const logging = { outputs: { console: { level: "debug" as const } } };
		const { run, configure, logging: object } = setup(valid({ api, logging }));

		await run();

		expect(configure).toHaveBeenCalledExactlyOnceWith(logging);
		expect(object.effectiveLevel("console", "core")).toBe("debug");
	});

	it("still calls logging.configure without the section, so that the standard levels apply", async () => {
		const { run, configure, logging } = setup(valid({ api }));

		await run();

		expect(configure).toHaveBeenCalledExactlyOnceWith({});
		expect(logging.effectiveLevel("console", "core")).toBe("warn");
	});

	it("shows no dialog", async () => {
		const { run, modals } = setup(valid({ api }));

		await run();

		expect(modals.getSnapshot()).toBeUndefined();
	});
});

describe("loadAppConfig: config that cannot be used", () => {
	it("returns nothing, so that the application does not start", async () => {
		await expect(setup(valid({ api: 5 })).run()).resolves.toBeUndefined();
	});

	it("reports an invalid config once: one log entry with code and details, one alert", async () => {
		const { run, sink, modals } = setup(valid({ api: {} }));

		await run();

		expect(sink.entries).toHaveLength(1);
		const entry = sink.entries[0];
		expect(entry).toMatchObject({
			level: "error",
			origin: "core",
			action: "load-config",
			userMessage: "config.invalid",
			data: [{ path: "/api", message: "must have required property 'url'" }],
		});
		expect(entry?.error).toBeInstanceOf(ConfigError);
		expect((entry?.error as ConfigError).code).toBe("config-invalid");
		expect(shownAlert(modals)).toMatchObject({ severity: "error", message: { key: "config.invalid" } });
	});

	it("shows code and details of the error in the technical details of the alert", async () => {
		const { run, modals } = setup(valid({ api: {} }));

		await run();

		const text = (shownAlert(modals).details ?? []).map((row) => row.value).join("\n");
		expect(text).toContain("config-invalid");
		expect(text).toContain("/api: must have required property 'url'");
	});

	it("reports an unreachable source with its code", async () => {
		const { run, sink, modals } = setup(failing(new ConfigError("config-unreachable", "HTTP 404")));

		await expect(run()).resolves.toBeUndefined();

		expect((sink.entries[0]?.error as ConfigError).code).toBe("config-unreachable");
		expect(shownAlert(modals).message).toEqual({ key: "config.invalid" });
	});

	it("does not call logging.configure", async () => {
		const { run, configure } = setup(valid({}));

		await run();

		expect(configure).not.toHaveBeenCalled();
	});

	it("does not wait for the user to close the alert", async () => {
		const { run, modals } = setup(valid({}));

		await run();

		expect(modals.getSnapshot()?.kind).toBe("alert");
	});
});

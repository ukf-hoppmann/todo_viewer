import { describe, expect, it, vi } from "vitest";
import { createPluginApi } from "../../../../../src/core/api/createPluginApi";
import { ConfigError } from "../../../../../src/core/config/ConfigError";
import type { PluginSelection } from "../../../../../src/core/config/types";
import { initI18n } from "../../../../../src/core/i18n/initI18n";
import { createLogging } from "../../../../../src/core/logging/createLogging";
import { MemorySink } from "../../../../../src/core/logging/MemorySink";
import { createPluginRegistry } from "../../../../../src/core/plugins/createPluginRegistry";
import { definePlugin } from "../../../../../src/core/plugins/definePlugin";
import type { PluginCatalogue } from "../../../../../src/core/plugins/types";

function texts(id: string) {
	return { de: { title: `${id} de` }, en: { title: `${id} en` }, fr: { title: `${id} fr` } };
}

/** Catalogue entry whose loader returns a valid definition. */
function plugin(id: string, ...requires: string[]) {
	return { manifest: { requires }, load: vi.fn(async () => ({ plugin: definePlugin({ i18n: texts(id) }) })) };
}

function enabled(...ids: string[]): PluginSelection {
	return { plugins: Object.fromEntries(ids.map((id) => [id, { enabled: true }])) };
}

async function setup(config: PluginSelection, catalogue: PluginCatalogue) {
	const i18n = await initI18n({ lng: "en" });
	const logging = createLogging();
	const sink = new MemorySink();
	logging.addSink(sink, { level: "debug" });
	const registry = await createPluginRegistry({ config, catalogue, i18n, logger: logging.forOrigin("core") });
	const statusOf = (id: string) => registry.statuses().find((status) => status.id === id);
	const entriesFor = (id: string) =>
		sink.entries.filter((entry) => (entry.data as { plugin?: string } | undefined)?.plugin === id);
	return { registry, i18n, sink, statusOf, entriesFor };
}

describe("createPluginRegistry: loading", () => {
	it("loads and activates the plugins that are switched on", async () => {
		const catalogue = { a: plugin("a", "b"), b: plugin("b"), off: plugin("off") };
		const { registry, statusOf } = await setup(enabled("a", "b"), catalogue);

		expect(registry.active().map((active) => active.id)).toEqual(["b", "a"]);
		expect(statusOf("a")).toEqual({ id: "a", status: "active" });
		expect(statusOf("off")).toEqual({ id: "off", status: "disabled" });
	});

	it("never calls the loader of a plugin that is not active", async () => {
		const catalogue = { off: plugin("off"), blocked: plugin("blocked", "off"), broken: plugin("broken", "ghost") };
		await setup(enabled("blocked", "broken"), catalogue);

		expect(catalogue.off.load).not.toHaveBeenCalled();
		expect(catalogue.blocked.load).not.toHaveBeenCalled();
		expect(catalogue.broken.load).not.toHaveBeenCalled();
	});

	it("rejects config ids without a plugin before loading anything", async () => {
		const catalogue = { a: plugin("a") };

		await expect(setup(enabled("a", "ghost"), catalogue)).rejects.toThrow(ConfigError);
		expect(catalogue.a.load).not.toHaveBeenCalled();
	});

	it("returns the status of every plugin", async () => {
		const { registry } = await setup(enabled("a"), { a: plugin("a"), b: plugin("b") });

		expect(registry.statuses().map((status) => status.id)).toEqual(["a", "b"]);
	});
});

describe("createPluginRegistry: failures while loading", () => {
	it("marks a plugin whose import fails as import-failed and blocks its dependents", async () => {
		const error = new Error("chunk missing");
		const catalogue = {
			a: plugin("a", "b"),
			b: { manifest: { requires: [] }, load: vi.fn(async () => Promise.reject(error)) },
			c: plugin("c"),
		};
		const { registry, statusOf } = await setup(enabled("a", "b", "c"), catalogue);

		expect(statusOf("b")).toMatchObject({ status: "failed", code: "import-failed", error });
		expect(statusOf("a")).toMatchObject({ status: "blocked", code: "requires-failed", cause: ["b"] });
		expect(registry.active().map((active) => active.id)).toEqual(["c"]);
	});

	it("marks a plugin without a valid export plugin as definition-invalid and blocks dependents transitively", async () => {
		const catalogue = {
			a: plugin("a", "b"),
			b: plugin("b", "c"),
			c: { manifest: { requires: [] }, load: async () => ({ plugin: { i18n: { de: {} } } }) },
		};
		const { statusOf } = await setup(enabled("a", "b", "c"), catalogue);

		expect(statusOf("c")).toMatchObject({ status: "failed", code: "definition-invalid" });
		expect(statusOf("c")?.message).toContain("i18n.en");
		expect(statusOf("b")).toMatchObject({ status: "blocked", code: "requires-failed", cause: ["c"] });
		expect(statusOf("a")).toMatchObject({ status: "blocked", code: "requires-failed", cause: ["b", "c"] });
	});

	it("marks a plugin with an invalid reducer as definition-invalid and blocks its dependents", async () => {
		const catalogue = {
			a: plugin("a", "b"),
			b: { manifest: { requires: [] }, load: async () => ({ plugin: { i18n: texts("b"), reducer: "no function" } }) },
		};
		const { registry, statusOf } = await setup(enabled("a", "b"), catalogue);

		expect(statusOf("b")).toMatchObject({ status: "failed", code: "definition-invalid" });
		expect(statusOf("b")?.message).toContain("reducer");
		expect(statusOf("a")).toMatchObject({ status: "blocked", code: "requires-failed", cause: ["b"] });
		expect(registry.active()).toEqual([]);
	});

	it("marks a plugin whose api has the wrong key as definition-invalid, names the expected key, and blocks its dependents", async () => {
		const wrong = createPluginApi("other", () => ({}));
		const catalogue = {
			a: plugin("a", "b"),
			b: { manifest: { requires: [] }, load: async () => ({ plugin: { i18n: texts("b"), api: wrong } }) },
			c: { manifest: { requires: [] }, load: async () => ({ plugin: { i18n: texts("c"), api: createPluginApi("c", () => ({})) } }) },
		};
		const { registry, statusOf, entriesFor } = await setup(enabled("a", "b", "c"), catalogue);

		expect(statusOf("b")).toMatchObject({ status: "failed", code: "definition-invalid" });
		expect(statusOf("b")?.message).toContain("`api.reducerPath` is 'other.api', expected 'b.api'");
		expect(statusOf("a")).toMatchObject({ status: "blocked", code: "requires-failed", cause: ["b"] });
		expect(statusOf("c")).toEqual({ id: "c", status: "active" });
		expect(registry.active().map((active) => active.id)).toEqual(["c"]);
		expect(entriesFor("b")).toMatchObject([{ level: "error", action: "activate-plugin" }]);
	});

	it("does not register the texts of a plugin that is blocked after loading", async () => {
		const catalogue = { a: plugin("a", "b"), b: { manifest: { requires: [] }, load: async () => ({}) } };
		const { i18n } = await setup(enabled("a", "b"), catalogue);

		expect(i18n.hasResourceBundle("en", "a")).toBe(false);
	});
});

describe("createPluginRegistry: i18n", () => {
	it("registers the texts of an active plugin in the namespace of its id", async () => {
		const { i18n } = await setup(enabled("a"), { a: plugin("a") });

		expect(i18n.t("title", { ns: "a" })).toBe("a en");
		expect(i18n.t("title", { ns: "a", lng: "fr" })).toBe("a fr");
	});
});

describe("createPluginRegistry: log entries", () => {
	it("logs failed plugins as error with code and cause", async () => {
		const { entriesFor } = await setup({ plugins: {} }, { broken: plugin("broken", "ghost") });

		expect(entriesFor("broken")).toEqual([
			expect.objectContaining({ level: "error", data: expect.objectContaining({ code: "requires-unknown" }) }),
		]);
	});

	it("keeps the log entry of every reported plugin in its status, so that support finds it", async () => {
		const { statusOf, entriesFor } = await setup(enabled("a", "broken"), {
			a: plugin("a", "broken"),
			broken: plugin("broken", "ghost"),
			ok: plugin("ok"),
		});

		expect(statusOf("broken")?.logEntry).toBe(entriesFor("broken")[0]);
		expect(statusOf("a")?.logEntry).toBe(entriesFor("a")[0]);
		expect(statusOf("ok")?.logEntry).toBeUndefined();
	});

	it("logs plugins blocked by a failure as warn", async () => {
		const { entriesFor } = await setup(enabled("a", "broken"), { a: plugin("a", "broken"), broken: plugin("broken", "ghost") });

		expect(entriesFor("a")).toEqual([
			expect.objectContaining({ level: "warn", data: expect.objectContaining({ code: "requires-failed", cause: ["broken"] }) }),
		]);
	});

	it("logs active, disabled and plugins blocked by a switched-off plugin only as debug", async () => {
		const { sink } = await setup(enabled("a", "b"), { a: plugin("a"), b: plugin("b", "off"), off: plugin("off") });

		expect(sink.entries.map((entry) => entry.level)).toEqual(["debug", "debug", "debug"]);
	});
});

describe("createPluginRegistry: result", () => {
	it("cannot be changed by the caller", async () => {
		const { registry } = await setup(enabled("a"), { a: plugin("a") });

		expect(() => (registry.active() as unknown[]).push({})).toThrow(TypeError);
		expect(() => (registry.statuses() as unknown[]).pop()).toThrow(TypeError);
	});
});

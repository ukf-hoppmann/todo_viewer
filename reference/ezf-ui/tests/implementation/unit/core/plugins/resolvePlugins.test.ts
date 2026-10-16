import { describe, expect, it } from "vitest";
import { ConfigError } from "../../../../../src/core/config/ConfigError";
import type { PluginSelection } from "../../../../../src/core/config/types";
import { resolvePlugins } from "../../../../../src/core/plugins/resolvePlugins";
import type { PluginCatalogue } from "../../../../../src/core/plugins/types";

const load = async () => ({});

/** Catalogue entry with a valid manifest and a loader. */
function plugin(...requires: string[]) {
	return { manifest: { requires }, load };
}

function enabled(...ids: string[]): PluginSelection {
	return { plugins: Object.fromEntries(ids.map((id) => [id, { enabled: true }])) };
}

function statusOf(catalogue: PluginCatalogue, config: PluginSelection, id: string) {
	return resolvePlugins(config, catalogue).statuses.get(id);
}

describe("resolvePlugins: config", () => {
	it("throws config-unknown-plugin for every config id without a plugin", () => {
		let error: unknown;
		try {
			resolvePlugins(enabled("a", "ghost", "spook"), { a: plugin() });
		} catch (caught) {
			error = caught;
		}

		expect(error).toBeInstanceOf(ConfigError);
		expect((error as ConfigError).code).toBe("config-unknown-plugin");
		expect((error as ConfigError).details.map((detail) => detail.path)).toEqual(["/plugins/ghost", "/plugins/spook"]);
	});

	it("also rejects an unknown id that is switched off", () => {
		expect(() => resolvePlugins({ plugins: { ghost: { enabled: false } } }, {})).toThrow(ConfigError);
	});

	it("treats a plugin missing from the config as disabled", () => {
		expect(statusOf({ a: plugin() }, { plugins: {} }, "a")).toEqual({ id: "a", status: "disabled" });
		expect(statusOf({ a: plugin() }, { plugins: { a: { enabled: false } } }, "a")).toEqual({ id: "a", status: "disabled" });
	});
});

describe("resolvePlugins: broken plugins", () => {
	it.each([
		["id-invalid", { Bad_Name: plugin() }, "Bad_Name"],
		["id-invalid", { core: plugin() }, "core"],
		["id-invalid", { dev: plugin() }, "dev"],
		["manifest-invalid", { a: { manifest: { requires: "b" }, load } }, "a"],
		["manifest-invalid", { a: { manifest: undefined, load } }, "a"],
		["definition-missing", { a: { manifest: { requires: [] } } }, "a"],
		["requires-unknown", { a: plugin("ghost") }, "a"],
	])("marks %s as failed", (code, catalogue, id) => {
		const status = statusOf(catalogue, { plugins: {} }, id);

		expect(status).toMatchObject({ id, status: "failed", code });
		expect(status?.message).toEqual(expect.any(String));
	});

	it("marks a broken plugin as failed even when it is switched off", () => {
		expect(statusOf({ a: plugin("ghost") }, { plugins: { a: { enabled: false } } }, "a")?.status).toBe("failed");
	});

	it("marks only the plugins in a cycle as requires-cycle", () => {
		const catalogue = { a: plugin("b"), b: plugin("c"), c: plugin("a"), d: plugin("a"), self: plugin("self") };
		const { statuses } = resolvePlugins(enabled("a", "b", "c", "d", "self"), catalogue);

		for (const id of ["a", "b", "c", "self"]) expect(statuses.get(id)).toMatchObject({ status: "failed", code: "requires-cycle" });
		expect(statuses.get("d")).toMatchObject({ status: "blocked", code: "requires-failed", cause: ["a"] });
	});
});

describe("resolvePlugins: blocked plugins", () => {
	it("blocks a plugin whose required plugin failed, with the chain to the cause", () => {
		const catalogue = { a: plugin("b"), b: plugin("c"), c: { manifest: undefined, load } };
		const { statuses } = resolvePlugins(enabled("a", "b", "c"), catalogue);

		expect(statuses.get("b")).toMatchObject({ status: "blocked", code: "requires-failed", cause: ["c"] });
		expect(statuses.get("a")).toMatchObject({ status: "blocked", code: "requires-failed", cause: ["b", "c"] });
	});

	it("blocks a plugin whose required plugin is switched off, directly or indirectly", () => {
		const catalogue = { a: plugin("b"), b: plugin("c"), c: plugin() };
		const { statuses } = resolvePlugins(enabled("a", "b"), catalogue);

		expect(statuses.get("c")).toEqual({ id: "c", status: "disabled" });
		expect(statuses.get("b")).toMatchObject({ status: "blocked", code: "requires-disabled", cause: ["c"] });
		expect(statuses.get("a")).toMatchObject({ status: "blocked", code: "requires-disabled", cause: ["b", "c"] });
	});

	it("prefers requires-failed over requires-disabled", () => {
		const catalogue = { a: plugin("off", "broken"), off: plugin(), broken: plugin("ghost") };

		expect(statusOf(catalogue, enabled("a", "broken"), "a")).toMatchObject({
			status: "blocked",
			code: "requires-failed",
			cause: ["broken"],
		});
	});

	it("does not block a plugin that is switched off itself", () => {
		expect(statusOf({ a: plugin("b"), b: plugin("ghost") }, { plugins: {} }, "a")).toEqual({ id: "a", status: "disabled" });
	});
});

describe("resolvePlugins: candidates", () => {
	it("returns the plugins to load in topological order of requires, without status", () => {
		const catalogue = { a: plugin("b", "c"), b: plugin("c"), c: plugin(), d: plugin() };
		const { statuses, candidates } = resolvePlugins(enabled("a", "b", "c", "d"), catalogue);

		const order = candidates.map((candidate) => candidate.id);
		expect(order).toHaveLength(4);
		expect(order.indexOf("c")).toBeLessThan(order.indexOf("b"));
		expect(order.indexOf("b")).toBeLessThan(order.indexOf("a"));
		expect(candidates.find((candidate) => candidate.id === "a")).toEqual({ id: "a", requires: ["b", "c"], load });
		expect(statuses.size).toBe(0);
	});

	it("keeps plugins that do not depend on a broken one", () => {
		const { candidates } = resolvePlugins(enabled("a", "broken"), { a: plugin(), broken: plugin("ghost") });

		expect(candidates.map((candidate) => candidate.id)).toEqual(["a"]);
	});
});

import { describe, expect, it } from "vitest";
import { collectMainEntries } from "../../../../../../client/src/core/navigation/order";
import { resolveView } from "../../../../../../client/src/core/navigation/resolveView";
import type { ActivePlugin, Contribution, PluginStatus } from "../../../../../../client/src/core/plugins/types";

const icon = () => null;
const page = async () => ({ default: () => null });
const i18n = { de: {}, en: {}, fr: {} };

function tab(name: string): Contribution {
	return { slot: "core.main", name, title: `t.${name}`, icon, page };
}

const active: ActivePlugin[] = [{ id: "example", definition: { i18n, contributions: [tab("overview")] } }];
const entries = collectMainEntries(active, [tab("patients")]);

function statuses(...others: PluginStatus[]): PluginStatus[] {
	return [{ id: "example", status: "active" }, ...others];
}

describe("resolveView: available views", () => {
	it("finds the main route of an active plugin", () => {
		const result = resolveView("/example/overview", { statuses: statuses(), entries });

		expect(result).toMatchObject({ kind: "available", entry: { ownerId: "example", name: "overview" } });
	});

	it("finds a view of the core without a status entry", () => {
		const result = resolveView("/core/patients", { statuses: statuses(), entries });

		expect(result).toMatchObject({ kind: "available", entry: { ownerId: "core", name: "patients" } });
	});

	it("ignores a trailing slash", () => {
		expect(resolveView("/example/overview/", { statuses: statuses(), entries }).kind).toBe("available");
	});
});

describe("resolveView: no such page", () => {
	it.each([
		["no owner with this id", "/ghost/overview"],
		["the owner has no view of this name", "/example/missing"],
		["the core has no view of this name", "/core/missing"],
		["the path has one part only", "/example"],
		["the path has more parts than a view of this task has", "/example/overview/more"],
	])("says the page does not exist when %s, and logs it", (_name, path) => {
		expect(resolveView(path, { statuses: statuses(), entries })).toEqual({ kind: "not-found", log: true });
	});
});

describe("resolveView: not available", () => {
	it("says not available for a plugin that is switched off, and logs it", () => {
		const result = resolveView("/off/anything", { statuses: statuses({ id: "off", status: "disabled" }), entries });

		expect(result).toEqual({ kind: "unavailable", log: true });
	});

	it.each([
		["failed", { id: "bad", status: "failed", code: "import-failed" }],
		["blocked", { id: "bad", status: "blocked", code: "requires-failed" }],
	] satisfies [string, PluginStatus][])("says not available for a %s plugin without logging again", (_name, status) => {
		const result = resolveView("/bad/anything", { statuses: statuses(status), entries });

		expect(result).toEqual({ kind: "unavailable", log: false });
	});
});

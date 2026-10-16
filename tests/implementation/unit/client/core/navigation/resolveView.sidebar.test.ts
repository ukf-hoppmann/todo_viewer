import { describe, expect, it } from "vitest";
import { collectMainEntries, collectSidebarEntries } from "../../../../../../client/src/core/navigation/order";
import { resolveView } from "../../../../../../client/src/core/navigation/resolveView";
import type { ActivePlugin, Contribution, PluginStatus } from "../../../../../../client/src/core/plugins/types";

const icon = () => null;
const page = async () => ({ default: () => null });
const i18n = { de: {}, en: {}, fr: {} };

const hub: Contribution = { slot: "core.main", name: "hub", title: "t.hub", icon, layout: { sidebar: true } };
const plain: Contribution = { slot: "core.main", name: "plain", title: "t.plain", icon, page };

function entry(slot: string, name: string): Contribution {
	return { slot, name, title: `t.${name}`, icon, page };
}

const active: ActivePlugin[] = [
	{ id: "example", definition: { i18n, contributions: [hub, plain, entry("example.hub", "start")] } },
	{ id: "addon", definition: { i18n, contributions: [entry("example.hub", "panel")] } },
];
const core = [{ ...hub, name: "patients" }, entry("core.patients", "list")];
const entries = collectMainEntries(active, core);
const sidebars = collectSidebarEntries(active, core);

function statuses(...others: PluginStatus[]): PluginStatus[] {
	return [{ id: "example", status: "active" }, { id: "addon", status: "active" }, ...others];
}

const input = (...others: PluginStatus[]) => ({ statuses: statuses(...others), entries, sidebars });

describe("resolveView: sidebars", () => {
	it("finds a main route with a sidebar without an entry", () => {
		expect(resolveView("/example/hub", input())).toMatchObject({ kind: "available", entry: { ownerId: "example", name: "hub" } });
	});

	it.each([
		["an entry of the host itself", "/example/hub/example/start", "example", "start"],
		["an entry of another plugin", "/example/hub/addon/panel", "addon", "panel"],
		["an entry of a sidebar of the core", "/core/patients/core/list", "core", "list"],
	])("finds %s", (_name, path, ownerId, name) => {
		const result = resolveView(path, input());

		expect(result).toMatchObject({ kind: "available", sidebarEntry: { ownerId, name } });
	});

	it("says the page does not exist when the main route has no sidebar", () => {
		expect(resolveView("/example/plain/addon/panel", input())).toEqual({ kind: "not-found", log: true });
	});

	it("says the whole page is not available when the host plugin is switched off", () => {
		const result = resolveView("/off/hub/addon/panel", input({ id: "off", status: "disabled" }));

		expect(result).toEqual({ kind: "unavailable", log: true });
	});
});

describe("resolveView: entries that cannot be shown", () => {
	it.each([
		["the entry does not exist", "/example/hub/addon/missing"],
		["the owner of the entry does not exist", "/example/hub/ghost/panel"],
		["the path names only the owner of an entry", "/example/hub/addon"],
		["the path has more parts than an entry", "/example/hub/addon/panel/more"],
	])("says the entry does not exist, naming the host, when %s", (_name, path) => {
		const result = resolveView(path, input());

		expect(result).toMatchObject({ kind: "not-found", log: true, host: { ownerId: "example", name: "hub" } });
	});

	it("says the entry is not available when its plugin is switched off, and logs it", () => {
		const result = resolveView("/example/hub/off/panel", input({ id: "off", status: "disabled" }));

		expect(result).toMatchObject({ kind: "unavailable", log: true, host: { name: "hub" } });
	});

	it.each([
		["failed", { id: "bad", status: "failed", code: "import-failed" }],
		["blocked", { id: "bad", status: "blocked", code: "requires-failed" }],
	] satisfies [string, PluginStatus][])("says the entry is not available without logging again when its plugin is %s", (_name, status) => {
		const result = resolveView("/example/hub/bad/panel", input(status));

		expect(result).toMatchObject({ kind: "unavailable", log: false, host: { name: "hub" } });
	});
});

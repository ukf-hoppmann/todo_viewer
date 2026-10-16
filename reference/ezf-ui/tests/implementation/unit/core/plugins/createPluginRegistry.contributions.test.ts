import { describe, expect, it } from "vitest";
import type { PluginSelection } from "../../../../../src/core/config/types";
import { initI18n } from "../../../../../src/core/i18n/initI18n";
import { createLogging } from "../../../../../src/core/logging/createLogging";
import { MemorySink } from "../../../../../src/core/logging/MemorySink";
import { createPluginRegistry } from "../../../../../src/core/plugins/createPluginRegistry";
import type { Contribution, PluginCatalogue } from "../../../../../src/core/plugins/types";

const i18n = { de: {}, en: {}, fr: {} };
const icon = () => null;
const page = async () => ({ default: () => null });

/** A main route with a sidebar, opening the slot `<owner>.<name>`. */
const hub: Contribution = { slot: "core.main", name: "hub", title: "t.hub", icon, layout: { sidebar: true } };
/** A main route with a page and no sidebar. */
const plain: Contribution = { slot: "core.main", name: "plain", title: "t.plain", icon, page };

function entry(slot: string, name = "panel"): Contribution {
	return { slot, name, title: `t.${name}`, icon, page };
}

/** Catalogue entry whose definition has these contributions. */
function plugin(requires: string[], ...contributions: Contribution[]) {
	return { manifest: { requires }, load: async () => ({ plugin: { i18n, contributions } }) };
}

function enabled(...ids: string[]): PluginSelection {
	return { plugins: Object.fromEntries(ids.map((id) => [id, { enabled: true }])) };
}

async function setup(config: PluginSelection, catalogue: PluginCatalogue, coreContributions?: readonly Contribution[]) {
	const logging = createLogging();
	const sink = new MemorySink();
	logging.addSink(sink, { level: "debug" });
	const registry = await createPluginRegistry({
		config,
		catalogue,
		i18n: await initI18n({ lng: "en" }),
		logger: logging.forOrigin("core"),
		coreContributions,
	});
	const statusOf = (id: string) => registry.statuses().find((status) => status.id === id);
	return { registry, sink, statusOf };
}

describe("createPluginRegistry: entries of a sidebar", () => {
	it("activates a plugin that hangs an entry into the sidebar of a plugin it requires", async () => {
		const catalogue = { host: plugin([], hub), addon: plugin(["host"], entry("host.hub")) };
		const { registry, statusOf } = await setup(enabled("host", "addon"), catalogue);

		expect(statusOf("addon")).toEqual({ id: "addon", status: "active" });
		expect(registry.active().map((active) => active.id)).toEqual(["host", "addon"]);
	});

	it("activates a host that fills its own sidebar", async () => {
		const catalogue = { host: plugin([], hub, entry("host.hub", "start")) };
		const { statusOf } = await setup(enabled("host"), catalogue);

		expect(statusOf("host")).toEqual({ id: "host", status: "active" });
	});

	it("marks the whole plugin as failed when its entry is for a host it does not require", async () => {
		const catalogue = { host: plugin([], hub), addon: plugin([], entry("host.hub", "panel"), plain) };
		const { statusOf, sink } = await setup(enabled("host", "addon"), catalogue);

		expect(statusOf("addon")).toMatchObject({
			id: "addon",
			status: "failed",
			code: "contribution-invalid",
			message: expect.stringContaining("contribution 'panel': the host 'host' of the slot 'host.hub' is not required"),
		});
		expect(statusOf("host")).toEqual({ id: "host", status: "active" });
		expect(sink.entries.filter((e) => e.level === "error")).toHaveLength(1);
	});

	it.each([
		["a slot that does not exist at the host", "host.missing"],
		["a main route of the host that has a page and no sidebar", "host.plain"],
		["a host that does not exist", "ghost.hub"],
	])("marks the plugin as failed for an entry to %s", async (_name, slot) => {
		const catalogue = { host: plugin([], hub, plain), addon: plugin(["host"], entry(slot)) };
		const { statusOf } = await setup(enabled("host", "addon"), catalogue);

		expect(statusOf("addon")).toMatchObject({ status: "failed", code: "contribution-invalid" });
	});

	it("names the slot that does not exist", async () => {
		const catalogue = { host: plugin([], hub), addon: plugin(["host"], entry("host.missing")) };
		const { statusOf } = await setup(enabled("host", "addon"), catalogue);

		expect(statusOf("addon")?.message).toContain("the slot 'host.missing' does not exist");
	});

	it("blocks the plugins that need a plugin with an invalid entry", async () => {
		const catalogue = { addon: plugin([], entry("ghost.hub")), user: plugin(["addon"]) };
		const { statusOf } = await setup(enabled("addon", "user"), catalogue);

		expect(statusOf("user")).toMatchObject({ status: "blocked", code: "requires-failed", cause: ["addon"] });
	});

	it("blocks the addon without an error when its host is switched off", async () => {
		const catalogue = { host: plugin([], hub), addon: plugin(["host"], entry("host.hub")) };
		const { statusOf, sink } = await setup(enabled("addon"), catalogue);

		expect(statusOf("host")).toEqual({ id: "host", status: "disabled" });
		expect(statusOf("addon")).toMatchObject({ status: "blocked", code: "requires-disabled" });
		expect(sink.entries.filter((e) => e.level === "error" || e.level === "warn")).toEqual([]);
	});
});

describe("createPluginRegistry: entries of a sidebar of the core", () => {
	const patients: Contribution = { slot: "core.main", name: "patients", title: "t.patients", icon, layout: { sidebar: true } };

	it("needs no requires for an entry of a sidebar that the core has", async () => {
		const catalogue = { addon: plugin([], entry("core.patients")) };
		const { statusOf } = await setup(enabled("addon"), catalogue, [patients]);

		expect(statusOf("addon")).toEqual({ id: "addon", status: "active" });
	});

	it("marks the plugin as failed when the core has no such sidebar", async () => {
		const catalogue = { addon: plugin([], entry("core.patients")) };

		expect((await setup(enabled("addon"), catalogue)).statusOf("addon")).toMatchObject({ status: "failed", code: "contribution-invalid" });
		expect((await setup(enabled("addon"), catalogue, [])).statusOf("addon")).toMatchObject({ code: "contribution-invalid" });
	});
});

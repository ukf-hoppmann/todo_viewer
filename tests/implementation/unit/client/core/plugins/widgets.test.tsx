import { describe, expect, it, vi } from "vitest";
import { initI18n } from "../../../../../../client/src/core/i18n/initI18n";
import { createLogging } from "../../../../../../client/src/core/logging/createLogging";
import { checkContributions } from "../../../../../../client/src/core/plugins/checkContributions";
import { checkDefinition } from "../../../../../../client/src/core/plugins/checkDefinition";
import { checkSlots, type RegisteredPlugin } from "../../../../../../client/src/core/plugins/checkSlots";
import { createPluginRegistry } from "../../../../../../client/src/core/plugins/createPluginRegistry";
import { definePlugin } from "../../../../../../client/src/core/plugins/definePlugin";
import { selectSlotEntries } from "../../../../../../client/src/core/plugins/useSlot";
import type { ActivePlugin, Contribution, PluginCatalogue } from "../../../../../../client/src/core/plugins/types";

const Component = () => null;
const widget = (slot: string, name: string, extra: Record<string, unknown> = {}) => ({ slot, name, component: Component, ...extra });
const i18n = { de: {}, en: {} };

describe("checkContributions: widgets", () => {
	it("accepts a widget with order and main routes", () => {
		expect(checkContributions([widget("layout.header", "counter", { order: 2, when: ["backlog/main", "notes/main"] })])).toEqual([]);
	});

	it("reports a slot that is not <owner>.<name>, a bad name, a missing component", () => {
		expect(checkContributions([widget("nope", "x")])).toEqual(["contribution 'x': the slot 'nope' is not of the form <owner id>.<name>"]);
		expect(checkContributions([widget("a.b", "Bad_Name")])).toEqual(["contribution 'Bad_Name': `name` is not kebab-case"]);
		expect(checkContributions([{ slot: "a.b", name: "x", component: "text" }])).toEqual(["contribution 'x': `component` is no component"]);
	});

	it("accepts a group in the settings slot and reports a bad group or one in another slot", () => {
		expect(checkContributions([widget("core.settings-sections", "x", { group: "projects" })])).toEqual([]);
		expect(checkContributions([widget("core.settings-sections", "x", { group: "Bad_Group" })])).toEqual(["contribution 'x': `group` is not kebab-case"]);
		expect(checkContributions([widget("layout.header", "x", { group: "projects" })])).toEqual([
			"contribution 'x': `group` is only allowed in 'core.settings-sections'",
		]);
	});

	it("reports a bad order and a bad when", () => {
		expect(checkContributions([widget("a.b", "x", { order: "first" })])).toEqual(["contribution 'x': `order` is no number"]);
		expect(checkContributions([widget("a.b", "x", { when: "backlog/main" })])).toEqual([
			"contribution 'x': `when` is no list of main routes (`<owner id>/<name>`)",
		]);
		expect(checkContributions([widget("a.b", "x", { when: ["backlog"] })])).toHaveLength(1);
	});

	it("does not allow the fields of a tab in a widget, nor the main slot", () => {
		expect(checkContributions([widget("a.b", "x", { title: "t", page: () => null })])).toEqual([
			"contribution 'x': `title` is not allowed in a widget",
			"contribution 'x': `page` is not allowed in a widget",
		]);
		expect(checkContributions([widget("core.main", "x")])).toEqual(["contribution 'x': a widget cannot hang into 'core.main'"]);
	});

	it("reports the same name twice in one slot", () => {
		expect(checkContributions([widget("a.b", "x"), widget("a.b", "x")])).toEqual(["contribution 'x': the name is used twice in 'a.b'"]);
		expect(checkContributions([widget("a.b", "x"), widget("a.c", "x")])).toEqual([]);
	});
});

describe("checkSlots: widgets", () => {
	const registered = new Map<string, RegisteredPlugin>([["layout", { contributions: [], slots: ["header-actions"] }]]);
	const check = (contributions: Contribution[], requires: string[] = ["layout"], slots: string[] = []) =>
		checkSlots({ id: "me", requires, contributions, slots, registered });

	it("accepts a widget in a slot of a required plugin", () => {
		expect(check([widget("layout.header-actions", "x")])).toEqual([]);
	});

	it("reports a slot the host does not provide", () => {
		expect(check([widget("layout.footer", "x")])).toEqual(["contribution 'x': the slot 'layout.footer' does not exist ('layout' provides no slot 'footer')"]);
	});

	it("reports a host that is not required", () => {
		expect(check([widget("layout.header-actions", "x")], [])).toEqual(["contribution 'x': the host 'layout' of the slot 'layout.header-actions' is not required"]);
	});

	it("accepts a widget in an own slot and in the slot of the core", () => {
		expect(check([widget("me.panel", "x"), widget("core.settings-sections", "y"), widget("core.sidebar-sections", "z")], [], ["panel"])).toEqual([]);
		expect(check([widget("me.panel", "x")], [], [])).toHaveLength(1);
		expect(check([widget("core.nothing", "y")])).toHaveLength(1);
	});
});

describe("checkDefinition: slots, event handlers, frame", () => {
	const check = (extra: Record<string, unknown>) => checkDefinition({ plugin: { i18n, ...extra } }, "demo");

	it("accepts all three", () => {
		expect(check({ slots: { panel: { description: "x" } }, eventHandlers: { "core.reconnected": () => {} }, frame: Component }).ok).toBe(true);
	});

	it.each([
		["slots is no object", { slots: [] }, "`slots` is no object"],
		["slot name not kebab-case", { slots: { Bad: { description: "x" } } }, "slot 'Bad': the name is not kebab-case"],
		["slot without description", { slots: { ok: {} } }, "slot 'ok': `description` is missing"],
		["handlers no object", { eventHandlers: 1 }, "`eventHandlers` is no object"],
		["handler topic malformed", { eventHandlers: { nope: () => {} } }, "event handler 'nope': the topic is not of the form <owner>.<name>"],
		["handler no function", { eventHandlers: { "a.b": 1 } }, "event handler 'a.b': the handler is no function"],
		["frame no component", { frame: "x" }, "`frame` is no component"],
	])("rejects: %s", (_name, extra, message) => {
		const result = check(extra);
		expect(result.ok).toBe(false);
		expect(!result.ok && result.message).toContain(message);
	});
});

describe("selectSlotEntries", () => {
	it("hands the group of a widget on to its entry", () => {
		const active: ActivePlugin[] = [
			{ id: "a", definition: definePlugin({ i18n, contributions: [widget("core.settings-sections", "one", { group: "projects" }), widget("core.settings-sections", "two")] as Contribution[] }) },
		];

		expect(selectSlotEntries(active, "core.settings-sections").map((entry) => [entry.name, entry.group])).toEqual([
			["one", "projects"],
			["two", undefined],
		]);
	});

	const plugin = (id: string, contributions: Contribution[]): ActivePlugin => ({ id, definition: definePlugin({ i18n, contributions }) });
	const A = () => null;
	const B = () => null;
	const C = () => null;

	it("collects the widgets of a slot, ordered by order, plugin id and definition", () => {
		const active = [
			plugin("zeta", [widget("host.slot", "late", { component: C })]),
			plugin("alpha", [widget("host.slot", "second", { component: B }), widget("host.slot", "first", { component: A, order: -1 }), widget("host.other", "x")]),
		];

		const entries = selectSlotEntries(active, "host.slot");

		expect(entries.map(({ ownerId, name }) => `${ownerId}/${name}`)).toEqual(["alpha/first", "alpha/second", "zeta/late"]);
		expect(entries[0]!.component).toBe(A);
	});

	it("shows a widget with `when` only on those main routes", () => {
		const active = [plugin("p", [widget("host.slot", "everywhere"), widget("host.slot", "backlog-only", { when: ["backlog/main"] })])];

		expect(selectSlotEntries(active, "host.slot", "backlog/main").map((entry) => entry.name)).toEqual(["everywhere", "backlog-only"]);
		expect(selectSlotEntries(active, "host.slot", "notes/main").map((entry) => entry.name)).toEqual(["everywhere"]);
		expect(selectSlotEntries(active, "host.slot", undefined).map((entry) => entry.name)).toEqual(["everywhere"]);
	});

	it("returns nothing for a slot without widgets, and ignores tabs", () => {
		expect(selectSlotEntries([plugin("p", [{ slot: "core.main", name: "t", title: "t", icon: A, page: async () => ({ default: A }) }])], "core.main")).toEqual([]);
	});
});

describe("createPluginRegistry: slots and the frame", () => {
	async function start(catalogue: PluginCatalogue, ids: string[]) {
		const instance = await initI18n({ lng: "en" });
		const logging = createLogging();
		return createPluginRegistry({
			config: { plugins: Object.fromEntries(ids.map((id) => [id, { enabled: true }])) },
			catalogue,
			i18n: instance,
			logger: logging.forOrigin("core"),
		});
	}
	const entry = (definition: ReturnType<typeof definePlugin>, ...requires: string[]) => ({ manifest: { requires }, load: vi.fn(async () => ({ plugin: definition })) });

	it("activates a plugin whose widget hangs into the slot of a required plugin", async () => {
		const catalogue = {
			layout: entry(definePlugin({ i18n, slots: { actions: { description: "x" } } })),
			user: entry(definePlugin({ i18n, contributions: [widget("layout.actions", "w")] }), "layout"),
		};

		const registry = await start(catalogue, ["layout", "user"]);

		expect(registry.statuses().map((s) => [s.id, s.status])).toEqual([["layout", "active"], ["user", "active"]]);
	});

	it("fails a plugin whose widget hangs into a slot that does not exist", async () => {
		const catalogue = {
			layout: entry(definePlugin({ i18n })),
			user: entry(definePlugin({ i18n, contributions: [widget("layout.actions", "w")] }), "layout"),
		};

		const registry = await start(catalogue, ["layout", "user"]);

		expect(registry.statuses().find((s) => s.id === "user")).toMatchObject({ status: "failed", code: "contribution-invalid" });
	});

	it("lets only one active plugin provide the frame", async () => {
		const catalogue = {
			a: entry(definePlugin({ i18n, frame: Component })),
			b: entry(definePlugin({ i18n, frame: Component })),
		};

		const registry = await start(catalogue, ["a", "b"]);

		expect(registry.statuses().find((s) => s.id === "a")?.status).toBe("active");
		expect(registry.statuses().find((s) => s.id === "b")).toMatchObject({ status: "failed", code: "definition-invalid" });
		expect(registry.statuses().find((s) => s.id === "b")?.message).toContain("already provided by 'a'");
	});
});

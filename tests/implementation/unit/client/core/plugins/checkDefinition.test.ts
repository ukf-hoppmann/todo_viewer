import { describe, expect, it } from "vitest";
import { createPluginApi } from "../../../../../../client/src/core/api/createPluginApi";
import { checkDefinition } from "../../../../../../client/src/core/plugins/checkDefinition";
import { definePlugin } from "../../../../../../client/src/core/plugins/definePlugin";

const i18n = { de: { title: "Beispiel" }, en: { title: "Example" } };

describe("definePlugin", () => {
	it("returns the definition unchanged", () => {
		const definition = { i18n };

		expect(definePlugin(definition)).toBe(definition);
	});
});

describe("checkDefinition: valid modules", () => {
	it("accepts a module with the export plugin and texts for every language", () => {
		const plugin = definePlugin({ i18n });

		expect(checkDefinition({ plugin, other: 1 }, "example")).toEqual({ ok: true, definition: plugin });
	});
});

describe("checkDefinition: invalid modules", () => {
	it.each([
		["no module object", undefined, "the module is no object"],
		["no export plugin", { default: { i18n } }, "the export `plugin` is missing"],
		["plugin is no object", { plugin: "x" }, "the export `plugin` is no object"],
		["i18n missing", { plugin: {} }, "`i18n` is missing"],
		["language missing", { plugin: { i18n: { de: {} } } }, "`i18n.en` is missing"],
		["language is no object", { plugin: { i18n: { ...i18n, en: "x" } } }, "`i18n.en` is no object"],
		["language is a list", { plugin: { i18n: { ...i18n, de: [] } } }, "`i18n.de` is no object"],
	])("rejects %s", (_name, module, expected) => {
		const result = checkDefinition(module, "example");

		expect(result.ok).toBe(false);
		if (!result.ok) expect(result.message).toContain(expected);
	});
});

const page = async () => ({ default: () => null });
const icon = () => null;

/** A valid main contribution; `extra` overrides single fields. */
function tab(extra: Record<string, unknown> = {}) {
	return { slot: "core.main", name: "overview", title: "tab.overview", icon, page, ...extra };
}

describe("checkDefinition: contributions", () => {
	it("accepts a definition without contributions", () => {
		expect(checkDefinition({ plugin: { i18n } }, "example").ok).toBe(true);
	});

	it("accepts a main route with a sidebar and no page, and entries for its slot", () => {
		const plugin = {
			i18n,
			contributions: [
				tab({ name: "hub", page: undefined, layout: { header: true, sidebar: true } }),
				tab({ slot: "example.hub", name: "start" }),
				tab({ slot: "other-host.hub", name: "panel" }),
			],
		};

		expect(checkDefinition({ plugin }, "example")).toEqual({ ok: true, definition: plugin });
	});

	it("accepts the same name in different slots", () => {
		const plugin = { i18n, contributions: [tab({ name: "start" }), tab({ slot: "example.hub", name: "start" })] };

		expect(checkDefinition({ plugin }, "example").ok).toBe(true);
	});

	it("accepts several tabs, an object as icon and the layout switch header", () => {
		const plugin = {
			i18n,
			contributions: [tab(), tab({ name: "details", icon: { $$typeof: Symbol.for("react.memo") }, layout: { header: true } })],
		};

		expect(checkDefinition({ plugin }, "example")).toEqual({ ok: true, definition: plugin });
	});

	it.each([
		["contributions is no list", { contributions: "x" }, "`contributions` is no list"],
		["an entry is no object", { contributions: ["x"] }, "contribution #0 is no object"],
		["slot is not written <owner id>.<name>", { contributions: [tab({ slot: "Other" })] }, "contribution 'overview': the slot 'Other' is not of the form <owner id>.<name>"],
		["slot has no slot name", { contributions: [tab({ slot: 7 })] }, "contribution 'overview': the slot '7' is not of the form <owner id>.<name>"],
		["name is missing", { contributions: [tab({ name: undefined })] }, "contribution #0: `name` is missing"],
		["name is no kebab-case", { contributions: [tab({ name: "Over_View" })] }, "contribution 'Over_View': `name` is not kebab-case"],
		["title is missing", { contributions: [tab({ title: "" })] }, "contribution 'overview': `title` is missing"],
		["icon is missing", { contributions: [tab({ icon: undefined })] }, "contribution 'overview': `icon` is no component"],
		["page is missing", { contributions: [tab({ page: undefined })] }, "contribution 'overview': `page` is no function"],
		["layout is no object", { contributions: [tab({ layout: true })] }, "contribution 'overview': `layout` is no object"],
		["layout switch is no boolean", { contributions: [tab({ layout: { header: "yes" } })] }, "contribution 'overview': `layout.header` is no boolean"],
		["layout has an unknown key", { contributions: [tab({ layout: { footer: true } })] }, "contribution 'overview': `layout.footer` is unknown"],
		["a main route with a sidebar has a page", { contributions: [tab({ layout: { sidebar: true } })] }, "contribution 'overview': `page` must not be set when `layout.sidebar` is true"],
		["an entry has a layout", { contributions: [tab({ slot: "example.hub", layout: { header: true } })] }, "contribution 'overview': `layout` is not allowed in an entry"],
		["an entry has no page", { contributions: [tab({ slot: "example.hub", page: undefined })] }, "contribution 'overview': `page` is no function"],
		["name is used twice", { contributions: [tab(), tab()] }, "contribution 'overview': the name is used twice in 'core.main'"],
	])("rejects a definition where %s", (_name, extra, expected) => {
		const result = checkDefinition({ plugin: { i18n, ...extra } }, "example");

		expect(result.ok).toBe(false);
		if (!result.ok) expect(result.message).toContain(expected);
	});

	it("names every problem it finds", () => {
		const result = checkDefinition({ plugin: { i18n, contributions: [tab({ title: "" }), tab({ name: "details", page: 1 })] } }, "example");

		expect(result.ok).toBe(false);
		if (!result.ok) expect(result.message).toMatch(/`title` is missing.*`page` is no function/);
	});
});

describe("checkDefinition: reducer", () => {
	const reducer = (state: number = 0) => state;

	it("accepts a definition without a reducer", () => {
		expect(checkDefinition({ plugin: { i18n } }, "example").ok).toBe(true);
	});

	it("accepts a reducer that is a function", () => {
		const plugin = definePlugin({ i18n, reducer });

		expect(checkDefinition({ plugin }, "example")).toEqual({ ok: true, definition: plugin });
	});

	it.each([
		["an object", {}],
		["a string", "x"],
		["null", null],
	])("rejects a reducer that is %s and names the field", (_name, value) => {
		const result = checkDefinition({ plugin: { i18n, reducer: value } }, "example");

		expect(result.ok).toBe(false);
		if (!result.ok) expect(result.message).toContain("`reducer` is no function");
	});
});

describe("checkDefinition: api", () => {
	/** The parts of an API that the core needs; a real one is built with `createPluginApi`. */
	function api(extra: Record<string, unknown> = {}) {
		return { reducerPath: "example.api", reducer: (state = {}) => state, middleware: () => (next: (action: unknown) => unknown) => next, ...extra };
	}

	it("accepts a definition without an api", () => {
		expect(checkDefinition({ plugin: { i18n } }, "example").ok).toBe(true);
	});

	it("accepts an api whose key is <plugin id>.api", () => {
		const plugin = { i18n, api: api() };

		expect(checkDefinition({ plugin }, "example")).toEqual({ ok: true, definition: plugin });
	});

	it("accepts an api built with createPluginApi", () => {
		const plugin = { i18n, api: createPluginApi("example", () => ({})) };

		expect(checkDefinition({ plugin }, "example").ok).toBe(true);
	});

	it.each([
		["a string", "x"],
		["null", null],
		["a list", []],
	])("rejects an api that is %s", (_name, value) => {
		const result = checkDefinition({ plugin: { i18n, api: value } }, "example");

		expect(result.ok).toBe(false);
		if (!result.ok) expect(result.message).toContain("`api` is no object");
	});

	it.each([
		["reducerPath is missing", { reducerPath: undefined }, "`api.reducerPath` is no string"],
		["reducerPath is no string", { reducerPath: 7 }, "`api.reducerPath` is no string"],
		["reducer is missing", { reducer: undefined }, "`api.reducer` is no function"],
		["middleware is no function", { middleware: {} }, "`api.middleware` is no function"],
	])("rejects an api where %s", (_name, extra, expected) => {
		const result = checkDefinition({ plugin: { i18n, api: api(extra) } }, "example");

		expect(result.ok).toBe(false);
		if (!result.ok) expect(result.message).toContain(expected);
	});

	it.each([
		["without the plugin id", "api", "`api.reducerPath` is 'api', expected 'example.api'"],
		["of another plugin", "other.api", "`api.reducerPath` is 'other.api', expected 'example.api'"],
		["of the core", "core.api", "`api.reducerPath` is 'core.api', expected 'example.api'"],
	])("rejects a key %s and names the expected one", (_name, reducerPath, expected) => {
		const result = checkDefinition({ plugin: { i18n, api: api({ reducerPath }) } }, "example");

		expect(result.ok).toBe(false);
		if (!result.ok) expect(result.message).toContain(expected);
	});

	it("expects the key of the plugin that is checked", () => {
		expect(checkDefinition({ plugin: { i18n, api: api() } }, "example").ok).toBe(true);
		expect(checkDefinition({ plugin: { i18n, api: api() } }, "other").ok).toBe(false);
	});
});

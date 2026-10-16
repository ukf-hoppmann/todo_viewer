import { describe, expect, it } from "vitest";
import { ConfigError } from "../../../../../src/core/config/ConfigError";
import { validatePluginSelection } from "../../../../../src/core/config/validatePluginSelection";

function failure(raw: unknown): ConfigError {
	try {
		validatePluginSelection(raw);
	} catch (error) {
		if (error instanceof ConfigError) return error;
		throw error;
	}
	throw new Error("validatePluginSelection did not throw");
}

describe("validatePluginSelection: section navigation", () => {
	it("accepts a start view and order lists for slots", () => {
		const config = {
			plugins: {},
			navigation: {
				start: "example/overview",
				"core.main": ["example/overview", "core/patients"],
				"example.hub": ["example-addon/panel", "example/start"],
			},
		};

		expect(validatePluginSelection(config)).toEqual(config);
	});

	it("accepts a sidebar entry as start view", () => {
		const config = { plugins: {}, navigation: { start: "example/hub/example-addon/panel" } };

		expect(validatePluginSelection(config)).toEqual(config);
	});

	it("accepts an empty section", () => {
		expect(validatePluginSelection({ plugins: {}, navigation: {} })).toEqual({ plugins: {}, navigation: {} });
	});

	it.each([
		["navigation is no object", { navigation: [] }],
		["start is no text", { navigation: { start: 1 } }],
		["start has a leading slash", { navigation: { start: "/example/overview" } }],
		["start is not a view", { navigation: { start: "example" } }],
		["start has upper case", { navigation: { start: "Example/overview" } }],
		["a slot is no list", { navigation: { "core.main": "example/overview" } }],
		["a list entry is not a view", { navigation: { "core.main": ["example"] } }],
		["a list has a duplicate", { navigation: { "core.main": ["example/overview", "example/overview"] } }],
		["a key is neither start nor a slot", { navigation: { order: [] } }],
	])("rejects a plugin selection where %s", (_name, extra) => {
		const error = failure({ plugins: {}, ...extra });

		expect(error.code).toBe("config-invalid");
		expect(error.details.some((detail) => detail.path.startsWith("/navigation"))).toBe(true);
	});
});

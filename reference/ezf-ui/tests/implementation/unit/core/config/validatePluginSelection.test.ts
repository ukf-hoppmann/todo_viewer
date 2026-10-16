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

describe("validatePluginSelection: valid selections", () => {
	it("accepts an empty list of plugins", () => {
		expect(validatePluginSelection({ plugins: {} })).toEqual({ plugins: {} });
	});

	it("accepts plugins that are switched on or off", () => {
		const selection = { plugins: { example: { enabled: false }, "variant-filter": { enabled: true } } };

		expect(validatePluginSelection(selection)).toEqual(selection);
	});
});

describe("validatePluginSelection: invalid selections", () => {
	it.each([
		["null", null],
		["a list", []],
		["a text", "plugins"],
		["a number", 7],
	])("rejects %s instead of an object", (_name, raw) => {
		const error = failure(raw);

		expect(error.code).toBe("config-invalid");
		expect(error.details.length).toBeGreaterThan(0);
	});

	it("rejects a selection without plugins and names the missing field", () => {
		const error = failure({});

		expect(error.code).toBe("config-invalid");
		expect(error.details).toEqual([{ path: "", message: "must have required property 'plugins'" }]);
	});

	it("rejects plugins that are no object", () => {
		const error = failure({ plugins: [] });

		expect(error.details[0]).toMatchObject({ path: "/plugins", message: "must be object" });
	});

	it("rejects a plugin without enabled", () => {
		const error = failure({ plugins: { example: {} } });

		expect(error.details).toEqual([{ path: "/plugins/example", message: "must have required property 'enabled'" }]);
	});

	it("rejects enabled that is no boolean", () => {
		const error = failure({ plugins: { example: { enabled: "yes" } } });

		expect(error.details).toEqual([{ path: "/plugins/example/enabled", message: "must be boolean" }]);
	});

	it("rejects an unknown field at the top and names it", () => {
		const error = failure({ plugins: {}, extra: 1 });

		expect(error.details).toEqual([{ path: "", message: "must NOT have additional properties: extra" }]);
	});

	it.each(["api", "logging"])("rejects the section %s, which belongs to config.json", (section) => {
		const error = failure({ plugins: {}, [section]: {} });

		expect(error.details).toEqual([{ path: "", message: `must NOT have additional properties: ${section}` }]);
	});

	it("rejects settings of a plugin, which do not exist yet", () => {
		const error = failure({ plugins: { example: { enabled: true, settings: {} } } });

		expect(error.details).toEqual([
			{ path: "/plugins/example", message: "must NOT have additional properties: settings" },
		]);
	});

	it.each(["Example", "my_plugin", "-a", "a--b", "a b"])("rejects the plugin id %s that is not kebab-case", (id) => {
		const error = failure({ plugins: { [id]: { enabled: true } } });

		expect(error.code).toBe("config-invalid");
		expect(error.details[0]?.message).toContain(id);
	});

	it("collects all errors instead of stopping at the first", () => {
		const error = failure({
			plugins: { example: { enabled: "yes" }, other: {} },
			extra: true,
		});

		expect(error.details.map((detail) => detail.path).sort()).toEqual(["", "/plugins/example/enabled", "/plugins/other"]);
	});

	it("puts the code and every error into the message of the error", () => {
		const error = failure({ plugins: { example: {} }, extra: true });

		expect(error).toBeInstanceOf(Error);
		expect(error.name).toBe("ConfigError");
		expect(error.message).toContain("config-invalid");
		expect(error.message).toContain("/plugins/example: must have required property 'enabled'");
		expect(error.message).toContain("must NOT have additional properties: extra");
	});
});

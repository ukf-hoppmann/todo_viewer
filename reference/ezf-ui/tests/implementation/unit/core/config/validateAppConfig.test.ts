import { describe, expect, it } from "vitest";
import { ConfigError } from "../../../../../src/core/config/ConfigError";
import { validateAppConfig } from "../../../../../src/core/config/validateAppConfig";

const api = { url: "https://backend.et.localhost" };

function failure(raw: unknown): ConfigError {
	try {
		validateAppConfig(raw);
	} catch (error) {
		if (error instanceof ConfigError) return error;
		throw error;
	}
	throw new Error("validateAppConfig did not throw");
}

describe("validateAppConfig: valid configs", () => {
	it("accepts the section api with only the url", () => {
		expect(validateAppConfig({ api })).toEqual({ api });
	});

	it.each([
		"https://backend.et.localhost",
		"http://localhost:8081/ezfBackend",
		"https://example.org/a/b",
	])("accepts the url %s", (url) => {
		expect(validateAppConfig({ api: { url } })).toEqual({ api: { url } });
	});

	it("accepts returnToMaxAgeMinutes as a whole number from 1", () => {
		const config = { api: { ...api, returnToMaxAgeMinutes: 1 } };

		expect(validateAppConfig(config)).toEqual(config);
	});

	it("accepts a valid section logging", () => {
		const config = {
			api,
			logging: {
				outputs: { console: { level: "warn", origins: { "variant-filter": "debug" } } },
				limits: { depth: 5 },
			},
		};

		expect(validateAppConfig(config)).toEqual(config);
	});
});

describe("validateAppConfig: section api.connection", () => {
	it("accepts all three settings as whole numbers from 1", () => {
		const config = { api: { ...api, connection: { failuresBeforeWarning: 2, retryIntervalSeconds: 10, logoutAfterSeconds: 600 } } };

		expect(validateAppConfig(config)).toEqual(config);
	});

	it.each([{}, { failuresBeforeWarning: 1 }, { logoutAfterSeconds: 20 }])("accepts the optional settings %j", (connection) => {
		const config = { api: { ...api, connection } };

		expect(validateAppConfig(config)).toEqual(config);
	});

	it.each(["failuresBeforeWarning", "retryIntervalSeconds", "logoutAfterSeconds"])("rejects %s that is no whole number from 1", (field) => {
		for (const value of [0, -1, 2.5, "5"]) {
			const error = failure({ api: { ...api, connection: { [field]: value } } });

			expect(error.code).toBe("config-invalid");
			expect(error.details.length).toBeGreaterThan(0);
			expect(error.details.every((detail) => detail.path === `/api/connection/${field}`)).toBe(true);
		}
	});

	it("rejects an unknown field in connection and names it", () => {
		const error = failure({ api: { ...api, connection: { retries: 3 } } });

		expect(error.details).toEqual([{ path: "/api/connection", message: "must NOT have additional properties: retries" }]);
	});
});

describe("validateAppConfig: section banners", () => {
	it("accepts maxVisible as a whole number from 1", () => {
		const config = { api, banners: { maxVisible: 20 } };

		expect(validateAppConfig(config)).toEqual(config);
	});

	it("accepts an empty section banners, so that the default applies", () => {
		const config = { api, banners: {} };

		expect(validateAppConfig(config)).toEqual(config);
	});

	it.each([
		["0", 0],
		["a negative number", -1],
		["a decimal number", 2.5],
		["a text", "20"],
	])("rejects maxVisible that is %s, and names the field", (_name, maxVisible) => {
		const error = failure({ api, banners: { maxVisible } });

		expect(error.code).toBe("config-invalid");
		expect(error.details.every((detail) => detail.path === "/banners/maxVisible")).toBe(true);
		expect(error.details.length).toBeGreaterThan(0);
	});

	it("rejects an unknown field in banners and names it", () => {
		const error = failure({ api, banners: { size: 5 } });

		expect(error.details).toEqual([{ path: "/banners", message: "must NOT have additional properties: size" }]);
	});
});

describe("validateAppConfig: invalid configs", () => {
	it.each([
		["null", null],
		["a list", []],
		["a text", "config"],
		["a number", 7],
	])("rejects %s instead of an object", (_name, raw) => {
		const error = failure(raw);

		expect(error.code).toBe("config-invalid");
		expect(error.details.length).toBeGreaterThan(0);
	});

	it("rejects a config without api and names the missing field", () => {
		const error = failure({});

		expect(error.code).toBe("config-invalid");
		expect(error.details).toEqual([{ path: "", message: "must have required property 'api'" }]);
	});

	it("rejects an api without url", () => {
		const error = failure({ api: {} });

		expect(error.details).toEqual([{ path: "/api", message: "must have required property 'url'" }]);
	});

	it.each([
		["a url with a slash at the end", "https://backend.et.localhost/"],
		["a url without a scheme", "backend.et.localhost"],
		["a relative url", "/ezfBackend"],
		["another scheme", "ftp://backend.et.localhost"],
		["a url with a query", "https://backend.et.localhost?a=1"],
		["a url with a fragment", "https://backend.et.localhost#top"],
		["a url with a blank", "https://backend et.localhost"],
		["an empty text", ""],
	])("rejects %s", (_name, url) => {
		const error = failure({ api: { url } });

		expect(error.code).toBe("config-invalid");
		expect(error.details).toEqual([{ path: "/api/url", message: 'must match pattern "^https?://[^\\s/?#]+(/[^\\s?#]*[^\\s/?#])?$"' }]);
	});

	it("rejects a url that is no text", () => {
		const error = failure({ api: { url: 8081 } });

		expect(error.details).toEqual([{ path: "/api/url", message: "must be string" }]);
	});

	it.each([
		["0", 0],
		["a negative number", -5],
		["a decimal number", 2.5],
		["a text", "10"],
	])("rejects returnToMaxAgeMinutes that is %s", (_name, returnToMaxAgeMinutes) => {
		const error = failure({ api: { ...api, returnToMaxAgeMinutes } });

		expect(error.code).toBe("config-invalid");
		expect(error.details.every((detail) => detail.path === "/api/returnToMaxAgeMinutes")).toBe(true);
	});

	it("rejects an unknown field in api and names it", () => {
		const error = failure({ api: { ...api, port: 8081 } });

		expect(error.details).toEqual([{ path: "/api", message: "must NOT have additional properties: port" }]);
	});

	it.each(["plugins", "navigation"])("rejects the section %s, which belongs to plugins.json", (section) => {
		const error = failure({ api, [section]: {} });

		expect(error.details).toEqual([{ path: "", message: `must NOT have additional properties: ${section}` }]);
	});

	it("rejects an invalid section logging with the path of the field", () => {
		const error = failure({ api, logging: { outputs: { console: { level: "verbose" } } } });

		expect(error.details).toEqual([
			{ path: "/logging/outputs/console/level", message: "must be equal to one of the allowed values" },
		]);
	});

	it("collects all errors instead of stopping at the first", () => {
		const error = failure({ api: { url: "backend", returnToMaxAgeMinutes: 0 }, extra: true });

		expect(error.details.map((detail) => detail.path).sort()).toEqual(["", "/api/returnToMaxAgeMinutes", "/api/url"]);
	});

	it("puts the code and every error into the message of the error", () => {
		const error = failure({ api: {}, extra: true });

		expect(error).toBeInstanceOf(Error);
		expect(error.name).toBe("ConfigError");
		expect(error.message).toContain("config-invalid");
		expect(error.message).toContain("/api: must have required property 'url'");
		expect(error.message).toContain("must NOT have additional properties: extra");
	});
});

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { validateAppConfig } from "../../../../../src/core/config/validateAppConfig";
import { validatePluginSelection } from "../../../../../src/core/config/validatePluginSelection";

const read = (path: string): unknown => JSON.parse(readFileSync(path, "utf-8"));

describe("template configs/config.example.json", () => {
	it("is a valid app config, so that copying it gives a working config.json", () => {
		expect(() => validateAppConfig(read("configs/config.example.json"))).not.toThrow();
	});

	it("shows the section api and the optional sections logging and banners", () => {
		const template = validateAppConfig(read("configs/config.example.json"));

		expect(template.api.url).toBeDefined();
		expect(template.logging?.outputs?.console?.level).toBeDefined();
		expect(template.banners?.maxVisible).toBeDefined();
	});

	it("shows the settings of the connection loss with their defaults", () => {
		const template = validateAppConfig(read("configs/config.example.json"));

		expect(template.api.connection).toEqual({ failuresBeforeWarning: 1, retryIntervalSeconds: 5, logoutAfterSeconds: 300 });
	});
});

describe("template configs/plugins.example.json", () => {
	it("is a valid plugin selection, so that copying it gives a working plugins.json", () => {
		expect(() => validatePluginSelection(read("configs/plugins.example.json"))).not.toThrow();
	});

	it("lists plugins and shows the optional section navigation", () => {
		const template = validatePluginSelection(read("configs/plugins.example.json"));

		expect(Object.keys(template.plugins).length).toBeGreaterThan(0);
		expect(template.navigation?.start).toBeDefined();
	});
});

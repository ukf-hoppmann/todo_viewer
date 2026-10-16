import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
	vi.unstubAllEnvs();
	vi.resetModules();
});

describe("standard logging object", () => {
	it("writes to the console from level debug in development mode", async () => {
		vi.stubEnv("DEV", true);
		const { logging } = await import("../../../../../src/core/logging/logging");

		expect(logging.effectiveLevel("console", "core")).toBe("debug");
	});

	it("writes to the console from level warn otherwise", async () => {
		vi.stubEnv("DEV", false);
		const { logging } = await import("../../../../../src/core/logging/logging");

		expect(logging.effectiveLevel("console", "core")).toBe("warn");
	});

	it("is one object for all importers", async () => {
		const first = await import("../../../../../src/core/logging/logging");
		const second = await import("../../../../../src/core/logging/logging");

		expect(first.logging).toBe(second.logging);
	});
});

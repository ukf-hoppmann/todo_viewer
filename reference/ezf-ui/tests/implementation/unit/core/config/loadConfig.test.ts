import { afterEach, describe, expect, it, vi } from "vitest";
import { ConfigError } from "../../../../../src/core/config/ConfigError";
import { FileConfigSource } from "../../../../../src/core/config/FileConfigSource";
import { loadConfig } from "../../../../../src/core/config/loadConfig";
import type { ConfigSource } from "../../../../../src/core/config/types";
import { validateAppConfig } from "../../../../../src/core/config/validateAppConfig";

const api = { url: "https://backend.et.localhost" };

function fakeSource(result: () => Promise<unknown>): ConfigSource {
	return { load: result };
}

async function failure(promise: Promise<unknown>): Promise<ConfigError> {
	try {
		await promise;
	} catch (error) {
		if (error instanceof ConfigError) return error;
		throw error;
	}
	throw new Error("did not throw");
}

function stubFetch(response: Response | Error) {
	const fetchMock = vi.fn(async () => {
		if (response instanceof Error) throw response;
		return response;
	});
	vi.stubGlobal("fetch", fetchMock);
	return fetchMock;
}

describe("loadConfig", () => {
	it("returns a valid config from the source", async () => {
		const config = { api };

		await expect(loadConfig(fakeSource(async () => config), validateAppConfig)).resolves.toEqual(config);
	});

	it("rejects data that do not match the schema with config-invalid", async () => {
		const error = await failure(loadConfig(fakeSource(async () => ({ api: 5 })), validateAppConfig));

		expect(error.code).toBe("config-invalid");
		expect(error.details[0]?.path).toBe("/api");
	});

	it("passes on a ConfigError of the source unchanged", async () => {
		const original = new ConfigError("config-not-json", "no json");

		const error = await failure(loadConfig(fakeSource(async () => Promise.reject(original)), validateAppConfig));

		expect(error).toBe(original);
	});

	it("turns any other failure of the source into config-unreachable and keeps the cause", async () => {
		const cause = new Error("boom");

		const error = await failure(loadConfig(fakeSource(async () => Promise.reject(cause)), validateAppConfig));

		expect(error.code).toBe("config-unreachable");
		expect(error.cause).toBe(cause);
	});
});

describe("FileConfigSource", () => {
	afterEach(() => {
		vi.unstubAllGlobals();
	});

	it("loads the given file without using a cache and returns the parsed content", async () => {
		const fetchMock = stubFetch(new Response(JSON.stringify({ plugins: {} }), { status: 200 }));

		await expect(new FileConfigSource("/plugins.json").load()).resolves.toEqual({ plugins: {} });

		expect(fetchMock).toHaveBeenCalledWith("/plugins.json", { cache: "no-store" });
	});

	it("names the file in the message of an error", async () => {
		stubFetch(new Response("x", { status: 404 }));

		const error = await failure(new FileConfigSource("/plugins.json").load());

		expect(error.message).toContain("/plugins.json");
	});

	it("reports a network error as config-unreachable with the cause", async () => {
		const cause = new TypeError("Failed to fetch");
		stubFetch(cause);

		const error = await failure(new FileConfigSource("/config.json").load());

		expect(error.code).toBe("config-unreachable");
		expect(error.cause).toBe(cause);
	});

	it.each([404, 500, 204])("reports the HTTP status %i as config-unreachable and names it", async (status) => {
		stubFetch(new Response(status === 204 ? null : "x", { status }));

		const error = await failure(new FileConfigSource("/config.json").load());

		expect(error.code).toBe("config-unreachable");
		expect(error.message).toContain(String(status));
	});

	it("reports content that is no JSON as config-not-json", async () => {
		stubFetch(new Response("{ not json", { status: 200 }));

		const error = await failure(new FileConfigSource("/config.json").load());

		expect(error.code).toBe("config-not-json");
	});

	it("reports an empty file as config-not-json", async () => {
		stubFetch(new Response("", { status: 200 }));

		const error = await failure(new FileConfigSource("/config.json").load());

		expect(error.code).toBe("config-not-json");
	});

	it("works together with loadConfig for a valid file", async () => {
		stubFetch(new Response(JSON.stringify({ api }), { status: 200 }));

		await expect(loadConfig(new FileConfigSource("/config.json"), validateAppConfig)).resolves.toEqual({ api });
	});
});

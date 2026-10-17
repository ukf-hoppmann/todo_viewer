import { createSlice } from "@reduxjs/toolkit";
import { describe, expect, it } from "vitest";
import { createPluginApi } from "../../../../../../client/src/core/api/createPluginApi";

import { initI18n } from "../../../../../../client/src/core/i18n/initI18n";
import { createLogging } from "../../../../../../client/src/core/logging/createLogging";
import { createPluginRegistry } from "../../../../../../client/src/core/plugins/createPluginRegistry";
import type { PluginCatalogue, PluginSelection } from "../../../../../../client/src/core/plugins/types";
import { createAppStore } from "../../../../../../client/src/core/store/createAppStore";
import { fakeConnection } from "../../../../../helpers/client/fakeBackend";

const { connection } = fakeConnection();

const i18n = { de: {}, en: {}, fr: {} };

/** A slice with a counter; its own name has nothing to do with the plugin id. */
function counter(name = "counter", initial = 0) {
	return createSlice({ name, initialState: { value: initial }, reducers: { up: (state) => void (state.value += 1) } });
}

function entry(definition: Record<string, unknown>, ...requires: string[]) {
	return { manifest: { requires }, load: async () => ({ plugin: { i18n, ...definition } }) };
}

function enabled(...ids: string[]): PluginSelection {
	return { plugins: Object.fromEntries(ids.map((id) => [id, { enabled: true }])) };
}

async function registryOf(config: PluginSelection, catalogue: PluginCatalogue) {
	return createPluginRegistry({
		config,
		catalogue,
		i18n: await initI18n({ lng: "en" }),
		logger: createLogging().forOrigin("core"),
	});
}

describe("createAppStore: compartments of the plugins", () => {
	it("puts the reducer of each active plugin under its id, whatever the slice is called", async () => {
		const registry = await registryOf(enabled("a", "b"), {
			a: entry({ reducer: counter("something-else", 1).reducer }),
			b: entry({ reducer: counter("b", 5).reducer }),
		});

		const store = createAppStore({ registry, connection });

		expect(store.getState()).toEqual({ a: { value: 1 }, b: { value: 5 } });
	});

	it("handles the actions of a plugin in its own compartment only", async () => {
		const a = counter("a");
		const registry = await registryOf(enabled("a", "b"), { a: entry({ reducer: a.reducer }), b: entry({ reducer: counter("b").reducer }) });
		const store = createAppStore({ registry, connection });

		store.dispatch(a.actions.up());

		expect(store.getState()).toEqual({ a: { value: 1 }, b: { value: 0 } });
	});

	it("has no compartment for a plugin without a reducer", async () => {
		const registry = await registryOf(enabled("a", "b"), { a: entry({}), b: entry({ reducer: counter().reducer }) });

		expect(Object.keys(createAppStore({ registry, connection }).getState())).toEqual(["b"]);
	});

	it("has no compartment for a plugin that is switched off", async () => {
		const registry = await registryOf(
			{ plugins: { a: { enabled: false }, b: { enabled: true } } },
			{ a: entry({ reducer: counter().reducer }), b: entry({ reducer: counter().reducer }) },
		);

		expect(Object.keys(createAppStore({ registry, connection }).getState())).toEqual(["b"]);
	});

	it("has no compartment for a plugin that failed or is blocked by one that failed", async () => {
		const registry = await registryOf(enabled("a", "b", "c"), {
			a: entry({ reducer: counter().reducer }, "b"),
			b: entry({ reducer: "no function" }),
			c: entry({ reducer: counter().reducer }),
		});

		expect(Object.keys(createAppStore({ registry, connection }).getState())).toEqual(["c"]);
	});

	it("builds a store without any compartment", async () => {
		const registry = await registryOf(enabled("a"), { a: entry({}) });

		expect(createAppStore({ registry, connection }).getState()).toEqual({});
	});
});

describe("createAppStore: compartments of the core", () => {
	it("takes over the compartments of the core under the names given", async () => {
		const registry = await registryOf(enabled("a"), { a: entry({ reducer: counter().reducer }) });

		const store = createAppStore({ registry, connection, coreSlices: { "core.thing": counter("x", 7).reducer } });

		expect(store.getState()).toEqual({ a: { value: 0 }, "core.thing": { value: 7 } });
	});

	it("refuses a compartment of the core whose name is a plugin id", async () => {
		const registry = await registryOf(enabled("a"), { a: entry({ reducer: counter().reducer }) });

		expect(() => createAppStore({ registry, connection, coreSlices: { a: counter().reducer } })).toThrow("'a'");
	});
});

describe("createAppStore: failures", () => {
	it("lets a reducer that throws for the initial state fail the build", async () => {
		const registry = await registryOf(enabled("a"), {
			a: entry({
				reducer: () => {
					throw new Error("broken");
				},
			}),
		});

		expect(() => createAppStore({ registry, connection })).toThrow("broken");
	});
});

/** An API with the endpoint `getVersion` at `<id>/version`; every plugin calls its endpoint the same. */
function versionApi(id: string) {
	return createPluginApi(id, (build) => ({
		getVersion: build.query<string, void>({ query: () => ({ url: `${id}/version`, responseHandler: "text" }) }),
	}));
}

describe("createAppStore: the caches of the APIs", () => {
	it("puts the cache of each active plugin with an api under <id>.api, next to its compartment", async () => {
		const registry = await registryOf(enabled("a", "b"), {
			a: entry({ api: versionApi("a") }),
			b: entry({ api: versionApi("b"), reducer: counter().reducer }),
		});

		const state = createAppStore({ registry, connection }).getState();

		expect(Object.keys(state).sort()).toEqual(["a.api", "b", "b.api"]);
	});

	it("has no cache for a plugin that is switched off, blocked, failed, or has no api", async () => {
		const registry = await registryOf(
			{ plugins: { off: { enabled: false }, blocked: { enabled: true }, failed: { enabled: true }, plain: { enabled: true }, good: { enabled: true } } },
			{
				off: entry({ api: versionApi("off") }),
				blocked: entry({ api: versionApi("blocked") }, "failed"),
				failed: entry({ api: versionApi("other") }),
				plain: entry({}),
				good: entry({ api: versionApi("good") }),
			},
		);

		expect(Object.keys(createAppStore({ registry, connection }).getState())).toEqual(["good.api"]);
	});

	it("lets two plugins use the same endpoint name without disturbing each other", async () => {
		const apiA = versionApi("a");
		const apiB = versionApi("b");
		const backend = fakeConnection({ "/a/version": new Response("A"), "/b/version": new Response("B") });
		const registry = await registryOf(enabled("a", "b"), { a: entry({ api: apiA }), b: entry({ api: apiB }) });
		const store = createAppStore({ registry, connection: backend.connection });

		const [a, b] = await Promise.all([
			store.dispatch(apiA.endpoints.getVersion.initiate()),
			store.dispatch(apiB.endpoints.getVersion.initiate()),
		]);

		expect([a.data, b.data]).toEqual(["A", "B"]);
		expect(backend.requests.map((request) => new URL(request.url).pathname).sort()).toEqual(["/a/version", "/b/version"]);
		const state = store.getState() as Record<string, { queries: Record<string, { data?: unknown }> }>;
		expect(state["a.api"]!.queries["getVersion(undefined)"]!.data).toBe("A");
		expect(state["b.api"]!.queries["getVersion(undefined)"]!.data).toBe("B");
	});

	it("hands the connection to the requests of the APIs", async () => {
		const api = versionApi("a");
		const backend = fakeConnection({ "/a/version": new Response(null, { status: 503 }) });
		const registry = await registryOf(enabled("a"), { a: entry({ api }) });
		const store = createAppStore({ registry, connection: backend.connection });

		const result = await store.dispatch(api.endpoints.getVersion.initiate());

		expect(result.error).toMatchObject({ status: 503, kind: "unreachable" });
		expect(backend.onFailure).toHaveBeenCalledExactlyOnceWith("unreachable");
	});
});

describe("createAppStore: the APIs of the core", () => {
	it("takes over the APIs of the core under their own key and serves their requests", async () => {
		const coreApi = createPluginApi("core", (build) => ({ ping: build.query<string, void>({ query: () => ({ url: "ping", responseHandler: "text" }) }) }));
		const backend = fakeConnection({ "/ping": new Response("pong") });
		const registry = await registryOf(enabled("a"), { a: entry({ reducer: counter().reducer }) });

		const store = createAppStore({ registry, connection: backend.connection, coreApis: [coreApi] });

		expect(Object.keys(store.getState()).sort()).toEqual(["a", "core.api"]);
		expect((await store.dispatch(coreApi.endpoints.ping.initiate())).data).toBe("pong");
	});

	it("refuses two APIs with the same key", async () => {
		const registry = await registryOf(enabled("a"), { a: entry({}) });
		const coreApis = [createPluginApi("core", () => ({})), createPluginApi("core", () => ({}))];

		expect(() => createAppStore({ registry, connection, coreApis })).toThrow("'core.api'");
	});

	it("refuses an API whose key is a compartment of the core", async () => {
		const registry = await registryOf(enabled("a"), { a: entry({}) });

		expect(() =>
			createAppStore({ registry, connection, coreSlices: { "core.api": counter().reducer }, coreApis: [createPluginApi("core", () => ({}))] }),
		).toThrow("'core.api'");
	});
});

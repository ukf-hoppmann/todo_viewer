import { configureStore } from "@reduxjs/toolkit";
import { describe, expect, it, vi } from "vitest";
import { createPluginApi } from "../../../../../../client/src/core/api/createPluginApi";
import type { Connection, PluginApi } from "../../../../../../client/src/core/api/types";
import { fakeBackendUrl, fakeConnection } from "../../../../../helpers/client/fakeBackend";

const exampleApi = createPluginApi("example", (build) => ({
	getVersion: build.query<string, void>({
		query: () => ({ url: "version", responseHandler: "text" }),
	}),
}));

/** The store as `createAppStore` builds it for one API: the connection is the extra argument. */
function storeOf(api: PluginApi, connection?: Connection) {
	return configureStore({
		reducer: { [api.reducerPath]: api.reducer },
		middleware: (getDefault) => getDefault({ thunk: { extraArgument: { connection } } }).concat(api.middleware),
	});
}

describe("createPluginApi: the key", () => {
	it("is <owner id>.api", () => {
		expect(exampleApi.reducerPath).toBe("example.api");
		expect(createPluginApi("core", () => ({})).reducerPath).toBe("core.api");
	});

	it("fits the field `api` of a plugin definition", () => {
		const api: PluginApi = exampleApi;

		expect(api.reducerPath).toBe("example.api");
	});
});

describe("createPluginApi: the request", () => {
	it("goes over the connection of the store: <url>/<endpoint>", async () => {
		const { connection, requests } = fakeConnection({ "/version": new Response("1.2.3") });
		const store = storeOf(exampleApi, connection);

		const result = await store.dispatch(exampleApi.endpoints.getVersion.initiate());

		expect(result.data).toBe("1.2.3");
		expect(requests[0]!.url).toBe(`${fakeBackendUrl}/version`);
	});

	it("keeps the answer in the cache under its key", async () => {
		const { connection, requests } = fakeConnection({ "/version": new Response("1.2.3") });
		const store = storeOf(exampleApi, connection);

		await store.dispatch(exampleApi.endpoints.getVersion.initiate());
		await store.dispatch(exampleApi.endpoints.getVersion.initiate());

		expect(Object.keys(store.getState())).toEqual(["example.api"]);
		expect(requests).toHaveLength(1);
	});

	it("asks the connection of each store, not one that was fixed at the import", async () => {
		const first = fakeConnection({ "/version": new Response("1") });
		const second = fakeConnection({ "/version": new Response("2") });

		const one = await storeOf(exampleApi, first.connection).dispatch(exampleApi.endpoints.getVersion.initiate());
		const two = await storeOf(exampleApi, second.connection).dispatch(exampleApi.endpoints.getVersion.initiate());

		expect([one.data, two.data]).toEqual(["1", "2"]);
		expect([first.requests.length, second.requests.length]).toEqual([1, 1]);
	});

	it("ends with an error that carries the kind of the failure, and reports it", async () => {
		const { connection, onFailure } = fakeConnection({ "/version": new Response(null, { status: 503 }) });
		const store = storeOf(exampleApi, connection);

		const result = await store.dispatch(exampleApi.endpoints.getVersion.initiate());

		expect(result.isError).toBe(true);
		expect(result.error).toMatchObject({ status: 503, kind: "unreachable" });
		expect(onFailure).toHaveBeenCalledExactlyOnceWith("unreachable");
	});

	it("ends with a plain error for a status the caller handles", async () => {
		const { connection, onFailure } = fakeConnection();
		const store = storeOf(exampleApi, connection);

		const result = await store.dispatch(exampleApi.endpoints.getVersion.initiate());

		expect(result.error).toMatchObject({ status: 404 });
		expect(result.error).not.toHaveProperty("kind");
		expect(onFailure).not.toHaveBeenCalled();
	});

	it("names the missing connection when the store was built without one", async () => {
		const spy = vi.spyOn(console, "error").mockImplementation(() => {});
		try {
			const result = await storeOf(exampleApi).dispatch(exampleApi.endpoints.getVersion.initiate());

			expect(result.isError).toBe(true);
			expect(result.error).toMatchObject({ message: expect.stringContaining("without a connection") });
		} finally {
			spy.mockRestore();
		}
	});
});

describe("createPluginApi: tags", () => {
	it("lets the owner invalidate the cache of its own API with tags", async () => {
		const tagged = createPluginApi(
			"tagged",
			(build) => ({
				getThing: build.query<string, void>({ query: () => ({ url: "thing", responseHandler: "text" }), providesTags: ["Thing"] }),
			}),
			{ tagTypes: ["Thing"] },
		);
		const { connection, requests } = fakeConnection({ "/thing": new Response("x") });
		const store = storeOf(tagged, connection);
		await store.dispatch(tagged.endpoints.getThing.initiate());

		store.dispatch(tagged.util.invalidateTags(["Thing"]));

		await vi.waitFor(() => expect(requests).toHaveLength(2));
	});
});

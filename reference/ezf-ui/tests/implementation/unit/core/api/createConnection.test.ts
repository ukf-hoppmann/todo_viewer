import type { BaseQueryApi } from "@reduxjs/toolkit/query";
import { describe, expect, it, vi } from "vitest";
import { createConnection } from "../../../../../src/core/api/createConnection";
import { fakeBackendUrl, fakeConnection, fakeFetch } from "../../../../helpers/fakeBackend";

/** What RTK Query hands to the base query with each request. */
function baseQueryApi(signal: AbortSignal = new AbortController().signal): BaseQueryApi {
	return { signal, abort: () => {}, dispatch: vi.fn(), getState: () => ({}), extra: undefined, endpoint: "getVersion", type: "query" };
}

const text = { url: "version", responseHandler: "text" as const };

describe("createConnection: the request", () => {
	it("asks <url>/<endpoint> with the cookies", async () => {
		const { connection, requests } = fakeConnection({ "/version": new Response("1.2.3") });

		await connection.baseQuery(text, baseQueryApi(), {});

		expect(requests).toHaveLength(1);
		expect(requests[0]!.url).toBe(`${fakeBackendUrl}/version`);
		expect(requests[0]!.method).toBe("GET");
		expect(requests[0]!.credentials).toBe("include");
	});

	it("takes an endpoint written as a plain string", async () => {
		const { connection, requests } = fakeConnection({ "/ping": new Response("{}") });

		await connection.baseQuery("ping", baseQueryApi(), {});

		expect(requests[0]!.url).toBe(`${fakeBackendUrl}/ping`);
	});

	it("returns the data of a successful answer", async () => {
		const { connection, onFailure } = fakeConnection({ "/version": new Response("1.2.3") });

		const result = await connection.baseQuery(text, baseQueryApi(), {});

		expect(result).toMatchObject({ data: "1.2.3" });
		expect(result.error).toBeUndefined();
		expect(onFailure).not.toHaveBeenCalled();
	});
});

describe("createConnection: not logged in", () => {
	it.each([401, 407])("ends the request with kind 'unauthorized' and reports it once for the status %i", async (status) => {
		const { connection, onFailure } = fakeConnection({ "/version": new Response(null, { status }) });

		const result = await connection.baseQuery(text, baseQueryApi(), {});

		expect(result.error).toMatchObject({ status, kind: "unauthorized" });
		expect(onFailure).toHaveBeenCalledExactlyOnceWith("unauthorized");
	});

	it("also recognises the status when the answer is no JSON", async () => {
		const html = () => new Response("<html>login</html>", { status: 401, headers: { "content-type": "text/html" } });
		const { connection, onFailure } = fakeConnection({ "/data": html });

		const result = await connection.baseQuery("data", baseQueryApi(), {});

		expect(result.error).toMatchObject({ status: "PARSING_ERROR", originalStatus: 401, kind: "unauthorized" });
		expect(onFailure).toHaveBeenCalledExactlyOnceWith("unauthorized");
	});
});

describe("createConnection: no answer from the backend", () => {
	it.each([500, 503])("ends the request with kind 'unreachable' and reports it once for the status %i", async (status) => {
		const { connection, onFailure } = fakeConnection({ "/version": new Response(null, { status }) });

		const result = await connection.baseQuery(text, baseQueryApi(), {});

		expect(result.error).toMatchObject({ status, kind: "unreachable" });
		expect(onFailure).toHaveBeenCalledExactlyOnceWith("unreachable");
	});

	it("also recognises the status when the answer is no JSON (a gateway page)", async () => {
		const html = () => new Response("<html>Bad Gateway</html>", { status: 502, headers: { "content-type": "text/html" } });
		const { connection, onFailure } = fakeConnection({ "/data": html });

		const result = await connection.baseQuery("data", baseQueryApi(), {});

		expect(result.error).toMatchObject({ status: "PARSING_ERROR", originalStatus: 502, kind: "unreachable" });
		expect(onFailure).toHaveBeenCalledExactlyOnceWith("unreachable");
	});

	it("treats a network error as 'unreachable'", async () => {
		const { connection, onFailure } = fakeConnection({ "/version": new TypeError("Failed to fetch") });

		const result = await connection.baseQuery(text, baseQueryApi(), {});

		expect(result.error).toMatchObject({ status: "FETCH_ERROR", kind: "unreachable" });
		expect(onFailure).toHaveBeenCalledExactlyOnceWith("unreachable");
	});

	it("treats a timeout as 'unreachable'", async () => {
		const { connection, onFailure } = fakeConnection({ "/version": new DOMException("too slow", "TimeoutError") });

		const result = await connection.baseQuery(text, baseQueryApi(), {});

		expect(result.error).toMatchObject({ status: "TIMEOUT_ERROR", kind: "unreachable" });
		expect(onFailure).toHaveBeenCalledExactlyOnceWith("unreachable");
	});
});

describe("createConnection: failures the caller handles", () => {
	it.each([400, 404, 409])("returns the error for the status %i without a kind and without a report", async (status) => {
		const body = () => new Response(JSON.stringify({ message: "no" }), { status, headers: { "content-type": "application/json" } });
		const { connection, onFailure } = fakeConnection({ "/data": body });

		const result = await connection.baseQuery("data", baseQueryApi(), {});

		expect(result.error).toEqual({ status, data: { message: "no" } });
		expect(onFailure).not.toHaveBeenCalled();
	});

	it("returns an answer that cannot be read as an error without a kind and without a report", async () => {
		const { connection, onFailure } = fakeConnection({ "/data": new Response("not json", { status: 200 }) });

		const result = await connection.baseQuery("data", baseQueryApi(), {});

		expect(result.error).toMatchObject({ status: "PARSING_ERROR", originalStatus: 200 });
		expect(result.error).not.toHaveProperty("kind");
		expect(onFailure).not.toHaveBeenCalled();
	});

	it("does not report a request that the caller aborted", async () => {
		const { connection, onFailure } = fakeConnection({ "/version": new Response("1.2.3") });
		const controller = new AbortController();
		controller.abort();

		const result = await connection.baseQuery(text, baseQueryApi(controller.signal), {});

		expect(result.error).toMatchObject({ status: "FETCH_ERROR" });
		expect(result.error).not.toHaveProperty("kind");
		expect(onFailure).not.toHaveBeenCalled();
	});
});

describe("createConnection: the fetch", () => {
	it("uses the global fetch when none is given", async () => {
		const backend = fakeFetch({ "/version": new Response("1.2.3") });
		const spy = vi.spyOn(globalThis, "fetch").mockImplementation(async (request) => backend.fetch(request as Request));
		try {
			const connection = createConnection({ url: fakeBackendUrl, onFailure: () => {} });

			const result = await connection.baseQuery(text, baseQueryApi(), {});

			expect(result).toMatchObject({ data: "1.2.3" });
		} finally {
			spy.mockRestore();
		}
	});
});

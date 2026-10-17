import { vi } from "vitest";
import { createConnection } from "../../../client/src/core/api/createConnection";
import type { ConnectionFetch } from "../../../client/src/core/api/types";
import { coreApi } from "../../../client/src/core/ui-state/coreApi";
import { createAppStore } from "../../../client/src/core/store/createAppStore";

const url = "https://backend.test/api";

/**
 * A server for `GET/PUT /core/ui-state/{owner}` that keeps the documents and the requests it got, and a store
 * with the API of the core on a connection to it.
 */
export function fakeUiStateBackend(initial: Record<string, Record<string, unknown>> = {}, options: { failGet?: boolean } = {}) {
	const documents = new Map(Object.entries(initial));
	const requests: Array<{ method: string; owner: string; body?: unknown }> = [];
	const fetch = vi.fn<ConnectionFetch>(async (request) => {
		const owner = new URL(request.url).pathname.split("/").at(-1)!;
		const body = request.method === "PUT" ? ((await request.json()) as { document: Record<string, unknown> }) : undefined;
		requests.push({ method: request.method, owner, body });
		if (request.method === "GET" && options.failGet) return new Response(null, { status: 503 });
		if (body) documents.set(owner, body.document);
		return Response.json({ owner, document: documents.get(owner) ?? {} });
	});
	const connection = createConnection({ url, fetch, onFailure: () => {} });
	const store = createAppStore({ registry: { active: () => [], statuses: () => [] }, connection, coreApis: [coreApi] });
	return { store, documents, requests, puts: () => requests.filter((request) => request.method === "PUT") };
}

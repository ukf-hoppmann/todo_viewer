import { vi } from "vitest";
import { createConnection } from "../../../client/src/core/api/createConnection";
import type { ConnectionFetch } from "../../../client/src/core/api/types";
import { createAppStore } from "../../../client/src/core/store/createAppStore";
import { coreApi } from "../../../client/src/core/ui-state/coreApi";
import type { PluginRegistry } from "../../../client/src/core/plugins/types";
import { workspaceApi, type FolderListing, type Project } from "../../../client/src/plugins/workspace/api";

const url = "https://backend.test/api";

export function project(uid: string, name: string, position: number, extra: Partial<Project> = {}): Project {
	return {
		uid,
		name,
		position,
		version: 1,
		builtin: false,
		mirror_folder: null,
		mirror_enabled: false,
		auto_sync: false,
		sync_direction: "both",
		created_at: "2026-10-16T10:00:00Z",
		...extra,
	};
}

/**
 * A server for the UI state and for the projects of the workspace plugin. It keeps the projects, the UI
 * documents and the requests it got; `folders` is what the folder browser sees by path, `removeNeedsConfirm`
 * is the number of elements a project holds (removing needs `confirm` then).
 */
export function fakeWorkspaceBackend(
	options: {
		projects?: Project[];
		documents?: Record<string, Record<string, unknown>>;
		folders?: Record<string, FolderListing>;
		elementsInProjects?: Record<string, number>;
	} = {},
) {
	let projects = options.projects ?? [project("p0", "Allgemein", 0, { builtin: true })];
	const documents = new Map(Object.entries(options.documents ?? {}));
	const requests: Array<{ method: string; path: string; query: URLSearchParams; body?: unknown }> = [];
	const fetch = vi.fn<ConnectionFetch>(async (request) => {
		const { pathname, searchParams } = new URL(request.url);
		const path = pathname.replace(/^\/api\//, "");
		const body = request.method === "GET" || request.method === "DELETE" ? undefined : ((await request.json()) as Record<string, unknown>);
		requests.push({ method: request.method, path, query: searchParams, body });

		if (path.startsWith("core/ui-state/")) {
			const owner = path.split("/").at(-1)!;
			if (body) documents.set(owner, (body as { document: Record<string, unknown> }).document);
			return Response.json({ owner, document: documents.get(owner) ?? {} });
		}
		if (path === "workspace/projects" && request.method === "GET") return Response.json(projects);
		if (path === "workspace/projects" && request.method === "POST") {
			if (projects.some((entry) => entry.name === body!.name)) {
				return Response.json({ code: "project_name_taken", message: "Der Name ist schon vergeben", details: {} }, { status: 409 });
			}
			const created = project(`p${projects.length}`, String(body!.name), projects.length, body as Partial<Project>);
			projects = [...projects, created];
			return Response.json(created);
		}
		const move = /^workspace\/projects\/([^/]+)\/move$/.exec(path);
		if (move) {
			const source = projects.find((entry) => entry.uid === move[1])!;
			const rest = projects.filter((entry) => entry !== source);
			rest.splice(Number(body!.position), 0, source);
			projects = rest.map((entry, position) => ({ ...entry, position, version: entry.version + 1 }));
			return Response.json(projects);
		}
		const one = /^workspace\/projects\/([^/]+)$/.exec(path);
		if (one && request.method === "PUT") {
			projects = projects.map((entry) => (entry.uid === one[1] ? { ...entry, ...(body as Partial<Project>), version: entry.version + 1 } : entry));
			return Response.json(projects.find((entry) => entry.uid === one[1]));
		}
		if (one && request.method === "DELETE") {
			const count = options.elementsInProjects?.[one[1]!] ?? 0;
			if (count > 0 && searchParams.get("confirm") !== "true") {
				return Response.json({ code: "project_not_empty", message: "nicht leer", details: { elements: count } }, { status: 400 });
			}
			projects = projects.filter((entry) => entry.uid !== one[1]);
			return Response.json({ trashed: count });
		}
		if (path === "workspace/folders") {
			const listing = options.folders?.[searchParams.get("path") ?? ""];
			return listing ? Response.json(listing) : new Response(null, { status: 404 });
		}
		return new Response(null, { status: 404 });
	});
	const connection = createConnection({ url, fetch, onFailure: () => {} });
	const registry: PluginRegistry = {
		active: () => [{ id: "workspace", definition: { i18n: { de: {}, en: {} }, api: workspaceApi } }],
		statuses: () => [],
	} as unknown as PluginRegistry;
	const store = createAppStore({ registry, connection, coreApis: [coreApi] });
	return {
		store,
		documents,
		requests,
		projects: () => projects,
		calls: (method: string, pathPart: string) => requests.filter((entry) => entry.method === method && entry.path.includes(pathPart)),
	};
}

/** Waits until the UI document of the owner on the server equals `expected` (a write is async and delayed). */
export async function expectPersisted(
	backend: ReturnType<typeof fakeWorkspaceBackend>,
	flush: (store: ReturnType<typeof fakeWorkspaceBackend>["store"]) => Promise<void>,
	waitFor: (check: () => Promise<void>) => Promise<unknown>,
	expected: unknown,
	owner = "workspace",
) {
	await waitFor(async () => {
		await flush(backend.store);
		if (JSON.stringify(backend.documents.get(owner)) !== JSON.stringify(expected)) {
			throw new Error(`UI state of ${owner}: ${JSON.stringify(backend.documents.get(owner))}`);
		}
	});
}

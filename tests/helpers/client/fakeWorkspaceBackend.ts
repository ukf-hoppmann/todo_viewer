import { vi } from "vitest";
import { createConnection } from "../../../client/src/core/api/createConnection";
import type { ConnectionFetch } from "../../../client/src/core/api/types";
import { createAppStore } from "../../../client/src/core/store/createAppStore";
import { coreApi } from "../../../client/src/core/ui-state/coreApi";
import type { PluginRegistry } from "../../../client/src/core/plugins/types";
import type { SyncPreview, SyncResult, SyncStatus } from "../../../client/src/plugins/workspace/api";
import { backlogApi, type DocumentOut, type IndexItem, type ItemOut } from "../../../client/src/plugins/backlog/api";
import { workspaceApi, type ElementOut, type FolderListing, type LinkedElement, type Project, type TrashedElement } from "../../../client/src/plugins/workspace/api";

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
		/** Elements for the search and the links; a link is `[linkUid, fromUid, toUid, role]`. */
		elements?: ElementOut[];
		links?: Array<[string, string, string, LinkedElement["role"]]>;
		/** Items of the backlog (`GET backlog/items` filters them by project) and the detail by `uid`. */
		backlog?: IndexItem[];
		details?: Record<string, ItemOut>;
		/** The documents of the items by name (`GET backlog/items/{uid}/documents/{name}`). */
		itemDocuments?: Record<string, DocumentOut>;
		/** The head of the notes by item uid (`GET backlog/items/{uid}/notes/state`) and the log entries (`…/notes/entries`). */
		notesStates?: Record<string, { state: string; content: string }>;
		notesEntries?: Record<string, Array<{ position: number; day: string; topic: string; text: string }>>;
		/** The sync state by project (`GET core/sync/{project}/status`); an in-sync state without changes if missing. */
		syncStatus?: Record<string, SyncStatus>;
		/** The preview of a sync (`GET core/sync/{project}/preview`) and the result of an execute. */
		syncPreview?: SyncPreview;
		syncResult?: SyncResult;
		/** The areas by project, for `GET backlog/areas`. */
		areas?: Record<string, string[]>;
		/** Answers a request itself (return `undefined` to let the fake answer): for errors and special cases. */
		respond?: (request: { method: string; path: string; body?: unknown; query: URLSearchParams }) => Response | undefined;
		/** More plugin APIs for the store (e.g. `notes`). */
		extraApis?: Array<{ id: string; api: unknown }>;
		/** The elements in the trash. */
		trash?: TrashedElement[];
		/** Number of children by element `uid`: deleting such an element needs `cascade`. */
		children?: Record<string, number>;
		/** Elements whose restore the plugin refuses, with the message. */
		restoreRefused?: Record<string, string>;
	} = {},
) {
	let projects = options.projects ?? [project("p0", "Allgemein", 0, { builtin: true })];
	const elements = options.elements ?? [];
	let links = options.links ?? [];
	let trash = options.trash ?? [];
	const linked = (linkUid: string, uid: string, role: LinkedElement["role"]): LinkedElement => {
		const e = elements.find((entry) => entry.uid === uid)!;
		return { link_uid: linkUid, role, uid, project_uid: e.project_uid, kind: e.kind, label: e.label, title: e.title, deleted: e.deleted };
	};
	const documents = new Map(Object.entries(options.documents ?? {}));
	const requests: Array<{ method: string; path: string; query: URLSearchParams; body?: unknown }> = [];
	const fetch = vi.fn<ConnectionFetch>(async (request) => {
		const { pathname, searchParams } = new URL(request.url);
		const path = pathname.replace(/^\/api\//, "");
		const body = request.method === "GET" || request.method === "DELETE" ? undefined : ((await request.json()) as Record<string, unknown>);
		requests.push({ method: request.method, path, query: searchParams, body });

		const custom = options.respond?.({ method: request.method, path, body, query: searchParams });
		if (custom) return custom;
		const oneDocument = /^backlog\/items\/([^/]+)\/documents\/([^/]+)$/.exec(path);
		if (oneDocument && request.method === "GET") {
			const found = options.itemDocuments?.[oneDocument[2]!];
			return found ? Response.json(found) : Response.json({ code: "document_not_found", message: "Dokument gibt es nicht", details: {} }, { status: 400 });
		}
		const notesPart = /^backlog\/items\/([^/]+)\/notes\/(state|entries)$/.exec(path);
		if (notesPart && request.method === "GET") {
			const [, uid, part] = notesPart as unknown as [string, string, string];
			if (part === "entries") return Response.json(options.notesEntries?.[uid] ?? []);
			const head = options.notesStates?.[uid];
			return head
				? Response.json({ name: "notes.md", content: head.content, stamp: null, state: head.state, checksum: "0", last_entry: null, version: 1, hints: [] })
				: Response.json({ code: "notes_not_found", message: "Keine Notes", details: {} }, { status: 400 });
		}
		const syncMatch = /^core\/sync\/([^/]+)\/(status|preview|execute)$/.exec(path);
		if (syncMatch) {
			const [, project, action] = syncMatch as unknown as [string, string, string];
			if (action === "status") {
				return Response.json(options.syncStatus?.[project] ?? { project, state: "in_sync", conflicts: 0, to_database: 0, to_files: 0, files: [], reason: null, last_sync: null });
			}
			if (action === "preview") {
				return Response.json(options.syncPreview ?? { project, direction: "both", state: "in_sync", token: "t0", transfers: [], conflicts: [], skipped: [], not_imported: [] });
			}
			return Response.json(options.syncResult ?? { project, state: "in_sync", to_database: 0, to_files: 0, created: [], conflicts_left: [] });
		}
		if (path === "backlog/areas") return Response.json({ areas: options.areas?.[searchParams.get("project") ?? ""] ?? [] });
		if (path.startsWith("backlog/items") && request.method !== "GET") {
			const uid = path.split("/")[2];
			const detail = uid ? options.details?.[uid] : undefined;
			return Response.json(detail ?? { ...(body as object), uid: uid ?? "new", version: 1 });
		}
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
		if (path === "backlog/items" && request.method === "GET") {
			const wanted = (searchParams.get("projects") ?? "").split(",").filter(Boolean);
			return Response.json((options.backlog ?? []).filter((item) => wanted.includes(item.project_uid)));
		}
		const oneItem = /^backlog\/items\/([^/]+)$/.exec(path);
		if (oneItem) {
			const detail = options.details?.[oneItem[1]!];
			return detail ? Response.json(detail) : Response.json({ code: "not_found", message: "Item gibt es nicht", details: {} }, { status: 404 });
		}
		const ofElement = /^workspace\/elements\/([^/]+)\/links$/.exec(path);
		if (ofElement) {
			const uid = ofElement[1]!;
			return Response.json({
				outgoing: links.filter((l) => l[1] === uid).map((l) => linked(l[0], l[2], l[3])),
				incoming: links.filter((l) => l[2] === uid).map((l) => linked(l[0], l[1], l[3])),
			});
		}
		if (path === "workspace/links" && request.method === "POST") {
			const b = body as { from_uid: string; to_uid: string; role: LinkedElement["role"] };
			if (links.some((l) => l[1] === b.from_uid && l[2] === b.to_uid && l[3] === b.role)) {
				return Response.json({ code: "link_exists", message: "Diese Verknüpfung gibt es schon", details: {} }, { status: 400 });
			}
			const created: [string, string, string, LinkedElement["role"]] = [`l${links.length + 1}`, b.from_uid, b.to_uid, b.role];
			links = [...links, created];
			return Response.json(linked(created[0], b.to_uid, b.role));
		}
		const oneLink = /^workspace\/links\/([^/]+)$/.exec(path);
		if (oneLink && request.method === "DELETE") {
			links = links.filter((l) => l[0] !== oneLink[1]);
			return Response.json({ removed: true });
		}
		if (path === "workspace/elements") {
			const q = (searchParams.get("query") ?? "").toLowerCase();
			return Response.json(elements.filter((e) => !e.deleted && `${e.label} ${e.title}`.toLowerCase().includes(q)));
		}
		const deleteElement = /^workspace\/elements\/([^/]+)$/.exec(path);
		if (deleteElement && request.method === "DELETE") {
			const uid = deleteElement[1]!;
			const count = options.children?.[uid] ?? 0;
			if (count > 0 && searchParams.get("cascade") !== "true") return Response.json({ has_children: true, children: count, deleted: 0 });
			const e = elements.find((entry) => entry.uid === uid);
			if (!e) return Response.json({ code: "not_found", message: "Element gibt es nicht", details: {} }, { status: 404 });
			trash = [{ uid, project_uid: e.project_uid, kind: e.kind, label: e.label, title: e.title, deleted_at: "2026-10-16T12:00:00Z" }, ...trash];
			return Response.json({ has_children: false, children: count, deleted: 1 + count });
		}
		if (path === "workspace/trash" && request.method === "GET") {
			const projectsParam = searchParams.get("projects");
			const q = (searchParams.get("query") ?? "").toLowerCase();
			return Response.json(
				trash.filter(
					(e) =>
						(projectsParam === null || projectsParam.split(",").includes(e.project_uid)) &&
						`${e.label} ${e.title}`.toLowerCase().includes(q),
				),
			);
		}
		if ((path === "workspace/trash/restore" || path === "workspace/trash/purge") && request.method === "POST") {
			const uids = (body as { uids: string[] }).uids;
			const refused = uids.find((uid) => options.restoreRefused?.[uid]);
			if (path.endsWith("restore") && refused) {
				return Response.json({ code: "parent_in_trash", message: options.restoreRefused![refused], details: {} }, { status: 400 });
			}
			trash = trash.filter((e) => !uids.includes(e.uid));
			return Response.json({ uids });
		}
		if (path === "workspace/folders") {
			const listing = options.folders?.[searchParams.get("path") ?? ""];
			return listing ? Response.json(listing) : new Response(null, { status: 404 });
		}
		return new Response(null, { status: 404 });
	});
	const connection = createConnection({ url, fetch, onFailure: () => {} });
	const registry: PluginRegistry = {
		active: () => [
			{ id: "workspace", definition: { i18n: { de: {}, en: {} }, api: workspaceApi } },
			{ id: "backlog", definition: { i18n: { de: {}, en: {} }, api: backlogApi } },
			...(options.extraApis ?? []).map((entry) => ({ id: entry.id, definition: { i18n: { de: {}, en: {} }, api: entry.api } })),
		],
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

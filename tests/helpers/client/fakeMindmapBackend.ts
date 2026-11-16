import { mindmapApi, type NodeOut } from "../../../client/src/plugins/mindmap/api";
import { fakeWorkspaceBackend } from "./fakeWorkspaceBackend";

type Options = Omit<Parameters<typeof fakeWorkspaceBackend>[0] & object, "respond" | "extraApis"> & {
	nodes?: NodeOut[];
	/** Answers a request itself; `undefined` lets the fake answer. */
	respond?: (request: { method: string; path: string; body?: unknown; query: URLSearchParams }) => Response | undefined;
};

/**
 * The workspace fake plus the `mindmap` API. It keeps the nodes: `GET mindmap/trees/{project}` lists those of the
 * project, creating, updating and moving change them, and `DELETE workspace/elements/{uid}` removes a node (with its branch
 * when `cascade` is set; without it a node with children answers `has_children`). The documents of a node are kept
 * too: reading and putting one, and an entry in the notes (which create `<LABEL>_notes.md` and list it at the node).
 */
export function fakeMindmapBackend(options: Options = {}) {
	let nodes = [...(options.nodes ?? [])];
	let created = 0;
	const documents = new Map<string, { content: string; version: number }>();
	const addName = (uid: string, name: string) => {
		nodes = nodes.map((entry) => (entry.uid === uid && !entry.documents.includes(name) ? { ...entry, documents: [...entry.documents, name] } : entry));
	};
	const branch = (uid: string): string[] => [uid, ...nodes.filter((entry) => entry.parent_uid === uid).flatMap((entry) => branch(entry.uid))];
	return fakeWorkspaceBackend({
		...options,
		extraApis: [{ id: "mindmap", api: mindmapApi }],
		respond: (request) => {
			const custom = options.respond?.(request);
			if (custom) return custom;
			const { method, path, query } = request;
			const body = (request.body ?? {}) as Record<string, unknown>;
			const tree = /^mindmap\/trees\/([^/]+)$/.exec(path);
			if (tree && method === "GET") {
				const own = nodes.filter((entry) => entry.project_uid === tree[1]);
				return Response.json({ project_uid: tree[1], tree_uid: own.length > 0 ? "t1" : null, nodes: own });
			}
			if (path === "mindmap/nodes" && method === "POST") {
				created += 1;
				const parent = (body.parent as string | undefined) ?? null;
				const node: NodeOut = {
					uid: `new${created}`,
					project_uid: body.project as string,
					label: `NODE-new${created}`,
					title: body.title as string,
					text: null,
					tree_uid: "t1",
					parent_uid: parent,
					position: nodes.filter((entry) => (entry.parent_uid ?? null) === parent).length,
					version: 1,
					documents: [],
				};
				nodes = [...nodes, node];
				return Response.json(node);
			}
			const document = /^mindmap\/nodes\/([^/]+)\/documents\/([^/]+)$/.exec(path);
			if (document) {
				const [, uid, name] = document;
				const key = `${uid}/${name}`;
				const now = "2026-11-16T12:00:00Z";
				const stored = documents.get(key);
				if (method === "GET") {
					if (!stored) return Response.json({ code: "document_not_found", message: "Das Dokument gibt es nicht", details: {} }, { status: 400 });
					return Response.json({ name, kind: "notes", content: stored.content, version: stored.version, updated_at: now });
				}
				if (method === "PUT") {
					if (stored && body.version !== stored.version) return Response.json({ code: "version_conflict", message: "Das Dokument wurde inzwischen geändert", details: {} }, { status: 409 });
					const next = { content: body.content as string, version: (stored?.version ?? 0) + 1 };
					documents.set(key, next);
					addName(uid!, name!);
					return Response.json({ name, kind: name!.endsWith("_notes.md") ? "notes" : "spec", content: next.content, version: next.version, updated_at: now });
				}
			}
			const entry = /^mindmap\/nodes\/([^/]+)\/entries$/.exec(path);
			if (entry && method === "POST") {
				const found = nodes.find((candidate) => candidate.uid === entry[1]);
				if (!found) return Response.json({ code: "not_found", message: "Knoten gibt es nicht", details: {} }, { status: 404 });
				const name = `${found.label}_notes.md`;
				const key = `${found.uid}/${name}`;
				const previous = documents.get(key);
				const content = `${previous?.content ?? `# ${found.label} — ${found.title}\n`}\n## 2026-11-16 — ${body.topic as string}\n`;
				const next = { content, version: (previous?.version ?? 0) + 1 };
				documents.set(key, next);
				addName(found.uid, name);
				return Response.json({ name, kind: "notes", content, version: next.version, updated_at: "2026-11-16T12:00:00Z" });
			}
			const one = /^mindmap\/nodes\/([^/]+)$/.exec(path);
			if (one && method === "PUT") {
				const found = nodes.find((entry) => entry.uid === one[1]);
				if (!found) return Response.json({ code: "not_found", message: "Knoten gibt es nicht", details: {} }, { status: 404 });
				const changed: NodeOut = {
					...found,
					...(typeof body.title === "string" ? { title: body.title } : {}),
					...(typeof body.text === "string" ? { text: body.text === "" ? null : body.text } : {}),
					version: found.version + 1,
				};
				nodes = nodes.map((entry) => (entry.uid === changed.uid ? changed : entry));
				return Response.json(changed);
			}
			const moved = /^mindmap\/nodes\/([^/]+)\/move$/.exec(path);
			if (moved && method === "POST") {
				const found = nodes.find((entry) => entry.uid === moved[1]);
				if (!found) return Response.json({ code: "not_found", message: "Knoten gibt es nicht", details: {} }, { status: 404 });
				const parent = (body.parent as string | null | undefined) ?? null;
				const siblingsOf = (uid: string | null) => nodes.filter((entry) => (entry.parent_uid ?? null) === uid && entry.uid !== found.uid).sort((a, b) => a.position - b.position);
				const target = siblingsOf(parent);
				const changed: NodeOut = { ...found, parent_uid: parent, version: found.version + 1 };
				target.splice(Math.min((body.position as number | undefined) ?? target.length, target.length), 0, changed);
				const placed = new Map([...siblingsOf(found.parent_uid ?? null), ...target].map((entry) => [entry.uid, entry]));
				const positions = new Map([...siblingsOf(found.parent_uid ?? null).map((entry, index) => [entry.uid, index] as const), ...target.map((entry, index) => [entry.uid, index] as const)]);
				nodes = nodes.map((entry) => (placed.has(entry.uid) ? { ...placed.get(entry.uid)!, position: positions.get(entry.uid)! } : entry));
				return Response.json(nodes.find((entry) => entry.uid === found.uid));
			}
			const element = /^workspace\/elements\/([^/]+)$/.exec(path);
			if (element && method === "DELETE" && nodes.some((entry) => entry.uid === element[1])) {
				const gone = branch(element[1]!);
				if (gone.length > 1 && query.get("cascade") !== "true") return Response.json({ has_children: true, children: gone.length - 1, deleted: 0 });
				nodes = nodes.filter((entry) => !gone.includes(entry.uid));
				return Response.json({ has_children: false, children: gone.length - 1, deleted: gone.length });
			}
			return undefined;
		},
	});
}

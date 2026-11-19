import { mindmapApi, type ItemRefOut, type MapOut, type MemoRefOut, type NodeItemOut, type TreeNodeOut } from "../../../client/src/plugins/mindmap/api";
import { fakeWorkspaceBackend } from "./fakeWorkspaceBackend";

type Options = Omit<Parameters<typeof fakeWorkspaceBackend>[0] & object, "respond" | "extraApis"> & {
	nodes?: TreeNodeOut[];
	/** The items without a node (the side view), in the order of the backlog. */
	unassigned?: ItemRefOut[];
	/** The lines between nodes the tree answers with (`from_node` → `to_node`, summed `count`). */
	dependencyLinks?: Array<{ from_node: string; to_node: string; count: number }>;
	/** The items in the detail of a node, by node `uid`; `explicit` says whether the node is theirs. */
	items?: Record<string, NodeItemOut[]>;
	/** The memos linked to a node, by node `uid`. */
	memos?: Record<string, MemoRefOut[]>;
	/** The free maps of the projects at the start (`kind` and `node_count` are kept by the fake). */
	maps?: Array<{ uid: string; project_uid: string; name: string }>;
	/** Answers a request itself; `undefined` lets the fake answer. */
	respond?: (request: { method: string; path: string; body?: unknown; query: URLSearchParams }) => Response | undefined;
};

/**
 * The workspace fake plus the `mindmap` API. It also keeps the assignments: `unassigned`, the items and memos of the
 * nodes (`assign_item` moves an item from the side view or from another node to the node, `replace` is needed for the
 * latter; `unassign_item` puts an explicit item back to the side view; memos are linked and unlinked). It keeps the nodes: `GET mindmap/trees/{project}` lists those of the
 * project, creating, updating and moving change them, and `DELETE workspace/elements/{uid}` removes a node (with its branch
 * when `cascade` is set; without it a node with children answers `has_children`). The documents of a node are kept
 * too: reading and putting one, and an entry in the notes (which create `<LABEL>_notes.md` and list it at the node).
 */
export function fakeMindmapBackend(options: Options = {}) {
	let nodes = [...(options.nodes ?? [])];
	let unassigned = [...(options.unassigned ?? [])];
	const contents = new Map<string, NodeItemOut[]>(Object.entries(options.items ?? {}).map(([uid, list]) => [uid, [...list]]));
	const memos = new Map<string, MemoRefOut[]>(Object.entries(options.memos ?? {}).map(([uid, list]) => [uid, [...list]]));
	const failure = (code: string, message: string, status = 400) => Response.json({ code, message, details: {} }, { status });
	const explicitNode = (item: string) => [...contents].find(([, list]) => list.some((entry) => entry.uid === item && entry.explicit))?.[0];
	const takeFrom = (item: string): ItemRefOut | undefined => {
		const loose = unassigned.find((entry) => entry.uid === item);
		unassigned = unassigned.filter((entry) => entry.uid !== item);
		for (const [uid, list] of contents) {
			const found = list.find((entry) => entry.uid === item && entry.explicit);
			if (found) {
				contents.set(uid, list.filter((entry) => entry !== found));
				return found;
			}
		}
		return loose;
	};
	let freeMaps = (options.maps ?? []).map((entry) => ({ ...entry, version: 1 }));
	const projectName = (uid: string) => options.projects?.find((entry) => entry.uid === uid)?.name ?? "Projekt";
	const treeOf = (entry: TreeNodeOut) => (freeMaps.some((map) => map.uid === entry.tree_uid) ? entry.tree_uid : null);
	const mapEntry = (uid: string): MapOut => {
		const found = freeMaps.find((entry) => entry.uid === uid)!;
		return { project_uid: found.project_uid, kind: "free", name: found.name, tree_uid: found.uid, node_count: nodes.filter((entry) => entry.tree_uid === uid).length, shared_count: 0, version: found.version };
	};
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
			const listed = /^mindmap\/maps\/([^/]+)$/.exec(path);
			if (listed && method === "GET") {
				const own = nodes.filter((entry) => entry.project_uid === listed[1] && treeOf(entry) === null);
				const project: MapOut = { project_uid: listed[1]!, kind: "project", name: projectName(listed[1]!), tree_uid: own.length > 0 ? "t1" : null, node_count: own.length, shared_count: 0, version: 1 };
				return Response.json([project, ...freeMaps.filter((entry) => entry.project_uid === listed[1]).map((entry) => mapEntry(entry.uid))]);
			}
			if (path === "mindmap/maps" && method === "POST") {
				const name = String(body.name ?? "").trim();
				if (name === "") return failure("mindmap_map_name_missing", "Der Name der Map fehlt");
				if (freeMaps.some((entry) => entry.project_uid === body.project && entry.name.toLowerCase() === name.toLowerCase())) return failure("mindmap_map_name_taken", `Es gibt in diesem Projekt schon eine Map '${name}'`);
				created += 1;
				freeMaps = [...freeMaps, { uid: `map${created}`, project_uid: body.project as string, name, version: 1 }];
				return Response.json(mapEntry(`map${created}`));
			}
			const changedMap = /^mindmap\/maps\/([^/]+)$/.exec(path);
			if (changedMap && method === "PUT") {
				const found = freeMaps.find((entry) => entry.uid === changedMap[1]);
				if (!found) return failure("not_found", "Map gibt es nicht", 404);
				if (body.version !== found.version) return failure("version_conflict", "Die Map wurde inzwischen geändert", 409);
				freeMaps = freeMaps.map((entry) => (entry === found ? { ...entry, name: String(body.name), version: entry.version + 1 } : entry));
				return Response.json(mapEntry(found.uid));
			}
			if (changedMap && method === "DELETE") {
				const found = freeMaps.find((entry) => entry.uid === changedMap[1]);
				if (!found) return failure("mindmap_project_tree_fixed", "Der Projektbaum lässt sich nicht löschen");
				const going = nodes.filter((entry) => entry.tree_uid === found.uid).length;
				nodes = nodes.filter((entry) => entry.tree_uid !== found.uid);
				freeMaps = freeMaps.filter((entry) => entry !== found);
				return Response.json({ tree_uid: found.uid, nodes_deleted: going, kept_elsewhere: 0 });
			}
			const tree = /^mindmap\/trees\/([^/]+)$/.exec(path);
			if (tree && method === "GET") {
				const wanted = query.get("tree");
				const own = nodes.filter((entry) => entry.project_uid === tree[1] && (wanted ? entry.tree_uid === wanted : treeOf(entry) === null));
				return Response.json({ project_uid: tree[1], tree_uid: wanted ?? (own.length > 0 ? "t1" : null), nodes: own, unassigned: wanted ? [] : unassigned, links: options.dependencyLinks ?? [] });
			}
			const content = /^mindmap\/nodes\/([^/]+)\/content$/.exec(path);
			if (content && method === "GET") {
				return Response.json({ node_uid: content[1], items: contents.get(content[1]!) ?? [], memos: memos.get(content[1]!) ?? [] });
			}
			const assign = /^mindmap\/nodes\/([^/]+)\/items$/.exec(path);
			if (assign && method === "POST") {
				const item = body.item as string;
				const target = nodes.find((entry) => entry.uid === assign[1]);
				if (!target) return failure("not_found", "Knoten gibt es nicht", 404);
				if (explicitNode(item) && body.replace !== true) return failure("mindmap_item_assigned", "Das Item hängt schon an einem Knoten");
				const taken = takeFrom(item);
				if (!taken) return failure("not_found", "Item gibt es nicht", 404);
				const { uid, label, type, title, status } = taken;
				contents.set(target.uid, [...(contents.get(target.uid) ?? []), { uid, label, type, title, status, explicit: true }]);
				return Response.json(target);
			}
			const itemNode = /^mindmap\/items\/([^/]+)\/node$/.exec(path);
			if (itemNode && method === "GET") {
				const inherited = [...contents].find(([, list]) => list.some((entry) => entry.uid === itemNode[1]));
				const own = explicitNode(itemNode[1]!);
				return Response.json({ item_uid: itemNode[1], node_uid: own ?? inherited?.[0] ?? null, explicit: own !== undefined });
			}
			if (itemNode && method === "DELETE") {
				const own = explicitNode(itemNode[1]!);
				if (!own) return failure("not_found", "Das Item ist keinem Knoten eigens zugeordnet", 404);
				const taken = takeFrom(itemNode[1]!)!;
				unassigned = [...unassigned, { uid: taken.uid, label: taken.label, type: taken.type, title: taken.title, status: taken.status }];
				return Response.json({ ok: true });
			}
			const link = /^mindmap\/nodes\/([^/]+)\/memos$/.exec(path);
			if (link && method === "POST") {
				const memo = body.memo as string;
				const list = memos.get(link[1]!) ?? [];
				if (!list.some((entry) => entry.uid === memo)) memos.set(link[1]!, [...list, { uid: memo, label: `MEMO-${memo}`, title: `Memo ${memo}` }]);
				return Response.json(nodes.find((entry) => entry.uid === link[1]) ?? {});
			}
			const unlink = /^mindmap\/nodes\/([^/]+)\/memos\/([^/]+)$/.exec(path);
			if (unlink && method === "DELETE") {
				memos.set(unlink[1]!, (memos.get(unlink[1]!) ?? []).filter((entry) => entry.uid !== unlink[2]));
				return Response.json({ ok: true });
			}
			if (path === "mindmap/nodes" && method === "POST") {
				created += 1;
				const parent = (body.parent as string | undefined) ?? null;
				const node: TreeNodeOut = {
					uid: `new${created}`,
					project_uid: body.project as string,
					label: `NODE-new${created}`,
					title: body.title as string,
					text: null,
					tree_uid: (body.tree as string | undefined) ?? "t1",
					parent_uid: parent,
					position: nodes.filter((entry) => (entry.parent_uid ?? null) === parent).length,
					version: 1,
					documents: [],
					total: 0,
					done: 0,
					state: "idea",
					mark: null,
					tree_count: 1,
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
				const changed: TreeNodeOut = {
					...found,
					...(typeof body.title === "string" ? { title: body.title } : {}),
					...(typeof body.text === "string" ? { text: body.text === "" ? null : body.text } : {}),
					...(typeof body.mark === "string" ? { mark: body.mark === "" ? null : body.mark } : {}),
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
				const changed: TreeNodeOut = { ...found, parent_uid: parent, version: found.version + 1 };
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

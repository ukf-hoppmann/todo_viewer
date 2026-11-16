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
 * when `cascade` is set; without it a node with children answers `has_children`).
 */
export function fakeMindmapBackend(options: Options = {}) {
	let nodes = [...(options.nodes ?? [])];
	let created = 0;
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
				};
				nodes = [...nodes, node];
				return Response.json(node);
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

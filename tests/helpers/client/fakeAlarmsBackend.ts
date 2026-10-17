import { alarmsApi, type AlarmOut } from "../../../client/src/plugins/alarms/api";
import { fakeWorkspaceBackend } from "./fakeWorkspaceBackend";

type Options = Omit<Parameters<typeof fakeWorkspaceBackend>[0] & object, "respond" | "extraApis"> & {
	alarms?: AlarmOut[];
	/** Answers a request itself; `undefined` lets the fake answer. */
	respond?: (request: { method: string; path: string; body?: unknown; query: URLSearchParams }) => Response | undefined;
};

/** The workspace fake plus the `alarms` API: it lists by project and `due_only` and echoes every write. */
export function fakeAlarmsBackend(options: Options = {}) {
	return fakeWorkspaceBackend({
		...options,
		extraApis: [{ id: "alarms", api: alarmsApi }],
		respond: (request) => {
			const custom = options.respond?.(request);
			if (custom) return custom;
			const { method, path, query } = request;
			if (!path.startsWith("alarms/")) return undefined;
			if (path === "alarms/alarms" && method === "GET") {
				const wanted = query.get("projects")?.split(",").filter(Boolean);
				const dueOnly = query.get("due_only") === "true";
				return Response.json(
					(options.alarms ?? []).filter((entry) => (!wanted || wanted.includes(entry.project_uid)) && (!dueOnly || entry.status === "Due")),
				);
			}
			const one = /^alarms\/alarms\/([^/]+)(?:\/(\w+))?$/.exec(path);
			const found = one ? options.alarms?.find((entry) => entry.uid === one[1]) : undefined;
			return Response.json({ ...(found ?? {}), ...(request.body as object), uid: one?.[1] ?? "new", version: (found?.version ?? 0) + 1 });
		},
	});
}

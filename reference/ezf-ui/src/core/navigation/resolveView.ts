import { hasSidebar, sidebarSlot } from "../plugins/contributions";
import type { PluginStatus } from "../plugins/types";
import { parseViewPath } from "./paths";
import type { NavEntry, SidebarEntry } from "./types";

export type ViewResolution =
	/** The path leads to a main route, or to an entry of its sidebar (`sidebarEntry`). */
	| { kind: "available"; entry: NavEntry; sidebarEntry?: SidebarEntry }
	/**
	 * "This page does not exist": unknown owner, or the owner has no view of this
	 * name. `host` names the main route if only an entry of its sidebar is
	 * missing: sidebar and header stay and only the content shows the notice.
	 */
	| { kind: "not-found"; log: boolean; host?: NavEntry }
	/** "Not available right now": the owner is switched off, failed or blocked; `host` as above. */
	| { kind: "unavailable"; log: boolean; host?: NavEntry };

interface ResolveViewInput {
	/** Status of every plugin of the build (`registry.statuses()`). */
	statuses: readonly PluginStatus[];
	/** The tabs of the active plugins and of the core. */
	entries: readonly NavEntry[];
	/** The entries of every sidebar of the active plugins and of the core, by slot. */
	sidebars?: ReadonlyMap<string, readonly SidebarEntry[]>;
}

type Missing = { kind: "not-found" | "unavailable"; log: boolean };

/** What an owner's state says about a view that is not there: switched off, failed or blocked, or unknown. */
function missing(ownerId: string, statuses: readonly PluginStatus[]): Missing | undefined {
	const status = statuses.find((candidate) => candidate.id === ownerId);
	if (status?.status === "disabled") return { kind: "unavailable", log: true };
	if (status?.status === "failed" || status?.status === "blocked") return { kind: "unavailable", log: false };
	if (ownerId !== "core" && !status) return { kind: "not-found", log: true };
	return undefined;
}

/**
 * Tells what a path leads to: the owner is the first part of the path, its
 * state comes from the registry. `log` says whether the case is reported at
 * info level with the called path; failed and blocked plugins were reported
 * at the start already. A path below a main route with a sidebar names the
 * owner and the name of an entry.
 */
export function resolveView(pathname: string, { statuses, entries, sidebars = new Map() }: ResolveViewInput): ViewResolution {
	const parsed = parseViewPath(pathname);
	if (!parsed) return { kind: "not-found", log: true };

	const { ownerId, name, rest } = parsed;
	const hostProblem = missing(ownerId, statuses);
	if (hostProblem) return hostProblem;

	const entry = entries.find((candidate) => candidate.ownerId === ownerId && candidate.name === name);
	if (!entry) return { kind: "not-found", log: true };
	if (rest.length === 0) return { kind: "available", entry };
	if (!hasSidebar(entry.contribution)) return { kind: "not-found", log: true };

	// An entry below a main route with a sidebar: the sidebar and the header of the host stay in every case.
	const [entryOwner, entryName] = rest;
	if (rest.length !== 2 || !entryOwner || !entryName) return { kind: "not-found", log: true, host: entry };
	const sidebarEntry = sidebars.get(sidebarSlot(ownerId, name!))?.find((candidate) => candidate.ownerId === entryOwner && candidate.name === entryName);
	if (sidebarEntry) return { kind: "available", entry, sidebarEntry };

	const problem = missing(entryOwner, statuses);
	return { ...(problem ?? { kind: "not-found", log: true }), host: entry };
}

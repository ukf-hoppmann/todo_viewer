import type { PluginStatus } from "../plugins/types";
import { parseViewPath } from "./paths";
import type { NavEntry } from "./types";

export type ViewResolution =
	/** The path leads to a main route. */
	| { kind: "available"; entry: NavEntry }
	/** "This page does not exist": unknown owner, or the owner has no view of this name. */
	| { kind: "not-found"; log: boolean }
	/** "Not available right now": the owner is switched off, failed or blocked. */
	| { kind: "unavailable"; log: boolean };

interface ResolveViewInput {
	/** Status of every plugin of the build (`registry.statuses()`). */
	statuses: readonly PluginStatus[];
	/** The tabs of the active plugins and of the core. */
	entries: readonly NavEntry[];
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
 * at the start already.
 */
export function resolveView(pathname: string, { statuses, entries }: ResolveViewInput): ViewResolution {
	const parsed = parseViewPath(pathname);
	if (!parsed) return { kind: "not-found", log: true };

	const { ownerId, name, rest } = parsed;
	const problem = missing(ownerId, statuses);
	if (problem) return problem;

	const entry = entries.find((candidate) => candidate.ownerId === ownerId && candidate.name === name);
	if (!entry || rest.length > 0) return { kind: "not-found", log: true };
	return { kind: "available", entry };
}

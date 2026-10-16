import { logging } from "../logging/logging";
import type { Logger } from "../logging/types";
import type { StorageLike } from "./types";

/** Key in the `sessionStorage` of the browser tab: it survives the round trip through the login, and only this tab sees it. */
export const returnToKey = "core.return-to";

/** The backend login keeps its status cookie for 10 minutes; a remembered address does not outlive it by default. */
const defaultMaxAgeMinutes = 10;

/** The `sessionStorage` of the tab, or nothing where the browser does not give access to it. */
export function tabStorage(): StorageLike | undefined {
	try {
		return globalThis.sessionStorage;
	} catch {
		return undefined;
	}
}

/** Remembers the address (path, query, fragment) the user wanted to open; `/` is not worth remembering. */
export function saveReturnTo(storage: StorageLike | undefined, path: string, now: number): void {
	if (path === "/") return;
	try {
		storage?.setItem(returnToKey, JSON.stringify({ path, savedAt: now }));
	} catch {
		// A tab without storage simply does not return; the login itself works.
	}
}

/** Forgets the remembered address, e.g. because the login did not start. */
export function clearReturnTo(storage: StorageLike | undefined): void {
	try {
		storage?.removeItem(returnToKey);
	} catch {
		// See `saveReturnTo`.
	}
}

interface ConsumeReturnToOptions {
	/** The `sessionStorage` of the tab by default. */
	storage?: StorageLike;
	now?: () => number;
	/** `api.returnToMaxAgeMinutes`; 10 if missing. */
	maxAgeMinutes?: number;
	/** Whether the path (without query and fragment) leads to a view that exists and can be shown. */
	isAvailable: (pathname: string) => boolean;
	/** The logger of `core` by default. */
	logger?: Logger;
}

/** One local path only: a single `/` at the start, no scheme, no other host, no backslash tricks. */
function isLocalPath(path: string): boolean {
	return path.startsWith("/") && !path.startsWith("//") && !path.startsWith("/\\");
}

function readEntry(raw: string): { path: string; savedAt: number } | undefined {
	try {
		const entry: unknown = JSON.parse(raw);
		if (typeof entry !== "object" || entry === null) return undefined;
		const { path, savedAt } = entry as Record<string, unknown>;
		return typeof path === "string" && typeof savedAt === "number" ? { path, savedAt } : undefined;
	} catch {
		return undefined;
	}
}

/**
 * Reads the address remembered before the login once and deletes it at once.
 * It is returned only if it is young enough, is a local path, and leads to a
 * view that is available; otherwise nothing is returned and an `info` entry
 * (action `return-to`, reason in `data`) says why.
 */
export function consumeReturnTo({
	storage = tabStorage(),
	now = Date.now,
	maxAgeMinutes = defaultMaxAgeMinutes,
	isAvailable,
	logger = logging.forOrigin("core"),
}: ConsumeReturnToOptions): string | undefined {
	let raw: string | null;
	try {
		raw = storage?.getItem(returnToKey) ?? null;
	} catch {
		return undefined;
	}
	if (raw === null) return undefined;
	clearReturnTo(storage);

	const drop = (reason: string, data: Record<string, unknown> = {}) => {
		logger.info({ action: "return-to", message: `the remembered address is not used: ${reason}`, data: { reason, ...data } });
		return undefined;
	};

	const entry = readEntry(raw);
	if (!entry) return drop("unreadable");
	if (now() - entry.savedAt > maxAgeMinutes * 60_000) return drop("expired", { path: entry.path });
	if (!isLocalPath(entry.path)) return drop("invalid-path", { path: entry.path });

	const pathname = entry.path.split(/[?#]/, 1)[0] ?? "";
	if (!isAvailable(pathname)) return drop("not-available", { path: entry.path });
	return entry.path;
}

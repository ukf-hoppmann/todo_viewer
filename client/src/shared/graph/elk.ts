import type { ELK } from "elkjs/lib/elk.bundled.js";

// ELK is large: it is imported when the first layout is asked for, not with the page that needs it.
let elkPromise: Promise<ELK> | null = null;

/** The one ELK instance of the app, loaded on first use (its own chunk in the build). */
export function loadElk(): Promise<ELK> {
	elkPromise ??= import("elkjs/lib/elk.bundled.js").then(({ default: ElkConstructor }) => new ElkConstructor());
	return elkPromise;
}

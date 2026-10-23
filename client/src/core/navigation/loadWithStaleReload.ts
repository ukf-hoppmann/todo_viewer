const RELOADED_KEY = "stale-chunk-reloaded";

/** Browsers word a failed `import()` differently; all of them name the module or the dynamic import. */
const CHUNK_LOAD_ERROR = /dynamically imported module|Importing a module script failed|Failed to fetch dynamically/i;

/**
 * Wraps a lazy import. A page opened before a new build asks for chunks that no longer exist; the page is
 * reloaded once so that it gets the current build. A second failure within the same tab session is a real
 * one and is passed on, so there is no reload loop.
 */
export function loadWithStaleReload<T>(
	load: () => Promise<T>,
	reload: () => void = () => window.location.reload(),
): () => Promise<T> {
	return async () => {
		try {
			return await load();
		} catch (error) {
			if (!(error instanceof Error) || !CHUNK_LOAD_ERROR.test(error.message)) throw error;
			if (!markReloaded()) throw error;
			reload();
			// The page is going away; keep the lazy component pending instead of flashing the error.
			return new Promise<T>(() => {});
		}
	};
}

/** True when this call set the guard; false when it was set before or session storage is unavailable. */
function markReloaded(): boolean {
	try {
		if (sessionStorage.getItem(RELOADED_KEY)) return false;
		sessionStorage.setItem(RELOADED_KEY, "1");
		return true;
	} catch {
		// Better to show the error than to risk a reload loop.
		return false;
	}
}

/** Called once a page loaded fine, so that the next new build may reload again. */
export function clearStaleReloadGuard(): void {
	try {
		sessionStorage.removeItem(RELOADED_KEY);
	} catch {
		// Nothing to clear.
	}
}

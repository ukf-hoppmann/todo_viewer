/** `unknown` until the check at the start; no user data is kept (the backend does not hand out any). */
export type AuthState = "unknown" | "authenticated" | "unauthenticated";

/** The part of `Storage` the core uses; the `sessionStorage` of the tab in the browser. */
export type StorageLike = Pick<Storage, "getItem" | "setItem" | "removeItem">;

/** The address bar as the core needs it: where the tab is now, and the two ways to leave. */
export interface BrowserLocation {
	/** Path, query and fragment of the current address. */
	current(): string;
	/** Leaves the page; the way back leads here again. */
	assign(url: string): void;
	/** Leaves the page without a way back. */
	replace(url: string): void;
}

/** How long `check` waits for the answer; without a value it waits as long as the browser does. */
export interface CheckOptions {
	timeoutMs?: number;
}

/** The login of the application. Lives outside the store because it is needed before the plugins. */
export interface Auth {
	getState(): AuthState;
	/** For `useSyncExternalStore`; returns the function that removes the listener. */
	subscribe(listener: () => void): () => void;
	/**
	 * Asks the backend. Throws `AuthCheckError` if the answer cannot be used;
	 * with `timeoutMs`, no answer within that time counts as `unreachable`.
	 */
	check(options?: CheckOptions): Promise<AuthState>;
	/**
	 * Remembers the current address and sends the browser to the login of the
	 * backend. A failure is reported to the user (`reportError`); nothing is thrown.
	 */
	login(): Promise<void>;
	/**
	 * Logs out like `src_old` and reloads the page through the logout address,
	 * so that nothing of the user stays in memory. A failure is reported to the
	 * user; nothing is thrown.
	 */
	logout(): Promise<void>;
	/** A request got 401 or 407: the login is over. Many reports act like one. */
	unauthorized(): void;
}

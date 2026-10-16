import type { Banners } from "../banners/types";

/** What the application does when the backend does not answer. */
export interface ConnectionSettings {
	/** How many failed tests in a row until the warning appears. */
	failuresBeforeWarning: number;
	/** Seconds between the end of one test and the start of the next; also how long a test waits for an answer. */
	retryIntervalSeconds: number;
}

export const defaultConnectionSettings: ConnectionSettings = {
	failuresBeforeWarning: 1,
	retryIntervalSeconds: 5,
};

/** The backend did not answer the connection test. */
export class BackendUnreachableError extends Error {
	constructor(cause?: unknown) {
		super("the backend did not answer", { cause });
		this.name = "BackendUnreachableError";
	}
}

export interface ConnectionMonitorOptions {
	/** Asks the backend (`GET /api/core/health`); rejects with `BackendUnreachableError` if it does not answer in time. */
	check: (options: { timeoutMs: number }) => Promise<void>;
	banners: Banners;
	/** Missing settings take their defaults. */
	settings?: Partial<ConnectionSettings>;
	/** Runs `run` after `ms` and returns the function that cancels it; `setTimeout` by default. */
	schedule?: (run: () => void, ms: number) => () => void;
	/** Called when the backend answers again after a failure (the application reloads its data then). */
	onRecovered?: () => void;
}

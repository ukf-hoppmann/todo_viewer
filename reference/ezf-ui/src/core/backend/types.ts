import type { Banners } from "../banners/types";
import type { Auth } from "../auth/types";

/** What the application does when the backend does not answer; the section `api.connection` of the app config. */
export interface ConnectionSettings {
	/** How many failed tests in a row until the warning appears. */
	failuresBeforeWarning: number;
	/** Seconds between the end of one test and the start of the next; also how long a test waits for an answer. */
	retryIntervalSeconds: number;
	/** Seconds without a successful test, counted from the first failed one, until the application logs out locally. */
	logoutAfterSeconds: number;
}

export const defaultConnectionSettings: ConnectionSettings = {
	failuresBeforeWarning: 1,
	retryIntervalSeconds: 5,
	logoutAfterSeconds: 300,
};

export interface ConnectionMonitorOptions {
	auth: Pick<Auth, "check" | "unauthorized">;
	banners: Banners;
	/** Missing settings take their defaults. */
	settings?: Partial<ConnectionSettings>;
	/** The clock in milliseconds; `Date.now` by default. */
	now?: () => number;
	/** Runs `run` after `ms` and returns the function that cancels it; `setTimeout` by default. */
	schedule?: (run: () => void, ms: number) => () => void;
}

import { AuthCheckError } from "../auth/AuthCheckError";
import type { BannerHandle, BannerRequest } from "../banners/types";
import type { BackendFailureKind } from "./classifyFailure";
import { defaultConnectionSettings, type ConnectionMonitorOptions, type ConnectionSettings } from "./types";

export interface ConnectionMonitor {
	/**
	 * A request or the log output failed for good. `unauthorized` goes to the
	 * login; `unreachable` starts the connection test, unless one is running.
	 */
	report(kind: BackendFailureKind): void;
	/**
	 * At the start: asks the backend until it answers (200, 401, or 407), shows
	 * the warning meanwhile, and returns afterwards. The state of the login is set
	 * by then. Never gives up.
	 */
	waitForBackend(): Promise<void>;
}

/** From this many seconds on the time until the logout is named in minutes. */
const MINUTES_FROM_SECONDS = 120;

const defaultSchedule = (run: () => void, ms: number) => {
	const timer = setTimeout(run, ms);
	return () => clearTimeout(timer);
};

/**
 * The one place that reacts when the backend does not answer. After a
 * reported failure it tests the connection with the login check (never two
 * tests at once), warns the user, recovers by itself, and logs out locally
 * when the test does not work for long. Requests are not repeated here.
 */
export function createConnectionMonitor({
	auth,
	banners,
	settings,
	now = Date.now,
	schedule = defaultSchedule,
}: ConnectionMonitorOptions): ConnectionMonitor {
	const { failuresBeforeWarning, retryIntervalSeconds, logoutAfterSeconds }: ConnectionSettings = {
		...defaultConnectionSettings,
		...settings,
	};
	const intervalMs = retryIntervalSeconds * 1000;

	/** The test is running or waits for its next turn. */
	let active = false;
	/** Failed tests in a row. */
	let attempts = 0;
	/** When the first of these failed tests began; the logout counts from here. */
	let failingSince = 0;
	/** When the next test should begin, to notice a jump in time. */
	let plannedAt = 0;
	let warning: BannerHandle | undefined;

	const test = () => auth.check({ timeoutMs: intervalMs });

	const durationParams = () =>
		logoutAfterSeconds >= MINUTES_FROM_SECONDS
			? { key: "connection.messageMinutes", params: { attempts, count: Math.round(logoutAfterSeconds / 60) } }
			: { key: "connection.messageSeconds", params: { attempts, count: logoutAfterSeconds } };

	/** Shows the warning from `failuresBeforeWarning` failed tests on, and raises its number afterwards. */
	const warn = (message: () => BannerRequest["message"]) => {
		if (attempts < failuresBeforeWarning) return;
		if (warning) warning.update({ message: message() });
		else warning = banners.show({ severity: "warning", dismissible: false, title: { key: "connection.title" }, message: message() });
	};

	const forget = () => {
		attempts = 0;
		warning?.close();
		warning = undefined;
	};

	/** One test during operation; schedules the next one if the backend stays away. */
	const run = async (): Promise<void> => {
		const startedAt = now();
		// The computer slept or the tab was frozen: the time without a connection is not known.
		if (attempts > 0 && startedAt - plannedAt > 2 * intervalMs) failingSince = startedAt;
		let failed = false;
		try {
			await test();
		} catch (error) {
			if (!(error instanceof AuthCheckError)) {
				active = false;
				throw error;
			}
			failed = true;
		}

		if (!failed) {
			// 200: the backend is there. 401 or 407: the check has turned to the login page.
			active = false;
			forget();
			return;
		}

		if (attempts === 0) failingSince = startedAt;
		attempts++;
		warn(durationParams);

		if (now() - failingSince >= logoutAfterSeconds * 1000) {
			active = false;
			forget();
			// The logout clears all banners; the notice is shown afterwards, so that it stays.
			auth.unauthorized();
			banners.show({ severity: "info", message: { key: "connection.loggedOut" } });
			return;
		}

		plannedAt = now() + intervalMs;
		schedule(() => void run(), intervalMs);
	};

	return {
		report(kind) {
			if (kind === "unauthorized") {
				auth.unauthorized();
				return;
			}
			if (active) return;
			active = true;
			void run();
		},

		async waitForBackend() {
			let failedTests = 0;
			let notice: BannerHandle | undefined;
			for (;;) {
				try {
					await test();
					notice?.close();
					return;
				} catch (error) {
					if (!(error instanceof AuthCheckError)) throw error;
				}
				failedTests++;
				if (failedTests >= failuresBeforeWarning) {
					const message = { key: "connection.startMessage", params: { attempts: failedTests } };
					if (notice) notice.update({ message });
					else notice = banners.show({ severity: "warning", dismissible: false, title: { key: "connection.title" }, message });
				}
				await new Promise<void>((resolve) => schedule(resolve, intervalMs));
			}
		},
	};
}

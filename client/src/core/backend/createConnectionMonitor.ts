import type { BannerHandle } from "../banners/types";
import type { BackendFailureKind } from "./classifyFailure";
import { BackendUnreachableError, defaultConnectionSettings, type ConnectionMonitorOptions, type ConnectionSettings } from "./types";

export interface ConnectionMonitor {
	/** A request failed for good: starts the connection test, unless one is running. */
	report(kind: BackendFailureKind): void;
	/** At the start: asks the backend until it answers, shows the warning meanwhile, and returns afterwards. Never gives up. */
	waitForBackend(): Promise<void>;
}

const defaultSchedule = (run: () => void, ms: number) => {
	const timer = setTimeout(run, ms);
	return () => clearTimeout(timer);
};

/**
 * The one place that reacts when the backend does not answer. After a reported
 * failure it tests the connection (never two tests at once), warns the user,
 * and recovers by itself. There is no login, so nothing is logged out.
 * Requests are not repeated here.
 */
export function createConnectionMonitor({
	check,
	banners,
	settings,
	schedule = defaultSchedule,
	onRecovered,
}: ConnectionMonitorOptions): ConnectionMonitor {
	const { failuresBeforeWarning, retryIntervalSeconds }: ConnectionSettings = { ...defaultConnectionSettings, ...settings };
	const intervalMs = retryIntervalSeconds * 1000;

	let active = false;
	let attempts = 0;
	let warning: BannerHandle | undefined;

	const message = () => ({ key: "connection.message", params: { attempts } });

	const warn = () => {
		if (attempts < failuresBeforeWarning) return;
		if (warning) warning.update({ message: message() });
		else warning = banners.show({ severity: "warning", dismissible: false, title: { key: "connection.title" }, message: message() });
	};

	const run = async (): Promise<void> => {
		try {
			await check({ timeoutMs: intervalMs });
		} catch (error) {
			if (!(error instanceof BackendUnreachableError)) {
				active = false;
				throw error;
			}
			attempts++;
			warn();
			schedule(() => void run(), intervalMs);
			return;
		}
		active = false;
		attempts = 0;
		warning?.close();
		warning = undefined;
		onRecovered?.();
	};

	return {
		report() {
			if (active) return;
			active = true;
			void run();
		},

		async waitForBackend() {
			let failedTests = 0;
			let notice: BannerHandle | undefined;
			for (;;) {
				try {
					await check({ timeoutMs: intervalMs });
					notice?.close();
					return;
				} catch (error) {
					if (!(error instanceof BackendUnreachableError)) throw error;
				}
				failedTests++;
				if (failedTests >= failuresBeforeWarning) {
					const startMessage = { key: "connection.startMessage", params: { attempts: failedTests } };
					if (notice) notice.update({ message: startMessage });
					else notice = banners.show({ severity: "warning", dismissible: false, title: { key: "connection.title" }, message: startMessage });
				}
				await new Promise<void>((resolve) => schedule(resolve, intervalMs));
			}
		},
	};
}

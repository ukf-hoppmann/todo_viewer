import type { Logging } from "../logging/types";
import type { Modals } from "../modals/types";
import { buildDetails } from "./buildDetails";
import type { Errors, ReportError, ReportErrorInput } from "./types";

interface ErrorsDependencies {
	logging: Logging;
	modals: Modals;
}

/**
 * Connects logging and dialogs for errors the backend knows nothing about:
 * one log entry and one alert per call. Logging and dialogs know nothing of
 * each other; this is the only place that joins them.
 */
export function createErrors({ logging, modals }: ErrorsDependencies): Errors {
	const reporters = new Map<string, ReportError>();

	function createReporter(origin: string): ReportError {
		const logger = logging.forOrigin(origin);

		return ({ userMessage, title, severity = "error", message, ...fields }: ReportErrorInput) => {
			const key = typeof userMessage === "string" ? userMessage : userMessage.key;
			const log = severity === "warning" ? logger.warn : logger.error;
			const entry = log({ ...fields, userMessage: key, message: message ?? key });

			const showStack = logging.effectiveLevel("console", origin) === "debug";
			return modals.alert({
				severity,
				title,
				message: userMessage,
				details: buildDetails(entry, { showStack }),
			});
		};
	}

	return {
		forOrigin(origin) {
			let reporter = reporters.get(origin);
			if (!reporter) {
				reporter = createReporter(origin);
				reporters.set(origin, reporter);
			}
			return reporter;
		},
	};
}

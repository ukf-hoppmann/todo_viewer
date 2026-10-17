import type { LogEntry, Logging } from "../logging/types";
import type { Errors } from "./types";

interface UnhandledErrorsDependencies {
	errors: Errors;
	logging: Logging;
}

/** Where and how an unhandled error was found. */
export interface UnhandledErrorInfo {
	/** `core` or a plugin id; `core` without it. */
	origin?: string;
	/** Which way caught the error, e.g. `render`, `unhandled-error`, `unhandled-rejection`. */
	action: string;
	data?: unknown;
}

export interface UnhandledErrors {
	/** Logs the error and shows one hint to the user, unless it was reported before or a hint is still open. */
	report(error: unknown, info: UnhandledErrorInfo): void;
	/** Only logs a warning: for things the user does not notice. */
	warn(error: unknown, info: UnhandledErrorInfo): void;
	/**
	 * For a crash after which no dialog can be shown any more: logs as error
	 * without a hint and returns the entry, so that its ids can be shown instead.
	 */
	fatal(error: unknown, info: UnhandledErrorInfo): LogEntry;
}

const userMessage = { key: "errors.unexpected" };

/**
 * The one place where errors nobody handled are reported, whichever way they
 * were caught. It makes sure that an error appears once and that a burst of
 * errors does not produce a burst of dialogs.
 */
export function createUnhandledErrors({ errors, logging }: UnhandledErrorsDependencies): UnhandledErrors {
	// Only objects can be remembered; a rejected string is reported each time.
	const reported = new WeakSet<object>();
	let hintOpen = false;

	return {
		report(error, { origin = "core", action, data }) {
			if (typeof error === "object" && error !== null) {
				if (reported.has(error)) return;
				reported.add(error);
			}

			if (hintOpen) {
				logging.forOrigin(origin).error({ action, error, data, message: userMessage.key });
				return;
			}

			hintOpen = true;
			void errors
				.forOrigin(origin)({ userMessage, action, error, data })
				.finally(() => {
					hintOpen = false;
				});
		},

		warn(error, { origin = "core", action, data }) {
			logging.forOrigin(origin).warn({ action, error, data, message: userMessage.key });
		},

		fatal(error, { origin = "core", action, data }) {
			if (typeof error === "object" && error !== null) reported.add(error);
			return logging.forOrigin(origin).error({ action, error, data, message: userMessage.key });
		},
	};
}

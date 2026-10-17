import type { UnhandledErrors } from "./createUnhandledErrors";
import { unhandledErrors } from "./unhandledErrors";

/**
 * Reports errors in event handlers and timers (`error`) and rejected promises
 * without a `catch` (`unhandledrejection`). The plugin cannot be determined
 * here, so the origin is `core`; the stack trace in the log shows the place.
 * Returns a function that removes the listeners again.
 */
export function installGlobalErrorHandlers(unhandled: UnhandledErrors = unhandledErrors): () => void {
	const onError = (event: ErrorEvent) => {
		unhandled.report(event.error, {
			action: "unhandled-error",
			// Without an error object (e.g. a cross-origin script) the event is all there is.
			data: event.error
				? undefined
				: { message: event.message, filename: event.filename, lineno: event.lineno, colno: event.colno },
		});
	};
	const onRejection = (event: PromiseRejectionEvent) => {
		unhandled.report(event.reason, { action: "unhandled-rejection" });
	};

	window.addEventListener("error", onError);
	window.addEventListener("unhandledrejection", onRejection);
	return () => {
		window.removeEventListener("error", onError);
		window.removeEventListener("unhandledrejection", onRejection);
	};
}

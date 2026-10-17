import type { LogInput } from "../logging/types";
import type { Text } from "../modals/text";

export interface ReportErrorInput extends Pick<LogInput, "element" | "action" | "message" | "error" | "data"> {
	/** What the user reads: an i18n key or a finished text. */
	userMessage: Text;
	/** Without it the default title of the severity applies. */
	title?: Text;
	/** Default `error`. */
	severity?: "error" | "warning";
}

/** Logs an error and shows it to the user; resolves when the user closes the alert. */
export type ReportError = (input: ReportErrorInput) => Promise<void>;

export interface Errors {
	/** `reportError` with a fixed origin; the same origin returns the same function. */
	forOrigin(origin: string): ReportError;
}

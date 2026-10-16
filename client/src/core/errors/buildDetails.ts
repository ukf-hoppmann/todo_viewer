import type { LogEntry } from "../logging/types";
import { toLoggable } from "../logging/toLoggable";
import type { DetailRow } from "../modals/types";

interface BuildDetailsOptions {
	/** Whether the stack trace is part of the details. */
	showStack: boolean;
}

function pad(value: number): string {
	return String(value).padStart(2, "0");
}

/** Local time to the second, independent of the language: `YYYY-MM-DD HH:mm:ss`. */
function formatTime(iso: string): string {
	const time = new Date(iso);
	return `${time.getFullYear()}-${pad(time.getMonth() + 1)}-${pad(time.getDate())} ${pad(time.getHours())}:${pad(time.getMinutes())}:${pad(time.getSeconds())}`;
}

function describeError(error: unknown): string {
	if (error instanceof Error) return `${error.name}: ${error.message}`;
	if (typeof error === "object" && error !== null) return JSON.stringify(toLoggable(error));
	return String(error);
}

/**
 * Detail lines of the alert for a reported error. They show exactly the time,
 * error id and session id of the log entry, so that support can find it.
 * Lines without a value are left out.
 */
export function buildDetails(entry: LogEntry, { showStack }: BuildDetailsOptions): DetailRow[] {
	const rows: DetailRow[] = [
		{ label: { key: "reportError.details.time" }, value: formatTime(entry.time) },
		{ label: { key: "reportError.details.errorId" }, value: entry.id },
		{ label: { key: "reportError.details.sessionId" }, value: entry.sessionId },
	];
	if (entry.error !== undefined && entry.error !== null) {
		rows.push({ label: { key: "reportError.details.error" }, value: describeError(entry.error) });
	}
	if (showStack && entry.error instanceof Error && entry.error.stack) {
		rows.push({ label: { key: "reportError.details.stack" }, value: entry.error.stack });
	}
	return rows.filter((row) => row.value !== "");
}

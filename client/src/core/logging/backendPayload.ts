import type { LogEntry } from "./types";

/** Fields taken over unchanged. */
const plainFields = ["id", "time", "level", "origin", "route", "element", "action", "message"] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === "object" && value !== null && !Array.isArray(value);
}

/**
 * Brings a converted `error` into the form of the server: `name`, `message`, `stack`, `cause` (the same form
 * again). Anything that is no error becomes `NonError` with the value as text. Missing parts are left out.
 */
function toBackendError(converted: unknown): Record<string, unknown> {
	if (!isRecord(converted) || typeof converted.name !== "string" || !("message" in converted)) {
		return { name: "NonError", message: typeof converted === "string" ? converted : (JSON.stringify(converted) ?? String(converted)) };
	}
	const result: Record<string, unknown> = { name: converted.name, message: converted.message };
	if (converted.stack !== undefined) result.stack = converted.stack;
	if (converted.cause !== undefined) result.cause = toBackendError(converted.cause);
	return result;
}

/**
 * The body of one request to `POST /api/core/client-log` (the operation `client_log` of the core). `error` and
 * `data` are converted with `toLoggable` of the logging, so that its limits apply. Empty fields are left out.
 */
export function toBackendPayload(entry: LogEntry, toLoggable: (value: unknown) => unknown): Record<string, unknown> {
	const payload: Record<string, unknown> = {};
	for (const field of plainFields) {
		const value = entry[field];
		if (value !== undefined && value !== "") payload[field] = value;
	}
	payload.session_id = entry.sessionId;
	if (entry.userMessage) payload.user_message = entry.userMessage;
	if (entry.error !== undefined) payload.error = toBackendError(toLoggable(entry.error));
	if (entry.data !== undefined) {
		const data = toLoggable(entry.data);
		if (data !== undefined) payload.data = data;
	}
	return payload;
}

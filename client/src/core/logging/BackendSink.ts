import { toBackendPayload } from "./backendPayload";
import type { LogEntry, LogSink, SinkContext } from "./types";

/** Browsers refuse `keepalive` requests above 64 kB; larger entries go without it. */
const KEEPALIVE_MAX_BYTES = 60_000;

export interface BackendSinkOptions {
	/** Address of the operation `client_log`, e.g. `/api/core/client-log`. */
	url: string;
	/** The global `fetch` by default. */
	fetch?: (url: string, init: RequestInit) => Promise<Response>;
}

/**
 * Sends each entry on its own to the server, which writes it into `viewer.log`. `write` returns at once and
 * never throws; sending runs in the background, once per entry (a server that does not answer is the business of
 * the connection monitor, not of the log). Failures go to `console.warn`, never through the logging, so that
 * failed sending creates no new entries.
 */
export class BackendSink implements LogSink {
	readonly name = "backend";

	constructor(private readonly options: BackendSinkOptions) {}

	write(entry: LogEntry, context: SinkContext): void {
		try {
			const body = JSON.stringify(toBackendPayload(entry, context.toLoggable));
			const keepalive = new TextEncoder().encode(body).length <= KEEPALIVE_MAX_BYTES;
			const send = this.options.fetch ?? globalThis.fetch.bind(globalThis);
			void send(this.options.url, { method: "POST", keepalive, headers: { "Content-Type": "application/json" }, body })
				.then((response) => {
					if (!response.ok) warn(entry, `HTTP ${response.status}`);
				})
				.catch((error: unknown) => warn(entry, String(error)));
		} catch (error) {
			warn(entry, String(error));
		}
	}
}

function warn(entry: LogEntry, reason: string): void {
	console.warn(`Log entry ${entry.id} not sent to the server (${reason})`);
}

import { failureKindOfStatus, type BackendFailureKind } from "../backend/classifyFailure";
import { toBackendPayload } from "./backendPayload";
import type { LogEntry, LogSink, SinkContext } from "./types";

/** Delays before the second and third attempt. */
const RETRY_DELAYS_MS = [1_000, 3_000];

/** Browsers refuse `keepalive` requests above 64 kB; larger entries go without it. */
const KEEPALIVE_MAX_BYTES = 60_000;

export interface BackendSinkOptions {
	/** Address of `persistLogFromUi`. */
	url: string;
	/** `false` before the login: nothing is sent, the entry is dropped for the backend. */
	canSend: () => boolean;
	/** A request finally failed; both kinds go to the central handling of the connection loss (`createConnectionMonitor`). */
	onFailure: (kind: BackendFailureKind) => void;
	/** The global `fetch` by default. */
	fetch?: (url: string, init: RequestInit) => Promise<Response>;
}

type Outcome = { done: true } | { done: false; retry: boolean; kind?: BackendFailureKind; reason: string };

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Sends each entry on its own to the backend (format of STORY-009). `write`
 * returns at once and never throws; sending runs in the background. Nothing
 * is kept besides the running attempts. Failures go to `console.warn`, never
 * through the logging, so that failed sending creates no new entries.
 */
export class BackendSink implements LogSink {
	readonly name = "backend";

	constructor(private readonly options: BackendSinkOptions) {}

	write(entry: LogEntry, context: SinkContext): void {
		try {
			if (!this.options.canSend()) return;
			const body = JSON.stringify(toBackendPayload(entry, context.toLoggable));
			void this.send(entry, body).catch((error: unknown) => warn(entry, `sending failed: ${String(error)}`));
		} catch (error) {
			warn(entry, `sending failed: ${String(error)}`);
		}
	}

	private async send(entry: LogEntry, body: string): Promise<void> {
		const keepalive = new TextEncoder().encode(body).length <= KEEPALIVE_MAX_BYTES;
		let outcome = await this.attempt(body, keepalive);
		for (const delay of RETRY_DELAYS_MS) {
			if (outcome.done || !outcome.retry) break;
			await wait(delay);
			outcome = await this.attempt(body, keepalive);
		}
		if (outcome.done) return;

		warn(entry, outcome.reason);
		if (outcome.kind) this.options.onFailure(outcome.kind);
	}

	private async attempt(body: string, keepalive: boolean): Promise<Outcome> {
		let response: Response;
		try {
			const fetch = this.options.fetch ?? globalThis.fetch;
			response = await fetch(this.options.url, {
				method: "POST",
				credentials: "include",
				keepalive,
				headers: { "Content-Type": "application/json" },
				body,
			});
		} catch (error) {
			return { done: false, retry: true, kind: failureKindOfStatus("no-response"), reason: `network error: ${String(error)}` };
		}

		const { status } = response;
		if (status >= 200 && status < 300) return { done: true };
		const kind = failureKindOfStatus(status);
		if (kind) return { done: false, retry: kind === "unreachable", kind, reason: `HTTP ${status}` };
		// Other client errors: the entry is wrong for the backend; the answer says why.
		const text = await response.text().catch(() => "");
		return { done: false, retry: false, reason: `HTTP ${status}${text ? `: ${text}` : ""}` };
	}
}

function warn(entry: LogEntry, reason: string): void {
	console.warn(`Log entry ${entry.id} not sent to the backend (${reason})`);
}

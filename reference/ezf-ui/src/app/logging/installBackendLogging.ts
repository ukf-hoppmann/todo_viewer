import { BackendSink, logging as defaultLogging, type BackendFailureKind, type BackendSinkOptions, type Logging } from "../../core";
import { mockLogBackend } from "./mockLogBackend";

interface InstallBackendLoggingOptions {
	logging?: Logging;
	/** Until the backend takes the new format (STORY-009): the mock that checks it. */
	fetch?: BackendSinkOptions["fetch"];
}

export interface BackendConnection {
	/** The backend address (`api.url`); entries go to `<url>/persistLogFromUi`. */
	url: string;
	/** Whether the user is logged in right now; entries are sent only then. */
	canSend: () => boolean;
	/** An entry finally failed to reach the backend (after the output's own attempts): hand it to the central handling of the connection loss. */
	onFailure: (kind: BackendFailureKind) => void;
}

export interface BackendLogging {
	/** From now on entries go to the backend, while `canSend` says yes. */
	connect(connection: BackendConnection): void;
}

/**
 * Registers the output `backend` once at the start, before anything else, so
 * that every entry passes it; it is never removed. Nothing is sent until
 * `connect` was called (the address comes from the app config) and the user is
 * logged in, also not entries remembered from before. A backend that cannot
 * be reached is reported to the central handling of the connection loss
 * (`createConnectionMonitor`, wired by `startApp`), like a failed request.
 */
export function installBackendLogging({
	logging = defaultLogging,
	fetch = mockLogBackend,
}: InstallBackendLoggingOptions = {}): BackendLogging {
	let connection: BackendConnection | undefined;
	const sink = new BackendSink({
		// Read at each request, so the address set by `connect` applies.
		get url() {
			return connection ? `${connection.url}/persistLogFromUi` : "";
		},
		canSend: () => connection?.canSend() ?? false,
		onFailure: (kind) => connection?.onFailure(kind),
		fetch,
	});
	logging.addSink(sink, { level: "warn" });

	return {
		connect(next) {
			connection = next;
		},
	};
}

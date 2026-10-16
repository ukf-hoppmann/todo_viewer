/** The part of `EventSource` the stream uses; tests give a fake. */
export interface EventSourceLike {
	addEventListener(type: string, listener: (event: MessageEvent<string>) => void): void;
	close(): void;
}

export interface EventStreamOptions {
	/** The address of the event stream, `/api/core/events`. */
	url: string;
	/** The topics to listen for; read at each (re)connection, so late handlers are included. */
	topics: () => readonly string[];
	/** A server event arrived. */
	onEvent: (topic: string, payload: unknown) => void;
	/** The stream is back after an interruption: events may have been missed, data must be reloaded. */
	onReconnected: () => void;
	/** For warnings, e.g. an unreadable payload. */
	onProblem?: (message: string, error?: unknown) => void;
	createSource?: (url: string) => EventSourceLike;
	/** Waits `ms`, then runs `run`; returns the function that cancels it. */
	schedule?: (run: () => void, ms: number) => () => void;
	/** Wait before the first retry and the highest wait, in milliseconds; each retry doubles the wait. */
	backoff?: { initialMs: number; maxMs: number };
}

export interface EventStream {
	start(): void;
	stop(): void;
}

const defaultSchedule = (run: () => void, ms: number) => {
	const timer = setTimeout(run, ms);
	return () => clearTimeout(timer);
};

/**
 * The one connection from the backend to the frontend (`GET /api/core/events`, Server-Sent Events). The
 * browser's own reconnect does not help when the server answers with an error or closes the stream, so the
 * stream is closed on every error and opened again after a growing wait. After an interruption the first
 * successful connection reports `onReconnected`: events are not guaranteed, so the plugins reload.
 */
export function createEventStream({
	url,
	topics,
	onEvent,
	onReconnected,
	onProblem,
	createSource = (address) => new EventSource(address),
	schedule = defaultSchedule,
	backoff = { initialMs: 1_000, maxMs: 30_000 },
}: EventStreamOptions): EventStream {
	let source: EventSourceLike | undefined;
	let cancelRetry: (() => void) | undefined;
	let wait = backoff.initialMs;
	let interrupted = false;
	let running = false;

	const open = () => {
		const current = createSource(url);
		source = current;
		const live = () => source === current;

		current.addEventListener("open", () => {
			if (!live()) return;
			wait = backoff.initialMs;
			if (interrupted) {
				interrupted = false;
				onReconnected();
			}
		});
		current.addEventListener("error", () => {
			if (!live()) return;
			current.close();
			source = undefined;
			interrupted = true;
			cancelRetry = schedule(() => {
				cancelRetry = undefined;
				if (running) open();
			}, wait);
			wait = Math.min(wait * 2, backoff.maxMs);
		});
		for (const topic of new Set(topics())) {
			current.addEventListener(topic, (event) => {
				if (!live()) return;
				let payload: unknown;
				try {
					payload = event.data === "" ? {} : JSON.parse(event.data);
				} catch (error) {
					onProblem?.(`the event '${topic}' has no readable payload`, error);
					return;
				}
				onEvent(topic, payload);
			});
		}
	};

	return {
		start() {
			if (running) return;
			running = true;
			open();
		},
		stop() {
			running = false;
			cancelRetry?.();
			cancelRetry = undefined;
			source?.close();
			source = undefined;
		},
	};
}

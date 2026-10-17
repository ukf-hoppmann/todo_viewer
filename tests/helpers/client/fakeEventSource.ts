import type { EventSourceLike } from "../../../client/src/core/events/createEventStream";

type Listener = (event: MessageEvent<string>) => void;

/** An `EventSource` the test drives by hand: it opens, fails and delivers events when the test says so. */
export class FakeEventSource implements EventSourceLike {
	static instances: FakeEventSource[] = [];
	static reset() {
		FakeEventSource.instances = [];
	}
	static get last(): FakeEventSource {
		return FakeEventSource.instances.at(-1)!;
	}

	closed = false;
	private listeners = new Map<string, Listener[]>();

	constructor(readonly url: string) {
		FakeEventSource.instances.push(this);
	}

	addEventListener(type: string, listener: Listener) {
		this.listeners.set(type, [...(this.listeners.get(type) ?? []), listener]);
	}

	close() {
		this.closed = true;
	}

	/** The topics the stream listens for (without `open` and `error`). */
	get topics() {
		return [...this.listeners.keys()].filter((type) => type !== "open" && type !== "error").sort();
	}

	open() {
		this.emit("open", "");
	}

	fail() {
		this.emit("error", "");
	}

	send(topic: string, data: unknown) {
		this.emit(topic, typeof data === "string" ? data : JSON.stringify(data));
	}

	private emit(type: string, data: string) {
		for (const listener of this.listeners.get(type) ?? []) listener(new MessageEvent(type, { data }));
	}
}

/** A scheduler that runs a waiting job only when the test says so; the waits are recorded. */
export function manualSchedule() {
	const jobs: Array<{ run: () => void; ms: number; cancelled: boolean }> = [];
	return {
		schedule: (run: () => void, ms: number) => {
			const job = { run, ms, cancelled: false };
			jobs.push(job);
			return () => {
				job.cancelled = true;
			};
		},
		jobs,
		/** Runs the oldest job that is still waiting. */
		runNext() {
			const job = jobs.find((candidate) => !candidate.cancelled);
			if (!job) throw new Error("no job is waiting");
			job.cancelled = true;
			job.run();
		},
		waits: () => jobs.map((job) => job.ms),
	};
}

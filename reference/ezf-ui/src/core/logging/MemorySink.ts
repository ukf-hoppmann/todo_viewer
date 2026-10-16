import type { LogEntry, LogSink } from "./types";

/** Keeps the written entries in a list; for tests of the core and of plugins. */
export class MemorySink implements LogSink {
	readonly entries: LogEntry[] = [];

	constructor(readonly name = "memory") {}

	write(entry: LogEntry): void {
		this.entries.push(entry);
	}

	clear(): void {
		this.entries.length = 0;
	}
}

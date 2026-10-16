import type { LogEntry, LogSink, SinkContext } from "./types";

function clock(iso: string): string {
	const time = new Date(iso);
	const part = (value: number, width = 2) => String(value).padStart(width, "0");
	return `${part(time.getHours())}:${part(time.getMinutes())}:${part(time.getSeconds())}.${part(time.getMilliseconds(), 3)}`;
}

/**
 * Writes to the browser console. `data` appears only where the effective
 * level for the origin is `debug`; the console is more exposed than the backend.
 */
export class ConsoleSink implements LogSink {
	readonly name = "console";

	write(entry: LogEntry, context: SinkContext): void {
		const details = [entry.element, entry.action, entry.message].filter(Boolean).join(" | ");
		const line = `${clock(entry.time)} ${entry.level.toUpperCase()} ${entry.origin}${details && ` | ${details}`}`;
		const extras: unknown[] = [`id=${entry.id}`];
		if (entry.error !== undefined) extras.push(entry.error);
		if (entry.data !== undefined && context.level === "debug") {
			extras.push(context.toLoggable(entry.data));
		}
		console[entry.level](line, ...extras);
	}
}

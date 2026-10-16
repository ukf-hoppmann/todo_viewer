import type { LoggableLimits } from "./toLoggable";

/** Levels in ascending order of severity. */
export const logLevels = ["debug", "info", "warn", "error"] as const;

export type LogLevel = (typeof logLevels)[number];

/** What a caller passes to a log method. All fields are optional. */
export interface LogInput {
	/** Test id of the element (`<owner-id>.<element>`). */
	element?: string;
	/** What happened, e.g. `click`, `submit`, `load-config`. */
	action?: string;
	/** Technical text. */
	message?: string;
	/** Key or text of the message for the user; set only by `reportError`. */
	userMessage?: string;
	/** Any value; a sink converts it before writing. */
	data?: unknown;
	/** Error object or any thrown value. */
	error?: unknown;
}

/** A log call completed with the automatic fields. */
export interface LogEntry extends LogInput {
	/** Short entry id (8 hex characters). */
	id: string;
	/** ISO timestamp. */
	time: string;
	level: LogLevel;
	/** `core` or a plugin id. */
	origin: string;
	/** Random id per page load, equal for all entries. */
	sessionId: string;
	/** `window.location.pathname` at the time of the call. */
	route: string;
}

/** Access to the central logging with a fixed origin. */
export interface Logger {
	debug(input: string | LogInput): LogEntry;
	info(input: string | LogInput): LogEntry;
	warn(input: string | LogInput): LogEntry;
	error(input: string | LogInput): LogEntry;
}

export interface SinkContext {
	/** Effective level of this sink for the origin of the entry. */
	level: LogLevel;
	/** Converts a value with the configured limits. */
	toLoggable(value: unknown): unknown;
}

/** An output of the logging, e.g. console or backend. */
export interface LogSink {
	/** Unique name, e.g. `console`, `backend`, `memory`. */
	name: string;
	write(entry: LogEntry, context: SinkContext): void;
}

/** Minimum level of a sink, with optional levels per origin. */
export interface SinkLevels {
	level: LogLevel;
	origins?: Record<string, LogLevel>;
}

/** The section `logging` of the app config (see `logging.schema.json`). */
export interface LoggingConfig {
	outputs?: Record<string, SinkLevels>;
	limits?: Partial<LoggableLimits>;
}

export interface Logging {
	/** Registers a sink; a level remembered through `configure` takes precedence. */
	addSink(sink: LogSink, levels: SinkLevels): void;
	removeSink(name: string): void;
	/** Applies the section `logging` of the app config. */
	configure(config: LoggingConfig): void;
	/** Effective level of a sink for an origin; `undefined` if it is not registered. */
	effectiveLevel(sinkName: string, origin: string): LogLevel | undefined;
	/** Logger with a fixed origin; the same origin returns the same logger. */
	forOrigin(origin: string): Logger;
}

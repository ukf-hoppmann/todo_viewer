import { defaultLoggableLimits, toLoggable, type LoggableLimits } from "./toLoggable";
import {
	logLevels,
	type LogEntry,
	type LogInput,
	type LogLevel,
	type Logger,
	type Logging,
	type LoggingConfig,
	type LogSink,
	type SinkLevels,
} from "./types";

/** Entries remembered before the first `configure`; not configurable. */
const BUFFER_SIZE = 500;

const ORIGIN_PATTERN = /^[a-z0-9]+(-[a-z0-9]+)*$/;

interface RegisteredSink {
	sink: LogSink;
	levels: SinkLevels;
}

interface BufferedEntry {
	entry: LogEntry;
	/** Names of the sinks that already received the entry. */
	delivered: Set<string>;
}

function randomHex(length: number): string {
	const bytes = crypto.getRandomValues(new Uint8Array(length / 2));
	return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function reaches(level: LogLevel, minimum: LogLevel): boolean {
	return logLevels.indexOf(level) >= logLevels.indexOf(minimum);
}

function effective(levels: SinkLevels, origin: string): LogLevel {
	return levels.origins?.[origin] ?? levels.level;
}

/**
 * Creates an independent logging object. The core uses one instance
 * (`logging`); tests create their own.
 */
export function createLogging(): Logging {
	const sinks = new Map<string, RegisteredSink>();
	const remembered = new Map<string, SinkLevels>();
	const reportedFailures = new Set<string>();
	const loggers = new Map<string, Logger>();
	const sessionId = randomHex(32);
	let limits: LoggableLimits = { ...defaultLoggableLimits };
	let configured = false;
	let buffer: BufferedEntry[] = [];

	const context = (levels: SinkLevels, origin: string) => ({
		level: effective(levels, origin),
		toLoggable: (value: unknown) => toLoggable(value, limits),
	});

	function deliver(registered: RegisteredSink, entry: LogEntry): boolean {
		if (!reaches(entry.level, effective(registered.levels, entry.origin))) return false;
		try {
			registered.sink.write(entry, context(registered.levels, entry.origin));
		} catch (error) {
			if (!reportedFailures.has(registered.sink.name)) {
				reportedFailures.add(registered.sink.name);
				console.error(`Log sink "${registered.sink.name}" failed`, error);
			}
		}
		return true;
	}

	function log(origin: string, level: LogLevel, input: string | LogInput): LogEntry {
		const fields = typeof input === "string" ? { message: input } : input;
		const entry: LogEntry = {
			...fields,
			id: randomHex(8),
			time: new Date().toISOString(),
			level,
			origin,
			sessionId,
			route: typeof window === "undefined" ? "" : window.location.pathname,
		};

		const delivered = new Set<string>();
		for (const registered of sinks.values()) {
			if (deliver(registered, entry)) delivered.add(registered.sink.name);
		}
		if (!configured && delivered.size < Math.max(sinks.size, 1)) {
			buffer.push({ entry, delivered });
			if (buffer.length > BUFFER_SIZE) buffer.shift();
		}
		return entry;
	}

	function flushBuffer(): void {
		const pending = buffer;
		buffer = [];
		for (const { entry, delivered } of pending) {
			for (const registered of sinks.values()) {
				if (!delivered.has(registered.sink.name)) deliver(registered, entry);
			}
		}
	}

	function createLogger(origin: string): Logger {
		return {
			debug: (input) => log(origin, "debug", input),
			info: (input) => log(origin, "info", input),
			warn: (input) => log(origin, "warn", input),
			error: (input) => log(origin, "error", input),
		};
	}

	return {
		addSink(sink, levels) {
			if (sinks.has(sink.name)) throw new Error(`Log sink "${sink.name}" already exists`);
			sinks.set(sink.name, { sink, levels: remembered.get(sink.name) ?? levels });
			remembered.delete(sink.name);
		},

		removeSink(name) {
			sinks.delete(name);
			reportedFailures.delete(name);
		},

		configure(config: LoggingConfig) {
			for (const [name, levels] of Object.entries(config.outputs ?? {})) {
				const registered = sinks.get(name);
				if (registered) registered.levels = levels;
				else remembered.set(name, levels);
			}
			if (config.limits) limits = { ...limits, ...config.limits };
			if (!configured) {
				configured = true;
				flushBuffer();
			}
		},

		effectiveLevel(sinkName, origin) {
			const registered = sinks.get(sinkName);
			return registered && effective(registered.levels, origin);
		},

		forOrigin(origin) {
			if (!ORIGIN_PATTERN.test(origin)) {
				throw new Error(`Invalid log origin "${origin}": expected "core" or a kebab-case plugin id`);
			}
			let logger = loggers.get(origin);
			if (!logger) {
				logger = createLogger(origin);
				loggers.set(origin, logger);
			}
			return logger;
		},
	};
}

export interface LoggableLimits {
	/** Nesting levels of objects and lists that are kept. */
	depth: number;
	/** Entries kept per object or list. */
	entries: number;
	/** Characters kept per string. */
	stringLength: number;
}

export const defaultLoggableLimits: LoggableLimits = {
	depth: 10,
	entries: 1000,
	stringLength: 10_000,
};

const TRUNCATED = "[truncated]";
const CIRCULAR = "[Circular]";

/**
 * Converts any value into a JSON-compatible copy that is safe to write to a
 * log: cycles, errors, dates, maps and sets are converted, and the size is
 * limited. Exceeded limits are marked with `[truncated]`.
 */
export function toLoggable(value: unknown, options: Partial<LoggableLimits> = {}): unknown {
	const limits = { ...defaultLoggableLimits, ...options };
	return convert(value, limits, 0, new Set());
}

function convert(
	value: unknown,
	limits: LoggableLimits,
	level: number,
	ancestors: Set<object>,
): unknown {
	switch (typeof value) {
		case "string":
			return value.length > limits.stringLength
				? value.slice(0, limits.stringLength) + TRUNCATED
				: value;
		case "number":
			return Number.isFinite(value) ? value : String(value);
		case "bigint":
			return value.toString();
		case "function":
		case "symbol":
		case "undefined":
			return undefined;
		case "object":
			return value === null ? null : convertObject(value, limits, level, ancestors);
		default:
			return value;
	}
}

function convertObject(
	value: object,
	limits: LoggableLimits,
	level: number,
	ancestors: Set<object>,
): unknown {
	if (ancestors.has(value)) return CIRCULAR;
	if (value instanceof Date) {
		return Number.isNaN(value.getTime()) ? "Invalid Date" : value.toISOString();
	}
	if (level >= limits.depth) return TRUNCATED;

	ancestors.add(value);
	try {
		if (value instanceof Error) return convertError(value, limits, level, ancestors);
		if (Array.isArray(value) || value instanceof Set) {
			return convertList([...value], limits, level, ancestors);
		}
		const entries =
			value instanceof Map
				? [...value].map(([key, item]): [string, unknown] => [String(key), item])
				: Object.entries(value);
		return convertEntries(entries, limits, level, ancestors);
	} finally {
		ancestors.delete(value);
	}
}

function convertList(
	items: unknown[],
	limits: LoggableLimits,
	level: number,
	ancestors: Set<object>,
): unknown[] {
	const result = items
		.slice(0, limits.entries)
		.map((item) => convert(item, limits, level + 1, ancestors) ?? null);
	if (items.length > limits.entries) result.push(TRUNCATED);
	return result;
}

function convertEntries(
	entries: [string, unknown][],
	limits: LoggableLimits,
	level: number,
	ancestors: Set<object>,
): Record<string, unknown> {
	const result: Record<string, unknown> = {};
	for (const [key, item] of entries.slice(0, limits.entries)) {
		const converted = convert(item, limits, level + 1, ancestors);
		if (converted !== undefined) result[key] = converted;
	}
	if (entries.length > limits.entries) result[TRUNCATED] = entries.length - limits.entries;
	return result;
}

function convertError(
	error: Error,
	limits: LoggableLimits,
	level: number,
	ancestors: Set<object>,
): Record<string, unknown> {
	const result: Record<string, unknown> = {
		name: error.name,
		message: convert(error.message, limits, level + 1, ancestors),
		stack: convert(error.stack, limits, level + 1, ancestors),
	};
	if (error.cause !== undefined) result.cause = convert(error.cause, limits, level + 1, ancestors);
	return result;
}

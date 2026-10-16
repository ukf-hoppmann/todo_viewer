import { ConfigError } from "./ConfigError";
import type { ConfigSource } from "./types";

/**
 * Loads a config file from the source and checks it with `validate`. Throws
 * `ConfigError`; a source that fails in another way is reported as
 * `config-unreachable`.
 */
export async function loadConfig<T>(source: ConfigSource, validate: (raw: unknown) => T): Promise<T> {
	let raw: unknown;
	try {
		raw = await source.load();
	} catch (cause) {
		if (cause instanceof ConfigError) throw cause;
		throw new ConfigError("config-unreachable", "the config source failed", [], cause);
	}
	return validate(raw);
}

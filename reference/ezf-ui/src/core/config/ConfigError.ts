export type ConfigErrorCode =
	/** Network error, or an HTTP status other than 200. */
	| "config-unreachable"
	/** The content is no JSON, also an empty file. */
	| "config-not-json"
	/** The schema is violated; `details` lists every violation. */
	| "config-invalid"
	/** The config switches plugins that do not exist; `details` lists each of them. */
	| "config-unknown-plugin";

/** One violation: the place in the config (JSON pointer, empty for the root) and what is wrong there. */
export interface ConfigErrorDetail {
	path: string;
	message: string;
}

/**
 * The app config could not be loaded or is not valid. The message holds the
 * code and every detail, so that the technical details of a reported error
 * (`name: message`) show them all.
 */
export class ConfigError extends Error {
	readonly code: ConfigErrorCode;
	readonly details: ConfigErrorDetail[];

	constructor(code: ConfigErrorCode, description: string, details: ConfigErrorDetail[] = [], cause?: unknown) {
		const lines = details.map(({ path, message }) => `${path === "" ? "/" : path}: ${message}`);
		super(`${code}: ${description}${lines.length > 0 ? ` (${lines.join("; ")})` : ""}`, { cause });
		this.name = "ConfigError";
		this.code = code;
		this.details = details;
	}
}

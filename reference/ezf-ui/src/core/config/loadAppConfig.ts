import { errors as defaultErrors } from "../errors/errors";
import type { Errors } from "../errors/types";
import { logging as defaultLogging } from "../logging/logging";
import type { Logging } from "../logging/types";
import { ConfigError } from "./ConfigError";
import { FileConfigSource } from "./FileConfigSource";
import { loadConfig } from "./loadConfig";
import type { AppConfig, ConfigSource } from "./types";
import { validateAppConfig } from "./validateAppConfig";

interface LoadAppConfigOptions {
	/** The file `/config.json` by default. */
	source?: ConfigSource;
	logging?: Logging;
	errors?: Errors;
}

/**
 * The start of the application: loads and checks the config and applies its
 * section `logging`. A config that cannot be used is reported (log entry and
 * a dialog for the user) and nothing is returned: the application must not
 * start. The dialog is not awaited, so the caller does not wait for the user.
 */
export async function loadAppConfig({
	source = new FileConfigSource("/config.json"),
	logging = defaultLogging,
	errors = defaultErrors,
}: LoadAppConfigOptions = {}): Promise<AppConfig | undefined> {
	let config: AppConfig;
	try {
		config = await loadConfig(source, validateAppConfig);
	} catch (error) {
		if (!(error instanceof ConfigError)) throw error;
		void errors.forOrigin("core")({
			userMessage: { key: "config.invalid" },
			action: "load-config",
			error,
			data: error.details,
		});
		return undefined;
	}

	// Without the section the standard levels stay; the call also releases the entries remembered so far.
	logging.configure(config.logging ?? {});
	return config;
}

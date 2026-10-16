import { errors as defaultErrors } from "../errors/errors";
import type { Errors } from "../errors/types";
import { ConfigError } from "./ConfigError";
import { FileConfigSource } from "./FileConfigSource";
import { loadConfig } from "./loadConfig";
import type { ConfigSource, PluginSelection } from "./types";
import { validatePluginSelection } from "./validatePluginSelection";

interface LoadPluginSelectionOptions {
	/** The file `/plugins.json` by default; a later source (the backend) takes its place here. */
	source?: ConfigSource;
	errors?: Errors;
}

/**
 * Loads and checks the plugin selection; called only after the login has been
 * checked. A selection that cannot be used is reported like a bad app config
 * (log entry and a dialog for the user) and nothing is returned: the
 * application must not start. The dialog is not awaited.
 */
export async function loadPluginSelection({
	source = new FileConfigSource("/plugins.json"),
	errors = defaultErrors,
}: LoadPluginSelectionOptions = {}): Promise<PluginSelection | undefined> {
	try {
		return await loadConfig(source, validatePluginSelection);
	} catch (error) {
		if (!(error instanceof ConfigError)) throw error;
		void errors.forOrigin("core")({
			userMessage: { key: "config.invalid" },
			action: "load-plugin-selection",
			error,
			data: error.details,
		});
		return undefined;
	}
}

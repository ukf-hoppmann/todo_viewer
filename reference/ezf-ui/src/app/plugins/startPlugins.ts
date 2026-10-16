import type { i18n as I18n } from "i18next";
import {
	ConfigError,
	createPluginRegistry,
	errors as defaultErrors,
	logging as defaultLogging,
	type PluginSelection,
	type Contribution,
	type Errors,
	type Logging,
	type PluginCatalogue,
	type PluginRegistry,
} from "../../core";

interface StartPluginsOptions {
	config: PluginSelection;
	catalogue: PluginCatalogue;
	i18n: I18n;
	logging?: Logging;
	errors?: Errors;
	/** The contributions of the core; the same list goes to `createAppRouter`. */
	coreContributions?: readonly Contribution[];
}

/**
 * Creates the plugin registry of this start. A config that names unknown
 * plugins is reported like any other config error (log entry and dialog) and
 * nothing is returned: the application must not start.
 */
export async function startPlugins({
	config,
	catalogue,
	i18n,
	logging = defaultLogging,
	errors = defaultErrors,
	coreContributions,
}: StartPluginsOptions): Promise<PluginRegistry | undefined> {
	try {
		return await createPluginRegistry({ config, catalogue, i18n, logger: logging.forOrigin("core"), coreContributions });
	} catch (error) {
		if (!(error instanceof ConfigError)) throw error;
		void errors.forOrigin("core")({
			userMessage: { key: "config.invalid" },
			action: "activate-plugins",
			error,
			data: error.details,
		});
		return undefined;
	}
}

import type { i18n as I18n } from "i18next";
import {
	createPluginRegistry,
	errors as defaultErrors,
	logging as defaultLogging,
	PluginSelectionError,
	type Errors,
	type Logging,
	type PluginCatalogue,
	type PluginRegistry,
	type PluginSelection,
} from "../../core";

interface StartPluginsOptions {
	config: PluginSelection;
	catalogue: PluginCatalogue;
	i18n: I18n;
	logging?: Logging;
	errors?: Errors;
}

/**
 * Creates the plugin registry of this start. A selection that names unknown
 * plugins is reported like any other error (log entry and dialog) and
 * nothing is returned: the application must not start.
 */
export async function startPlugins({
	config,
	catalogue,
	i18n,
	logging = defaultLogging,
	errors = defaultErrors,
}: StartPluginsOptions): Promise<PluginRegistry | undefined> {
	try {
		return await createPluginRegistry({ config, catalogue, i18n, logger: logging.forOrigin("core") });
	} catch (error) {
		if (!(error instanceof PluginSelectionError)) throw error;
		void errors.forOrigin("core")({
			userMessage: { key: "config.invalid" },
			action: "activate-plugins",
			error,
			data: error.details,
		});
		return undefined;
	}
}

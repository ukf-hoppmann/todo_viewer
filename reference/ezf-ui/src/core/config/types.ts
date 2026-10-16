import type { BannerSettings } from "../banners/types";
import type { ConnectionSettings } from "../backend/types";
import type { LoggingConfig } from "../logging/types";

/** The switch of one plugin. Settings follow with the first plugin that needs them. */
export interface PluginConfig {
	enabled: boolean;
}

/**
 * Start view and order of the entries per slot. Views are written
 * `<owner id>/<name>`; `start` may also be a sidebar entry
 * (`<host id>/<host name>/<owner id>/<name>`). Every other key is a slot
 * (`core.main`) whose value lists the entries in order.
 */
export type NavigationConfig = { start?: string } & { [slot: string]: string[] | string | undefined };

/** The backend the application talks to. */
export interface ApiConfig {
	/** Complete address without a slash at the end; the address of an endpoint is `<url>/<endpoint>`. */
	url: string;
	/** How long the address remembered before the login is valid, in minutes; 10 if missing. */
	returnToMaxAgeMinutes?: number;
	/** What happens when the backend does not answer; the defaults apply to missing fields. */
	connection?: Partial<ConnectionSettings>;
}

/** The app config (`config.json`), loaded first; matches `appConfig.schema.json`. */
export interface AppConfig {
	api: ApiConfig;
	logging?: LoggingConfig;
	/** Settings for the banners under the app bar; the defaults apply without the section. */
	banners?: BannerSettings;
}

/** The plugin selection (`plugins.json`), loaded after the login; matches `pluginSelection.schema.json`. */
export interface PluginSelection {
	navigation?: NavigationConfig;
	/** Keyed by plugin id; a plugin that is missing is switched off. */
	plugins: Record<string, PluginConfig>;
}

/** Where a config file comes from. Returns the raw data; the core checks it. */
export interface ConfigSource {
	load(): Promise<unknown>;
}

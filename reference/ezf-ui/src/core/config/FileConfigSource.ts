import { ConfigError } from "./ConfigError";
import type { ConfigSource } from "./types";

/**
 * Loads a config file next to the application (`/config.json`,
 * `/plugins.json`). The file is not bundled, so it can be changed without a
 * build; it is requested without a cache, so a change applies after the next
 * reload.
 */
export class FileConfigSource implements ConfigSource {
	constructor(private readonly url: string) {}

	async load(): Promise<unknown> {
		const { url } = this;
		let response: Response;
		try {
			response = await fetch(url, { cache: "no-store" });
		} catch (cause) {
			throw new ConfigError("config-unreachable", `${url} could not be requested`, [], cause);
		}
		if (response.status !== 200) {
			throw new ConfigError("config-unreachable", `${url} answered with HTTP status ${response.status}`);
		}

		try {
			return await response.json();
		} catch (cause) {
			throw new ConfigError("config-not-json", `${url} does not contain JSON`, [], cause);
		}
	}
}

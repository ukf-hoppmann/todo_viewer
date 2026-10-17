/** One violation: the place in the selection (JSON pointer) and what is wrong there. */
export interface PluginSelectionErrorDetail {
	path: string;
	message: string;
}

/** The plugin selection names plugins that do not exist; the application must not start. */
export class PluginSelectionError extends Error {
	readonly code = "config-unknown-plugin";
	readonly details: PluginSelectionErrorDetail[];

	constructor(description: string, details: PluginSelectionErrorDetail[]) {
		const lines = details.map(({ path, message }) => `${path}: ${message}`);
		super(`config-unknown-plugin: ${description}${lines.length > 0 ? ` (${lines.join("; ")})` : ""}`);
		this.name = "PluginSelectionError";
		this.details = details;
	}
}

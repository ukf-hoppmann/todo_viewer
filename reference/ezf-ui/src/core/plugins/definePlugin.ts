import type { PluginDefinition } from "./types";

/** Types the definition of a plugin; returns it unchanged. */
export function definePlugin(definition: PluginDefinition): PluginDefinition {
	return definition;
}

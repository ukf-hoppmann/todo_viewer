import type { PluginSelection } from "../../core";

/**
 * The plugins that are switched on: a fixed list in code (architecture rule 1, scope client). The catalogue
 * holds every plugin of the build; a plugin that is not listed here is switched off. The example plugin is
 * only part of the development mode.
 */
export const activePluginIds: readonly string[] = [
	"layout-header-sidebar",
	"workspace",
	"backlog",
	"notes",
	"alarms",
	...(import.meta.env.DEV ? ["example"] : []),
];

export function activePluginSelection(ids: readonly string[] = activePluginIds): PluginSelection {
	return { plugins: Object.fromEntries(ids.map((id) => [id, { enabled: true }])) };
}

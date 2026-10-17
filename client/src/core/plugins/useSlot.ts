import { useMemo, type ComponentType } from "react";
import { useLocation } from "react-router";
import { parseViewPath, viewKey } from "../navigation/paths";
import { isWidgetContribution } from "./contributions";
import type { ActivePlugin } from "./types";
import { usePluginRegistry } from "./usePluginRegistry";

/** One component in a slot, with whoever contributed it. */
export interface SlotEntry {
	/** The plugin id of the contributor. */
	ownerId: string;
	name: string;
	component: ComponentType;
}

/**
 * The widgets of a slot of the active plugins, in the fixed order: by `order`, then by plugin id, then in the
 * order of the definition. A widget with `when` appears only on those main routes (`route` is the main route
 * that is open, `<owner id>/<name>`).
 */
export function selectSlotEntries(active: readonly ActivePlugin[], slot: string, route?: string): SlotEntry[] {
	const entries = active.flatMap(({ id, definition }) =>
		(definition.contributions ?? [])
			.filter(isWidgetContribution)
			.filter((widget) => widget.slot === slot)
			.filter((widget) => widget.when === undefined || (route !== undefined && widget.when.includes(route)))
			.map((widget, position) => ({ ownerId: id, name: widget.name, component: widget.component, order: widget.order ?? 0, position })),
	);
	return entries
		.sort((a, b) => a.order - b.order || a.ownerId.localeCompare(b.ownerId) || a.position - b.position)
		.map(({ ownerId, name, component }) => ({ ownerId, name, component }));
}

/** The main route that is open, `<owner id>/<name>`, or nothing at `/`. */
export function useActiveRoute(): string | undefined {
	const { pathname } = useLocation();
	const parsed = parseViewPath(pathname);
	return parsed?.name === undefined ? undefined : viewKey(parsed.ownerId, parsed.name);
}

/** The owner of a slot draws these components. Needs a router and a `PluginRegistryProvider` above it. */
export function useSlot(slot: string): SlotEntry[] {
	const registry = usePluginRegistry();
	const route = useActiveRoute();
	return useMemo(() => selectSlotEntries(registry.active(), slot, route), [registry, slot, route]);
}

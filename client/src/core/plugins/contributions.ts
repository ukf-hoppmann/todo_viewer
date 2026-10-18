import type { Contribution, MainContribution, WidgetContribution } from "./types";

/** The slot of the main routes (the tabs). */
export const mainSlot = "core.main";

/** A contribution to the tabs. */
export function isMainContribution(contribution: Contribution): contribution is MainContribution {
	return contribution.slot === mainSlot;
}

/** A component in a slot of an owner. */
export function isWidgetContribution(contribution: Contribution): contribution is WidgetContribution {
	return "component" in contribution && contribution.component !== undefined;
}

/**
 * The slots the core itself provides (names without the owner): the sections of the settings page and the
 * sections of the sidebar of the main routes that ask for one (`layout.sidebar`).
 */
export const coreSlotNames: readonly string[] = ["settings-sections", "sidebar-sections"];

/** Splits a slot `<host id>.<host name>`; nothing for any other text. */
export function parseSlot(slot: string): { hostId: string; hostName: string } | undefined {
	const parts = slot.split(".");
	const [hostId, hostName] = parts;
	if (parts.length !== 2 || !hostId || !hostName) return undefined;
	return { hostId, hostName };
}

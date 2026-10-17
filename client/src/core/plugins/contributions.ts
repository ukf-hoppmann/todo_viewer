import type { Contribution, MainContribution, MainSidebarContribution, SidebarContribution, WidgetContribution } from "./types";

/** The slot of the main routes (the tabs). */
export const mainSlot = "core.main";

/** A contribution to the tabs. */
export function isMainContribution(contribution: Contribution): contribution is MainContribution {
	return contribution.slot === mainSlot;
}

/** A main route that opens a sidebar instead of showing a page. */
export function hasSidebar(contribution: MainContribution): contribution is MainSidebarContribution {
	return contribution.layout?.sidebar === true;
}

/** A component in a slot of an owner. */
export function isWidgetContribution(contribution: Contribution): contribution is WidgetContribution {
	return "component" in contribution && contribution.component !== undefined;
}

/** An entry of a sidebar. */
export function isSidebarEntry(contribution: Contribution): contribution is SidebarContribution {
	return contribution.slot !== mainSlot && !isWidgetContribution(contribution);
}

/** The slots the core itself provides (names without the owner): the sections of the settings page. */
export const coreSlotNames: readonly string[] = ["settings-sections"];

/** The slot a main route with a sidebar opens: `<owner id>.<name>`. */
export function sidebarSlot(ownerId: string, name: string): string {
	return `${ownerId}.${name}`;
}

/** Splits a slot `<host id>.<host name>`; nothing for any other text. */
export function parseSlot(slot: string): { hostId: string; hostName: string } | undefined {
	const parts = slot.split(".");
	const [hostId, hostName] = parts;
	if (parts.length !== 2 || !hostId || !hostName) return undefined;
	return { hostId, hostName };
}

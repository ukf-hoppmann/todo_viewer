import type { MainContribution } from "../plugins/types";

/** A tab: a contribution to `core.main` together with whoever contributed it. */
export interface NavEntry {
	/** `core` or a plugin id. */
	ownerId: string;
	name: string;
	contribution: MainContribution;
}

/**
 * Start view and order of the tabs. Views are written `<owner id>/<name>`. Every other key is a slot
 * (`core.main`) whose value lists the entries in order.
 */
export type NavigationConfig = { start?: string } & { [slot: string]: string[] | string | undefined };

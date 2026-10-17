import type { MainContribution, SidebarContribution } from "../plugins/types";

/** An entry of a sidebar together with whoever contributed it and the main route it hangs in. */
export interface SidebarEntry {
	/** `core` or a plugin id: who contributed the entry. */
	ownerId: string;
	name: string;
	/** The slot the entry hangs in: `<host id>.<host name>`. */
	slot: string;
	hostId: string;
	/** The name of the main route that opens the sidebar. */
	hostName: string;
	contribution: SidebarContribution;
}

/** A tab: a contribution to `core.main` together with whoever contributed it. */
export interface NavEntry {
	/** `core` or a plugin id. */
	ownerId: string;
	name: string;
	contribution: MainContribution;
}

/**
 * Start view and order of the entries per slot. Views are written `<owner id>/<name>`; `start` may also be a
 * sidebar entry (`<host id>/<host name>/<owner id>/<name>`). Every other key is a slot (`core.main`) whose
 * value lists the entries in order.
 */
export type NavigationConfig = { start?: string } & { [slot: string]: string[] | string | undefined };

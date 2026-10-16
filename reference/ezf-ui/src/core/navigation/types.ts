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

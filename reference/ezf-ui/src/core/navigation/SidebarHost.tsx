import { Outlet } from "react-router";
import { Sidebar } from "./Sidebar";
import { SubLayout } from "./SubLayout";
import type { SidebarEntry } from "./types";

interface SidebarHostProps {
	/** The main route asked for a header area (`layout.header`). */
	header: boolean;
	/** The main route that opens the sidebar. */
	host: { ownerId: string; name: string };
	/** The entries in their order. */
	entries: readonly SidebarEntry[];
}

/**
 * The element of a main route with a sidebar: the sub layout with header and
 * sidebar, and the page of the selected entry (the child route) as content.
 * Sidebar and header stay when the entry changes.
 */
export function SidebarHost({ header, host, entries }: SidebarHostProps) {
	return (
		<SubLayout header={header} sidebar={<Sidebar host={host} entries={entries} />}>
			<Outlet />
		</SubLayout>
	);
}

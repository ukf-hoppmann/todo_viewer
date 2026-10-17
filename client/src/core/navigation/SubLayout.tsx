import { Box, Divider } from "@mui/material";
import { useMemo, useState, type ReactNode } from "react";
import { coreTestIds } from "../testIds";
import { PageHeaderContext } from "./PageHeaderContext";

interface SubLayoutProps {
	/** The main route asks for a header area (`layout.header`). */
	header: boolean;
	/** The sidebar of the main route (`layout.sidebar`); it stands left of the content, below the header. */
	sidebar?: ReactNode;
	/** The page of the main route, or of the selected entry of its sidebar. */
	children: ReactNode;
}

/**
 * The layout below the tabs, the same for every main route: a header area if
 * the main route asks for one, a sidebar if it asks for one, and the content.
 * The header area exists as soon as the layout does, so the content does not
 * jump while the page is still loading. The page fills the header through
 * `usePageHeader`.
 */
export function SubLayout({ header, sidebar, children }: SubLayoutProps) {
	const [headerContent, setHeaderContent] = useState<ReactNode>();
	const context = useMemo(() => ({ enabled: header, set: setHeaderContent }), [header]);

	return (
		<PageHeaderContext value={context}>
			{header && (
				<Box
					data-testid={coreTestIds.pageHeader}
					sx={{ minHeight: 64, bgcolor: "action.hover", borderBottom: 1, borderColor: "divider" }}
				>
					{headerContent}
				</Box>
			)}
			{sidebar ? (
				<Box sx={{ display: "flex", gap: 1, flexGrow: 1, minHeight: 0 }}>
					{sidebar}
					<Divider orientation="vertical" flexItem />
					<Box data-testid={coreTestIds.content} sx={{ flexGrow: 1, minWidth: 0, minHeight: 0, display: "flex", flexDirection: "column", overflowY: "auto" }}>
						{children}
					</Box>
				</Box>
			) : (
				<Box data-testid={coreTestIds.content} sx={{ flexGrow: 1, minHeight: 0, display: "flex", flexDirection: "column", overflowY: "auto" }}>{children}</Box>
			)}
		</PageHeaderContext>
	);
}

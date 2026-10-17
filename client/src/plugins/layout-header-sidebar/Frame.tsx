import { Box } from "@mui/material";
import { RootLayout, useSlot, type FrameProps } from "../../core";
import { layoutTestIds } from "./testIds";

/**
 * The frame of the application: the app bar of the core (logo, tabs, language) with the widgets of the slot
 * `layout-header-sidebar.header-actions` at its right end, and a sidebar at the left with the sections of the
 * slot `layout-header-sidebar.sidebar-sections` that belong to the open main route (`when`). Without a
 * section for the route there is no sidebar.
 */
export function Frame({ tabs, children }: FrameProps) {
	const actions = useSlot("layout-header-sidebar.header-actions");
	const sections = useSlot("layout-header-sidebar.sidebar-sections");

	return (
		<RootLayout
			tabs={tabs}
			actions={
				actions.length > 0 && (
					<Box data-testid={layoutTestIds.headerActions} sx={{ display: "flex", alignItems: "center", gap: 1, flexShrink: 0 }}>
						{actions.map(({ ownerId, name, component: Action }) => (
							<Box key={`${ownerId}/${name}`} data-testid={layoutTestIds.headerAction(ownerId, name)}>
								<Action />
							</Box>
						))}
					</Box>
				)
			}
		>
			<Box sx={{ display: "flex", flexGrow: 1, minHeight: 0 }}>
				{sections.length > 0 && (
					<Box
						component="aside"
						data-testid={layoutTestIds.sidebar}
						sx={{ width: 260, flexShrink: 0, p: 2, overflowY: "auto", bgcolor: "background.paper", borderRight: 1, borderColor: "divider" }}
					>
						{sections.map(({ ownerId, name, component: Section }) => (
							<Box key={`${ownerId}/${name}`} data-testid={layoutTestIds.sidebarSection(ownerId, name)} sx={{ mb: 2 }}>
								<Section />
							</Box>
						))}
					</Box>
				)}
				<Box sx={{ flexGrow: 1, minWidth: 0, minHeight: 0, display: "flex", flexDirection: "column", overflowY: "auto" }}>{children}</Box>
			</Box>
		</RootLayout>
	);
}

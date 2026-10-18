import { Box } from "@mui/material";
import { RootLayout, useSlot, type FrameProps } from "../../core";
import { layoutTestIds } from "./testIds";

/**
 * The frame of the application: the app bar of the core (logo, tabs, language) with the widgets of the slot
 * `layout-header-sidebar.header-actions` at its right end. Sidebar and detail column below it belong to the
 * core's sub layout (`layout.sidebar`, `layout.detail` of the main route).
 */
export function Frame({ tabs, children }: FrameProps) {
	const actions = useSlot("layout-header-sidebar.header-actions");

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
			{children}
		</RootLayout>
	);
}

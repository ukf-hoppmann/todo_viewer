import { AppBar, Box, Toolbar } from "@mui/material";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { BannerHost } from "../banners/BannerHost";
import { coreTestIds } from "../testIds";
import { AppBarControls } from "./AppBarControls";
import { AppLogo } from "./AppLogo";

interface RootLayoutProps {
	/** Between the logo and the switches. Only a logged-in user has routes, so only then are there tabs. */
	tabs?: ReactNode;
	/** At the right end, behind the switches (the logout button). */
	actions?: ReactNode;
	/** What the main area shows: the routes of the application, the login, or nothing. */
	children?: ReactNode;
}

/**
 * The layout of the whole application, the same in every state of the start: the app bar with the
 * logo, the tabs, the switches for language and color scheme and the actions, below it the banners
 * (`BannerHost`, no room without a banner), and then the main area. It knows neither a router nor the plugin registry nor the login, so it also works before the
 * login and when the start has stopped; what depends on them comes in as `tabs`, `actions`, and
 * `children`.
 */
export function RootLayout({ tabs, actions, children }: RootLayoutProps) {
	const { t } = useTranslation("core");

	return (
		<Box data-testid={coreTestIds.rootLayout} sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
			<AppBar position="static" data-testid={coreTestIds.appBar}>
				<Toolbar>
					<AppLogo />
					{tabs}
					<Box sx={{ flexGrow: 1 }} />
					<AppBarControls />
					{actions}
				</Toolbar>
			</AppBar>
			<BannerHost />
			<Box component="main" aria-label={t("layout.main")} data-testid={coreTestIds.main} sx={{ flexGrow: 1, display: "flex", flexDirection: "column" }}>
				{children}
			</Box>
		</Box>
	);
}

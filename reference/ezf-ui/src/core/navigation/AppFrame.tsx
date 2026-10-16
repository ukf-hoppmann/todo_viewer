import { Button, Tab, Tabs } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link, Outlet, useLocation } from "react-router";
import { useAuth } from "../auth/useAuth";
import { PluginErrorNotice } from "../plugins/PluginErrorNotice";
import { coreTestIds } from "../testIds";
import { parseViewPath, viewKey, viewPath } from "./paths";
import { RootLayout } from "./RootLayout";
import type { NavEntry } from "./types";

interface AppFrameProps {
	/** The tabs in their order. */
	tabs: readonly NavEntry[];
}

/**
 * Frame of the application for a logged-in user: the `RootLayout` with the tabs and the logout
 * button, and the current route in its main area. Every view of the core and of the plugins lives
 * below this one route, so the guard (`AuthGuard`) sits around it once. Needs an
 * `AuthProvider` and a `PluginRegistryProvider` above it; failed plugins are announced here once
 * after the start.
 */
export function AppFrame({ tabs }: AppFrameProps) {
	const { t } = useTranslation("core");
	const { logout } = useAuth();
	const { pathname } = useLocation();
	const parsed = parseViewPath(pathname);
	const current = parsed?.name === undefined ? undefined : viewKey(parsed.ownerId, parsed.name);
	const selected = tabs.some(({ ownerId, name }) => viewKey(ownerId, name) === current) ? current : false;

	return (
		<RootLayout
			tabs={
				// Scrollable like in the old app bar: too many tabs for the width scroll instead of running under the switches.
				<Tabs
					value={selected}
					variant="scrollable"
					scrollButtons="auto"
					textColor="inherit"
					indicatorColor="secondary"
					data-testid={coreTestIds.tabBar}
				>
					{tabs.map(({ ownerId, name, contribution }) => {
						const Icon = contribution.icon;
						return (
							<Tab
								key={viewKey(ownerId, name)}
								value={viewKey(ownerId, name)}
								component={Link}
								to={viewPath(ownerId, name)}
								icon={<Icon />}
								iconPosition="start"
								label={t(contribution.title, { ns: ownerId })}
								data-testid={coreTestIds.navTab(ownerId, name)}
							/>
						);
					})}
				</Tabs>
			}
			actions={
				// Moves into the avatar menu with TASK-020.
				<Button color="inherit" onClick={() => void logout()} sx={{ flexShrink: 0, whiteSpace: "nowrap" }} data-testid={coreTestIds.logoutButton}>
					{t("auth.logout")}
				</Button>
			}
		>
			<Outlet />
			<PluginErrorNotice />
		</RootLayout>
	);
}

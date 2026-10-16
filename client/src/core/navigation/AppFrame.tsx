import { Tab, Tabs } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link, Outlet, useLocation } from "react-router";
import { PluginErrorNotice } from "../plugins/PluginErrorNotice";
import { usePluginRegistry } from "../plugins/usePluginRegistry";
import { coreTestIds } from "../testIds";
import { parseViewPath, viewKey, viewPath } from "./paths";
import { RootLayout } from "./RootLayout";
import type { NavEntry } from "./types";

interface AppFrameProps {
	/** The tabs in their order. */
	tabs: readonly NavEntry[];
}

/**
 * Frame of the application: the app bar with the tabs and the current route in the main area. Every view of
 * the core and of the plugins lives below this one route. The plugin that provides a `frame` (the layout
 * plugin) draws the app bar and the sidebar around the tabs and the content; without one the plain
 * `RootLayout` does. Needs a `PluginRegistryProvider` above it; failed plugins are announced here once after
 * the start.
 */
export function AppFrame({ tabs }: AppFrameProps) {
	const { t } = useTranslation("core");
	const { pathname } = useLocation();
	const parsed = parseViewPath(pathname);
	const current = parsed?.name === undefined ? undefined : viewKey(parsed.ownerId, parsed.name);
	const selected = tabs.some(({ ownerId, name }) => viewKey(ownerId, name) === current) ? current : false;
	const Frame = usePluginRegistry()
		.active()
		.find(({ definition }) => definition.frame)?.definition.frame;

	// Scrollable: too many tabs for the width scroll instead of running under the switches.
	const tabBar = (
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
	);

	const content = (
		<>
			<Outlet />
			<PluginErrorNotice />
		</>
	);

	return Frame ? <Frame tabs={tabBar}>{content}</Frame> : <RootLayout tabs={tabBar}>{content}</RootLayout>;
}

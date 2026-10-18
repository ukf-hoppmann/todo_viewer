import type { ComponentType } from "react";
import { createBrowserRouter, createMemoryRouter, Navigate, type RouteObject } from "react-router";
import { logging } from "../logging/logging";
import type { Logger } from "../logging/types";
import { checkContributions } from "../plugins/checkContributions";
import type { Contribution, PluginRegistry } from "../plugins/types";
import { AppFrame } from "./AppFrame";
import { NavigationNotice } from "./NavigationNotice";
import { NotFoundView } from "./NotFoundView";
import { collectMainEntries, orderEntries, resolveStart } from "./order";
import { PageHost } from "./PageHost";
import { viewKey } from "./paths";
import { resolveView } from "./resolveView";
import { SubLayout } from "./SubLayout";
import type { NavEntry, NavigationConfig } from "./types";

/** A page for development only, shown at `/dev/<owner id>/<name>` without a tab. */
export interface DevRoute {
	ownerId: string;
	name: string;
	/** Lazy import of the page; its default export is the component. */
	load: () => Promise<{ default: ComponentType }>;
}

export interface AppRouterOptions {
	registry: PluginRegistry;
	/** Contributions of the core itself; none yet. */
	coreContributions?: readonly Contribution[];
	/** Section `navigation` of the app config. */
	navigation?: NavigationConfig;
	/** Pages that `src/app` adds in development mode. */
	devRoutes?: readonly DevRoute[];
	/** For warnings in development; the logger of `core` by default. */
	logger?: Logger;
	/** Starts a router in memory at these locations instead of the browser (tests). */
	initialEntries?: string[];
}

export type AppRouterInstance = ReturnType<typeof createBrowserRouter>;

/** Names the core must not use for its own views. */
const reservedCoreNames = ["link"];

function listFor(navigation: NavigationConfig | undefined, slot: string): string[] | undefined {
	const list = navigation?.[slot];
	return Array.isArray(list) ? list : undefined;
}

/**
 * Builds the router of the application once the plugins have started; the
 * registry does not change afterwards. Every view of the core and of the
 * plugins hangs below one common route, the app frame, A path decides
 * the view alone, so every view
 * survives a reload. Throws if a contribution of the core is invalid.
 */
export function createAppRouter({
	registry,
	coreContributions = [],
	navigation,
	devRoutes = [],
	logger = logging.forOrigin("core"),
	initialEntries,
}: AppRouterOptions): AppRouterInstance {
	const problems = checkContributions(coreContributions, { reservedNames: reservedCoreNames });
	if (problems.length > 0) throw new Error(`the contributions of the core are invalid: ${problems.join("; ")}`);

	const entries = collectMainEntries(registry.active(), coreContributions);
	const { ordered: tabs, skipped } = orderEntries(entries, listFor(navigation, "core.main"));
	const resolve = (pathname: string) => resolveView(pathname, { statuses: registry.statuses(), entries });
	const start = resolveStart(tabs, navigation?.start, (path) => resolve(path).kind === "available");

	const warnSkipped = (slot: string, keys: readonly string[]) => {
		if (!import.meta.env.DEV) return;
		for (const key of keys) {
			logger.warn({ action: "navigation", message: `navigation.${slot} lists '${key}', which is unknown or not active` });
		}
	};
	warnSkipped("core.main", skipped);
	if (import.meta.env.DEV && start.unavailableStart !== undefined) {
		logger.warn({ action: "navigation", message: `navigation.start is '${start.unavailableStart}', which is not available` });
	}

	const mainRoute = ({ ownerId, name, contribution }: NavEntry): RouteObject => ({
		path: `${ownerId}/${name}`,
		element: (
			<SubLayout key={viewKey(ownerId, name)} ownerId={ownerId} layout={contribution.layout}>
				<PageHost ownerId={ownerId} load={contribution.page} />
			</SubLayout>
		),
	});

	const devRoute = ({ ownerId, name, load }: DevRoute): RouteObject => ({
		path: `dev/${ownerId}/${name}`,
		element: (
			<SubLayout key={`dev/${viewKey(ownerId, name)}`} ownerId={ownerId}>
				<PageHost ownerId={ownerId} load={load} />
			</SubLayout>
		),
	});

	const routes: RouteObject[] = [
		{
			path: "/",
			element: <AppFrame tabs={tabs} />,
			children: [
				{
					index: true,
					// Replaces the entry in the history; the query of `/` is not carried along.
					element: start.to === undefined ? <NavigationNotice kind="no-views" /> : <Navigate to={start.to} replace />,
				},
				...tabs.map(mainRoute),
				...devRoutes.map(devRoute),
				{ path: "*", element: <NotFoundView resolve={resolve} /> },
			],
		},
	];

	if (initialEntries) {
		return createMemoryRouter(routes, { initialEntries });
	}
	return createBrowserRouter(routes);
}

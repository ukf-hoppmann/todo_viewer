import type { ComponentType } from "react";
import { createBrowserRouter, createMemoryRouter, Navigate, type RouteObject } from "react-router";
import type { NavigationConfig } from "../config/types";
import { AuthGuard } from "../auth/AuthGuard";
import { logging } from "../logging/logging";
import type { Logger } from "../logging/types";
import { checkContributions } from "../plugins/checkContributions";
import { hasSidebar, sidebarSlot } from "../plugins/contributions";
import type { Contribution, PluginRegistry } from "../plugins/types";
import { AppFrame } from "./AppFrame";
import { EmptySidebar } from "./EmptySidebar";
import { NavigationNotice } from "./NavigationNotice";
import { NotFoundView } from "./NotFoundView";
import { collectMainEntries, collectSidebarEntries, orderEntries, resolveStart } from "./order";
import { PageHost } from "./PageHost";
import { viewKey, viewPath } from "./paths";
import { resolveView } from "./resolveView";
import { SidebarHost } from "./SidebarHost";
import { SubLayout } from "./SubLayout";
import type { NavEntry } from "./types";

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
	/**
	 * Called once with a check that tells whether a path leads to an available
	 * view. An address it returns (path, query, fragment) replaces the opened one
	 * before the router starts, without a new entry in the history; this is how
	 * the user returns to the page wanted before the login.
	 */
	returnTo?: (isAvailable: (pathname: string) => boolean) => string | undefined;
}

export type AppRouterInstance = ReturnType<typeof createBrowserRouter>;

/** Names the core must not use for its own views: `/core/link/…` (STORY-011) and `/core/login` (kept free; the login page has no address). */
const reservedCoreNames = ["link", "login"];

function listFor(navigation: NavigationConfig | undefined, slot: string): string[] | undefined {
	const list = navigation?.[slot];
	return Array.isArray(list) ? list : undefined;
}

/**
 * Builds the router of the application once the plugins have started; the
 * registry does not change afterwards. Every view of the core and of the
 * plugins hangs below one common route, the app frame, with one guard around
 * it (`AuthGuard`, needs an `AuthProvider` above the router). A path decides
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
	returnTo,
}: AppRouterOptions): AppRouterInstance {
	const problems = checkContributions(coreContributions, { reservedNames: reservedCoreNames });
	if (problems.length > 0) throw new Error(`the contributions of the core are invalid: ${problems.join("; ")}`);

	const entries = collectMainEntries(registry.active(), coreContributions);
	const sidebars = collectSidebarEntries(registry.active(), coreContributions);
	const { ordered: tabs, skipped } = orderEntries(entries, listFor(navigation, "core.main"));
	const resolve = (pathname: string) => resolveView(pathname, { statuses: registry.statuses(), entries, sidebars });
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

	/** A main route with a sidebar: sidebar and header stay, the selected entry is the content. */
	const sidebarRoute = ({ ownerId, name, contribution }: NavEntry): RouteObject => {
		const slot = sidebarSlot(ownerId, name);
		const host = { ownerId, name };
		const { ordered, skipped: skippedEntries } = orderEntries(sidebars.get(slot) ?? [], listFor(navigation, slot));
		warnSkipped(slot, skippedEntries);
		const first = ordered[0];

		return {
			path: `${ownerId}/${name}`,
			element: <SidebarHost key={viewKey(ownerId, name)} header={contribution.layout?.header === true} host={host} entries={ordered} />,
			children: [
				{
					index: true,
					element: first ? <Navigate to={viewPath(first.ownerId, first.name, host)} replace /> : <EmptySidebar slot={slot} />,
				},
				...ordered.map(
					(entry): RouteObject => ({
						path: `${entry.ownerId}/${entry.name}`,
						element: <PageHost key={viewKey(entry.ownerId, entry.name)} ownerId={entry.ownerId} load={entry.contribution.page} />,
					}),
				),
				{ path: "*", element: <NotFoundView resolve={resolve} /> },
			],
		};
	};

	const mainRoute = (entry: NavEntry): RouteObject => {
		const { ownerId, name, contribution } = entry;
		if (hasSidebar(contribution)) return sidebarRoute(entry);
		return {
			path: `${ownerId}/${name}`,
			element: (
				<SubLayout key={viewKey(ownerId, name)} header={contribution.layout?.header === true}>
					<PageHost ownerId={ownerId} load={contribution.page} />
				</SubLayout>
			),
		};
	};

	const devRoute = ({ ownerId, name, load }: DevRoute): RouteObject => ({
		path: `dev/${ownerId}/${name}`,
		element: (
			<SubLayout key={`dev/${viewKey(ownerId, name)}`} header={false}>
				<PageHost ownerId={ownerId} load={load} />
			</SubLayout>
		),
	});

	const routes: RouteObject[] = [
		{
			path: "/",
			element: (
				<AuthGuard>
					<AppFrame tabs={tabs} />
				</AuthGuard>
			),
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

	// Decided before the router exists, so that it starts at the right address and nothing flashes.
	const target = returnTo?.((pathname) => resolve(pathname).kind === "available");
	if (initialEntries) {
		return createMemoryRouter(routes, { initialEntries: target ? [...initialEntries.slice(0, -1), target] : initialEntries });
	}
	if (target) globalThis.history.replaceState(null, "", target);
	return createBrowserRouter(routes);
}

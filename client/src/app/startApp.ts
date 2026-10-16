import type { i18n as I18n } from "i18next";
import {
	banners as defaultBanners,
	BackendUnreachableError,
	createAppRouter,
	createAppStore,
	createConnection,
	createConnectionMonitor,
	errors as defaultErrors,
	logging as defaultLogging,
	type AppRouterInstance,
	type AppRouterOptions,
	type AppStore,
	type Banners,
	type ConnectionFetch,
	type Contribution,
	type DevRoute,
	type Errors,
	type Logging,
	type NavigationConfig,
	type PluginCatalogue,
	type PluginRegistry,
	type PluginSelection,
} from "../core";
import { activePluginSelection } from "./plugins/activePlugins";
import { startPlugins } from "./plugins/startPlugins";

/** The server's API; the Vite dev server forwards it to the backend. */
export const apiUrl = "/api";

export interface StartAppOptions {
	i18n: I18n;
	catalogue: PluginCatalogue;
	coreContributions: readonly Contribution[];
	devRoutes: readonly DevRoute[];
	/** Which plugin is shown at `/`; the first tab by default. */
	navigation?: NavigationConfig;
	/** The plugins that are switched on; the fixed list of `activePlugins.ts` by default. */
	selection?: PluginSelection;
	logging?: Logging;
	errors?: Errors;
	banners?: Banners;
	/** For tests: replaces the `fetch` of the connection that the plugin APIs and the connection test use. */
	connection?: { fetch?: ConnectionFetch };
	/** For tests: a router in memory. */
	router?: Pick<AppRouterOptions, "initialEntries">;
}

export type StartResult =
	/** The plugins are started; the store holds one compartment per plugin with a reducer. */
	| { kind: "app"; registry: PluginRegistry; store: AppStore; router: AppRouterInstance }
	/** Something is wrong and has been reported to the user: the application stays away. */
	| { kind: "stopped" };

/**
 * The start of the application in its fixed order: logging, wait for the backend, plugins, connection,
 * store, router. A backend that does not answer is waited for (banner, no dialog); every other failure is
 * reported to the user and ends in `stopped`. There is no login. The caller renders what the result says.
 */
export async function startApp({
	i18n,
	catalogue,
	coreContributions,
	devRoutes,
	navigation,
	selection = activePluginSelection(),
	logging = defaultLogging,
	errors = defaultErrors,
	banners = defaultBanners,
	connection: connectionOptions,
	router: routerOptions,
}: StartAppOptions): Promise<StartResult> {
	logging.configure({});
	const fetchFn: ConnectionFetch = connectionOptions?.fetch ?? ((request) => fetch(request));

	// The one place that reacts when the backend does not answer; the connection reports to it.
	const monitor = createConnectionMonitor({
		banners,
		check: async ({ timeoutMs }) => {
			try {
				const response = await fetchFn(new Request(`${apiUrl}/core/health`, { signal: AbortSignal.timeout(timeoutMs) }));
				if (response.status >= 500) throw new BackendUnreachableError();
			} catch (error) {
				throw error instanceof BackendUnreachableError ? error : new BackendUnreachableError(error);
			}
		},
	});
	await monitor.waitForBackend();

	// Only the plugins that are switched on and whose requirements are met are loaded.
	const registry = await startPlugins({ config: selection, catalogue, i18n, logging, errors, coreContributions });
	if (!registry) return { kind: "stopped" };

	// The one connection of all plugin APIs; it reaches them through the store. A request that gets no answer
	// goes to the central handling, which starts the connection test.
	const connection = createConnection({ url: apiUrl, fetch: connectionOptions?.fetch, onFailure: (kind) => monitor.report(kind) });

	// Once per start; the form of the store does not change afterwards.
	const store = createAppStore({ registry, connection });

	const router = createAppRouter({ registry, coreContributions, navigation, devRoutes, ...routerOptions });
	return { kind: "app", registry, store, router };
}

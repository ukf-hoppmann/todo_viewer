import type { i18n as I18n } from "i18next";
import {
	banners as defaultBanners,
	BackendSink,
	BackendUnreachableError,
	createAppRouter,
	createAppStore,
	createConnection,
	coreApi,
	createConnectionMonitor,
	startEvents,
	errors as defaultErrors,
	logging as defaultLogging,
	type AppRouterInstance,
	type AppRouterOptions,
	type AppStore,
	type Banners,
	type ConnectionMonitorOptions,
	type ConnectionFetch,
	type Contribution,
	type DevRoute,
	type EventStream,
	type StartEventsOptions,
	type Errors,
	type Logging,
	type NavigationConfig,
	type PluginCatalogue,
	type PluginRegistry,
	type PluginSelection,
} from "../core";
import { activePluginSelection } from "./plugins/activePlugins";
import { startPlugins } from "./plugins/startPlugins";

/** The server's API, same origin as the page; the Vite dev server forwards it to the backend. */
export const apiPath = "/api";

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
	/** For tests: the timer and the settings of the connection test. */
	monitor?: Pick<ConnectionMonitorOptions, "schedule" | "settings">;
	/** For tests: a fake `EventSource`, timers and wait times of the event stream. */
	events?: StartEventsOptions["stream"];
	/** For tests: a router in memory. */
	router?: Pick<AppRouterOptions, "initialEntries">;
}

export type StartResult =
	/** The plugins are started; the store holds one compartment per plugin with a reducer. */
	| { kind: "app"; registry: PluginRegistry; store: AppStore; router: AppRouterInstance; events: EventStream }
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
	monitor: monitorOptions,
	events: eventOptions,
	router: routerOptions,
}: StartAppOptions): Promise<StartResult> {
	logging.configure({});
	const apiUrl = new URL(apiPath, globalThis.location.href).href;
	// Warnings and errors also go to `viewer.log` of the server, where they can be analysed; started once, a
	// second start (tests) replaces the sink.
	logging.removeSink("backend");
	logging.addSink(new BackendSink({ url: `${apiUrl}/core/client-log` }), { level: "warn" });
	const fetchFn: ConnectionFetch = connectionOptions?.fetch ?? ((request) => fetch(request));

	// The one place that reacts when the backend does not answer; the connection reports to it.
	const monitor = createConnectionMonitor({
		...monitorOptions,
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
	const store = createAppStore({ registry, connection, coreApis: [coreApi] });

	const router = createAppRouter({ registry, coreContributions, navigation, devRoutes, ...routerOptions });

	// The channel from the backend to the frontend; the plugins react to its events by reloading their data.
	const events = startEvents({ active: registry.active(), dispatch: store.dispatch, logger: logging.forOrigin("core"), stream: eventOptions });
	return { kind: "app", registry, store, router, events };
}

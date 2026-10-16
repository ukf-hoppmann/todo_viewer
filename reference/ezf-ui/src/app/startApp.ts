import type { i18n as I18n } from "i18next";
import {
	banners as defaultBanners,
	consumeReturnTo,
	createAppRouter,
	createAppStore,
	createAuth,
	createConnection,
	createConnectionMonitor,
	errors as defaultErrors,
	loadAppConfig,
	loadPluginSelection,
	logging as defaultLogging,
	type AppRouterInstance,
	type AppRouterOptions,
	type AppStore,
	type Auth,
	type Banners,
	type ConfigSource,
	type ConnectionFetch,
	type Contribution,
	type CreateAuthOptions,
	type DevRoute,
	type Errors,
	type Logging,
	type PluginCatalogue,
	type PluginRegistry,
	type StorageLike,
} from "../core";
import type { BackendLogging } from "./logging/installBackendLogging";
import { startPlugins } from "./plugins/startPlugins";

export interface StartAppOptions {
	backendLogging: BackendLogging;
	i18n: I18n;
	catalogue: PluginCatalogue;
	coreContributions: readonly Contribution[];
	devRoutes: readonly DevRoute[];
	/** The file `/config.json` by default. */
	appConfigSource?: ConfigSource;
	/** The file `/plugins.json` by default; later the backend. */
	pluginSelectionSource?: ConfigSource;
	logging?: Logging;
	errors?: Errors;
	/** The banner list that gets the settings of the app config and is cleared on logout; the central `banners` by default. */
	banners?: Banners;
	/** For tests: replaces the browser parts of the login. */
	auth?: Partial<Omit<CreateAuthOptions, "url" | "errors">>;
	/** For tests: replaces the `fetch` of the connection that the plugin APIs use. */
	connection?: { fetch?: ConnectionFetch };
	/** For tests: where the remembered address is read, and the clock. */
	returnTo?: { storage?: StorageLike; now?: () => number };
	/** For tests: a router in memory. */
	router?: Pick<AppRouterOptions, "initialEntries">;
}

export type StartResult =
	/** The user is not logged in: show only the login page. No plugin selection, no plugin code, no router. */
	| { kind: "login"; auth: Auth }
	/** The user is logged in and the plugins are started; the store holds one compartment per plugin with a reducer. */
	| { kind: "app"; auth: Auth; registry: PluginRegistry; store: AppStore; router: AppRouterInstance }
	/** Something is wrong and has been reported to the user: the application stays away. */
	| { kind: "stopped" };

/**
 * The start of the application in its fixed order: app config, then the check
 * of the login, and only for a logged-in user the plugin selection, the
 * plugins, and the router (architecture rule 3.5: no plugin code before the
 * login). A backend that does not answer is waited for (banner, no dialog);
 * every other failure is reported to the user and ends in `stopped`. The
 * caller renders what the result says.
 */
export async function startApp({
	backendLogging,
	i18n,
	catalogue,
	coreContributions,
	devRoutes,
	appConfigSource,
	pluginSelectionSource,
	logging = defaultLogging,
	errors = defaultErrors,
	banners = defaultBanners,
	auth: authOptions,
	connection: connectionOptions,
	returnTo,
	router: routerOptions,
}: StartAppOptions): Promise<StartResult> {
	const config = await loadAppConfig({ source: appConfigSource, logging, errors });
	if (!config) return { kind: "stopped" };

	banners.configure(config.banners ?? {});

	const auth = createAuth({ ...authOptions, url: config.api.url, errors });
	// When the user is logged out, the banners of the work so far go; the listener runs at once, so
	// a banner that is shown after the change (the hint about the logout) stays.
	auth.subscribe(() => {
		if (auth.getState() === "unauthenticated") banners.clear();
	});
	// The one place that reacts when the backend does not answer; the log output and the connection report to it.
	const monitor = createConnectionMonitor({ auth, banners, settings: config.api.connection });
	// The output sends only while the user is logged in; a 401 or 407 on the way ends the login.
	backendLogging.connect({
		url: config.api.url,
		canSend: () => auth.getState() === "authenticated",
		onFailure: (kind) => monitor.report(kind),
	});

	// Asks the login check until the backend answers: with the warning meanwhile, no dialog, no end.
	// The answer has set the state of the login by then.
	await monitor.waitForBackend();
	if (auth.getState() !== "authenticated") return { kind: "login", auth };

	const selection = await loadPluginSelection({ source: pluginSelectionSource, errors });
	if (!selection) return { kind: "stopped" };

	// Only the plugins that are switched on and whose requirements are met are loaded.
	const registry = await startPlugins({ config: selection, catalogue, i18n, logging, errors, coreContributions });
	if (!registry) return { kind: "stopped" };

	// The one connection of all plugin APIs; it reaches them through the store. A failed request goes to the
	// central handling, like a failure of the log output: 401 or 407 ends the login, no answer starts the test.
	const connection = createConnection({
		url: config.api.url,
		fetch: connectionOptions?.fetch,
		onFailure: (kind) => monitor.report(kind),
	});

	// Once per start; the form of the store does not change afterwards. A reducer that fails for its
	// initial state throws here and is reported like any other unhandled error.
	const store = createAppStore({ registry, connection });

	const router = createAppRouter({
		registry,
		coreContributions,
		navigation: selection.navigation,
		devRoutes,
		...routerOptions,
		returnTo: (isAvailable) =>
			consumeReturnTo({ ...returnTo, maxAgeMinutes: config.api.returnToMaxAgeMinutes, isAvailable, logger: logging.forOrigin("core") }),
	});
	return { kind: "app", auth, registry, store, router };
}

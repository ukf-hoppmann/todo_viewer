import {
	combineReducers,
	configureStore,
	type EnhancedStore,
	type Reducer,
	type StoreEnhancer,
	type ThunkDispatch,
	type Tuple,
	type UnknownAction,
} from "@reduxjs/toolkit";
import type { Connection, PluginApi, StoreExtra } from "../api/types";
import type { PluginRegistry } from "../plugins/types";

/** The whole state: the core does not know the plugins, so their compartments are unknown to it. */
export type AppState = Record<string, unknown>;

/** The store accepts thunks (the requests of the plugin APIs are thunks) with the connection as their extra argument. */
export type AppStore = EnhancedStore<
	AppState,
	UnknownAction,
	Tuple<[StoreEnhancer<{ dispatch: ThunkDispatch<AppState, StoreExtra, UnknownAction> }>, StoreEnhancer]>
>;

interface CreateAppStoreOptions {
	registry: PluginRegistry;
	/** The connection to the backend; the base query of every API reads it from the store at each request. */
	connection: Connection;
	/** Compartments of the core by name; none yet. A name must not be a plugin id. */
	coreSlices?: Record<string, Reducer>;
	/** APIs of the core, each under its own `reducerPath` (`core.api`); none yet. */
	coreApis?: readonly PluginApi[];
}

/**
 * Builds the global store of this start, called once by `src/app` after the
 * plugins started (architecture rule 5.1). Every active plugin with a
 * `reducer` gets one compartment under its id, whatever its slice is called,
 * and every active plugin with an `api` gets the cache and the middleware of
 * that API under `<id>.api`; switched-off, blocked, and failed plugins have
 * none. The connection travels as the extra argument of the thunk middleware.
 * The form of the store does not change afterwards.
 */
export function createAppStore({ registry, connection, coreSlices = {}, coreApis = [] }: CreateAppStoreOptions): AppStore {
	const reducers: Record<string, Reducer> = {};
	const apis: PluginApi[] = [];
	for (const { id, definition } of registry.active()) {
		if (definition.reducer) reducers[id] = definition.reducer;
		if (definition.api) apis.push(definition.api);
	}
	for (const [name, reducer] of Object.entries(coreSlices)) {
		if (name in reducers) throw new Error(`the compartment '${name}' of the core is also the id of a plugin`);
		reducers[name] = reducer;
	}
	apis.push(...coreApis);
	for (const { reducerPath, reducer } of apis) {
		if (reducerPath in reducers) throw new Error(`the key '${reducerPath}' of an API is already used`);
		reducers[reducerPath] = reducer;
	}

	// Redux refuses a combination without any reducer.
	const reducer: Reducer<AppState> = Object.keys(reducers).length > 0 ? combineReducers(reducers) : (state = {}) => state;
	const extra: StoreExtra = { connection };
	return configureStore({
		reducer,
		middleware: (getDefaultMiddleware) =>
			getDefaultMiddleware({ thunk: { extraArgument: extra } }).concat(apis.map(({ middleware }) => middleware)),
		devTools: import.meta.env.DEV,
	});
}

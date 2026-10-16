import type { Middleware, Reducer } from "@reduxjs/toolkit";
import type { BaseQueryFn, FetchArgs, FetchBaseQueryError, FetchBaseQueryMeta } from "@reduxjs/toolkit/query";
import type { BackendFailureKind } from "../backend/classifyFailure";

/** `fetchBaseQuery` always calls with a `Request`, unlike the `fetch` of the login and the log output. */
export type ConnectionFetch = (request: Request) => Promise<Response>;

/**
 * The error of a request. `kind` is set only for the two failures the core
 * handles centrally: `unauthorized` (401, 407) and `unreachable` (no answer,
 * status 500 and above). Any other error is for the caller.
 */
export type ConnectionError = FetchBaseQueryError & { kind?: BackendFailureKind };

/** The one connection to the backend that every API of the core and the plugins is built on. */
export interface Connection {
	/** The base query of RTK Query: `<url>/<endpoint>`, with the cookies, failures recognised and reported. */
	baseQuery: BaseQueryFn<string | FetchArgs, unknown, ConnectionError, object, FetchBaseQueryMeta>;
}

export interface CreateConnectionOptions {
	/** Complete address of the backend (`api.url`). */
	url: string;
	/** A request failed with `unauthorized` or `unreachable`; called once per request, not when the caller aborted it. */
	onFailure: (kind: BackendFailureKind) => void;
	/** The global `fetch` by default. */
	fetch?: ConnectionFetch;
}

/** The extra argument of the thunk middleware of the store: how every API gets to the connection. */
export interface StoreExtra {
	connection: Connection;
}

/**
 * What the core needs of an API built with `createPluginApi`: its place in the
 * state and its parts for the store. Everything else (endpoints, hooks) stays
 * with the owner.
 */
export interface PluginApi {
	/** `<owner id>.api` */
	reducerPath: string;
	reducer: Reducer;
	middleware: Middleware;
}

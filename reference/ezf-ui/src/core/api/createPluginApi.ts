import type { EndpointBuilder, EndpointDefinitions } from "@reduxjs/toolkit/query";
import { createApi } from "@reduxjs/toolkit/query/react";
import type { Connection, StoreExtra } from "./types";

type ConnectionBaseQuery = Connection["baseQuery"];

/** Reads the connection from the store at each request, so importing a plugin registers nothing. */
const connectionBaseQuery: ConnectionBaseQuery = async (args, api, extraOptions) => {
	const { connection } = (api.extra ?? {}) as Partial<StoreExtra>;
	if (!connection) throw new Error("the store was built without a connection: `createAppStore` passes it as the extra argument");
	return connection.baseQuery(args, api, extraOptions);
};

/**
 * Builds the API of an owner (the core or a plugin): its endpoints and its own
 * cache, on the connection of the core. The key in the state is always
 * `<ownerId>.api`. Nothing is registered here; a plugin names the result in
 * the field `api` of its definition and the core puts it into the store.
 * The names of the endpoints are free, the hooks follow from them
 * (`getVersion` becomes `useGetVersionQuery`).
 */
export function createPluginApi<OwnerId extends string, Definitions extends EndpointDefinitions, TagTypes extends string = never>(
	ownerId: OwnerId,
	endpoints: (build: EndpointBuilder<ConnectionBaseQuery, TagTypes, `${OwnerId}.api`>) => Definitions,
	options: { tagTypes?: readonly TagTypes[] } = {},
) {
	return createApi({
		reducerPath: `${ownerId}.api` as const,
		baseQuery: connectionBaseQuery,
		tagTypes: options.tagTypes,
		endpoints,
	});
}

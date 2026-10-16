import { createPluginApi } from "../../core";

/**
 * The plugin's own API with its own cache, on the connection of the core. The
 * key in the state is `example.api`; building it registers nothing, the plugin
 * names it in its definition. The endpoint `version` of the backend checks no
 * token and answers a text.
 */
export const exampleApi = createPluginApi("example", (build) => ({
	getVersion: build.query<string, void>({
		query: () => ({ url: "version", responseHandler: "text" }),
	}),
}));

export const { useGetVersionQuery } = exampleApi;

import { createPluginApi } from "../../core";

/**
 * The plugin's own API with its own cache, on the connection of the core. The key in the state is
 * `example.api`. `getHealth` asks the server whether it is alive; the tag `Health` is what server events
 * invalidate (see `eventHandlers` in `index.ts`).
 */
export const exampleApi = createPluginApi(
	"example",
	(build) => ({
		getHealth: build.query<{ status: string }, void>({
			query: () => "core/health",
			providesTags: ["Health"],
		}),
	}),
	{ tagTypes: ["Health"] },
);

export const { useGetHealthQuery } = exampleApi;

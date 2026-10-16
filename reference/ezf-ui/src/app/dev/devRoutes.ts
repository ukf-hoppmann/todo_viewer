import type { DevRoute } from "../../core";

/**
 * Pages for development only, shown at `/dev/<owner id>/<name>` (see
 * `createAppRouter`). The condition is fixed at build time, so production
 * builds contain neither the routes nor the chunks of their pages.
 */
export const devRoutes: DevRoute[] = import.meta.env.DEV
	? [{ ownerId: "core", name: "dialogs", load: () => import("./DialogDemo").then(({ DialogDemo }) => ({ default: DialogDemo })) }]
	: [];

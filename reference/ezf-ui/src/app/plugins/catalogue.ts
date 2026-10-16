import { buildCatalogue } from "./buildCatalogue";

/**
 * All plugins of the build (architecture rule 1.3: only `src/app` knows them).
 * The manifests are part of the main bundle; each `index.ts` becomes its own
 * chunk that is loaded only when the core activates the plugin.
 */
export const catalogue = buildCatalogue(
	import.meta.glob("../../plugins/*/plugin.json", { eager: true, import: "default" }),
	import.meta.glob("../../plugins/*/index.ts"),
);

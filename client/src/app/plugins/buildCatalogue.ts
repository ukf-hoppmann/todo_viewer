import type { PluginCatalogue } from "../../core";

/** The plugin folder of a path such as `../plugins/<id>/plugin.json`. */
function folderOf(path: string): string {
	const parts = path.split("/");
	return parts[parts.length - 2]!;
}

/**
 * Joins the results of the two folder scans into the catalogue for the core.
 * Every folder that holds one of the files becomes an entry, so that an
 * incomplete plugin is reported instead of skipped.
 */
export function buildCatalogue(
	manifests: Record<string, unknown>,
	loaders: Record<string, () => Promise<unknown>>,
): PluginCatalogue {
	const catalogue: PluginCatalogue = {};
	for (const [path, manifest] of Object.entries(manifests)) {
		catalogue[folderOf(path)] = { manifest };
	}
	for (const [path, load] of Object.entries(loaders)) {
		const id = folderOf(path);
		catalogue[id] = { manifest: catalogue[id]?.manifest, load };
	}
	return catalogue;
}

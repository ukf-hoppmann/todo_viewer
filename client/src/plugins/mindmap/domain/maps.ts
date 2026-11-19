import type { MapOut } from "../api";

/** The key of a map in lists and test ids: its tree, for a project tree without a node yet its project. */
export function mapKey(map: Pick<MapOut, "tree_uid" | "project_uid">): string {
	return map.tree_uid ?? map.project_uid;
}

/**
 * The map the page shows for a project: the chosen free map if the list still has it, else the project tree (the
 * first entry of the list). A choice that points to a map that is gone (deleted, or another project's) is ignored.
 */
export function chooseMap(maps: readonly MapOut[] | undefined, chosen: string | undefined): MapOut | undefined {
	if (!maps || maps.length === 0) return undefined;
	return (chosen ? maps.find((map) => map.kind === "free" && map.tree_uid === chosen) : undefined) ?? maps[0];
}

/** What deleting a free map does to its nodes: `going` go to the trash with it, `kept` also stand in another tree and stay there. */
export function deleteQuestion(map: Pick<MapOut, "node_count" | "shared_count">): { going: number; kept: number } {
	return { going: map.node_count - map.shared_count, kept: map.shared_count };
}

import { useMemo } from "react";
import { usePersistentState } from "../../core";
import type { Fold } from "./domain/tree";

const OWNER = "mindmap";

/**
 * What the user chose in the mind map, kept in the UI state of the server (owner `mindmap`): `fold` holds, by node,
 * only what differs from the default (two levels open); `selected` is the node open in the detail column.
 */
export function useMindmapState() {
	const [fold, setFold] = usePersistentState<Fold>(OWNER, "fold", {});
	const [selected, setSelected] = usePersistentState<string | null>(OWNER, "selected", null);
	return useMemo(() => ({ fold, setFold, selected, setSelected }), [fold, setFold, selected, setSelected]);
}

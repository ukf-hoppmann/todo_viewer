import { useMemo } from "react";
import { usePersistentState } from "../../core";
import type { Fold } from "./domain/tree";

const OWNER = "mindmap";

/**
 * What the user chose in the mind map, kept in the UI state of the server (owner `mindmap`): `fold` holds, by node,
 * only what differs from the default (two levels open); `selected` is the node open in the detail column;
 * `hiddenStates` are the node states the filter hides; `showUnassigned` says whether the side view "Nicht
 * zugeordnet" is on.
 */
export function useMindmapState() {
	const [fold, setFold] = usePersistentState<Fold>(OWNER, "fold", {});
	const [selected, setSelected] = usePersistentState<string | null>(OWNER, "selected", null);
	const [hiddenStates, setHiddenStates] = usePersistentState<string[]>(OWNER, "hiddenStates", []);
	const [showUnassigned, setShowUnassigned] = usePersistentState<boolean>(OWNER, "showUnassigned", true);
	return useMemo(
		() => ({ fold, setFold, selected, setSelected, hiddenStates, setHiddenStates, showUnassigned, setShowUnassigned }),
		[fold, setFold, selected, setSelected, hiddenStates, setHiddenStates, showUnassigned, setShowUnassigned],
	);
}

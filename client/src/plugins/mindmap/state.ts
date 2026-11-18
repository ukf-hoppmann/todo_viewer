import { useMemo } from "react";
import { usePersistentState } from "../../core";
import type { Fold } from "./domain/tree";
import type { ViewMode } from "./domain/tree";
import type { LayoutMode } from "./mindmapLayout";

const OWNER = "mindmap";

/**
 * What the user chose in the mind map, kept in the UI state of the server (owner `mindmap`): `fold` holds, by node,
 * only what differs from the default (two levels open); `selected` is the node open in the detail column;
 * `hiddenStates` and `hiddenMarks` are the node states and marks the filter hides; `view` is the single view or the overall view with all chosen projects, `showUnassigned` says whether the side view "Nicht
 * zugeordnet" is on.
 */
export function useMindmapState() {
	const [fold, setFold] = usePersistentState<Fold>(OWNER, "fold", {});
	const [selected, setSelected] = usePersistentState<string | null>(OWNER, "selected", null);
	const [hiddenStates, setHiddenStates] = usePersistentState<string[]>(OWNER, "hiddenStates", []);
	const [hiddenMarks, setHiddenMarks] = usePersistentState<string[]>(OWNER, "hiddenMarks", []);
	const [showUnassigned, setShowUnassigned] = usePersistentState<boolean>(OWNER, "showUnassigned", true);
	const [layout, setLayout] = usePersistentState<LayoutMode>(OWNER, "layout", "side");
	const [view, setView] = usePersistentState<ViewMode>(OWNER, "view", "single");
	return useMemo(
		() => ({ view, setView, fold, setFold, selected, setSelected, hiddenStates, setHiddenStates, hiddenMarks, setHiddenMarks, showUnassigned, setShowUnassigned, layout, setLayout }),
		[view, setView, fold, setFold, selected, setSelected, hiddenStates, setHiddenStates, hiddenMarks, setHiddenMarks, showUnassigned, setShowUnassigned, layout, setLayout],
	);
}

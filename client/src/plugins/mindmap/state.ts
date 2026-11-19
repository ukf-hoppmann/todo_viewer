import { useCallback, useMemo } from "react";
import { usePersistentState } from "../../core";
import type { Fold } from "./domain/tree";
import type { ViewMode } from "./domain/tree";
import type { LayoutMode } from "./mindmapLayout";

const OWNER = "mindmap";

/**
 * What the user chose in the mind map, kept in the UI state of the server (owner `mindmap`): `fold` holds, by node,
 * only what differs from the default (two levels open); `selected` is the node open in the detail column;
 * `hiddenStates` and `hiddenMarks` are the node states and marks the filter hides; `view` is the single view or the overall view with all chosen projects, `showUnassigned` says whether the side view "Nicht
 * zugeordnet" is on, `chosenMaps` the free map chosen per project (project uid → tree uid; none: the project tree), `showDependencies` whether the lines between topics that depend on each other are drawn (off by default), `highlightShared` whether transferred branches (a node in several trees) get a frame (off by default).
 */
export function useMindmapState() {
	const [fold, setFold] = usePersistentState<Fold>(OWNER, "fold", {});
	const [selected, setSelected] = usePersistentState<string | null>(OWNER, "selected", null);
	const [hiddenStates, setHiddenStates] = usePersistentState<string[]>(OWNER, "hiddenStates", []);
	const [hiddenMarks, setHiddenMarks] = usePersistentState<string[]>(OWNER, "hiddenMarks", []);
	const [showUnassigned, setShowUnassigned] = usePersistentState<boolean>(OWNER, "showUnassigned", true);
	const [showDependencies, setShowDependencies] = usePersistentState<boolean>(OWNER, "showDependencies", false);
	const [highlightShared, setHighlightShared] = usePersistentState<boolean>(OWNER, "highlightShared", false);
	const [layout, setLayout] = usePersistentState<LayoutMode>(OWNER, "layout", "side");
	const [view, setView] = usePersistentState<ViewMode>(OWNER, "view", "single");
	const [chosenMaps, setChosenMaps] = usePersistentState<Record<string, string>>(OWNER, "maps", {});
	// The free map chosen per project (absent: the project tree); stale entries are ignored by `chooseMap`.
	const chooseMapOf = useCallback(
		(project: string, tree: string | null) =>
			setChosenMaps((current) => {
				const rest = Object.fromEntries(Object.entries(current).filter(([key]) => key !== project));
				return tree ? { ...rest, [project]: tree } : rest;
			}),
		[setChosenMaps],
	);
	return useMemo(
		() => ({ chosenMaps, chooseMapOf, view, setView, fold, setFold, selected, setSelected, hiddenStates, setHiddenStates, hiddenMarks, setHiddenMarks, showUnassigned, setShowUnassigned, showDependencies, setShowDependencies, highlightShared, setHighlightShared, layout, setLayout }),
		[chosenMaps, chooseMapOf, view, setView, fold, setFold, selected, setSelected, hiddenStates, setHiddenStates, hiddenMarks, setHiddenMarks, showUnassigned, setShowUnassigned, showDependencies, setShowDependencies, highlightShared, setHighlightShared, layout, setLayout],
	);
}

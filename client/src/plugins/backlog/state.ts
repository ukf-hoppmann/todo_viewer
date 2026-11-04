import { useCallback, useMemo } from "react";
import { usePersistentState } from "../../core";
import { DEFAULT_HIDDEN_STATUSES } from "./constants";

const OWNER = "backlog";

/** What the user chose in the backlog, kept in the UI state of the server (owner `backlog`). */
export function useBacklogState() {
	const [hiddenStatuses, setHiddenStatuses] = usePersistentState<string[]>(OWNER, "hiddenStatuses", [...DEFAULT_HIDDEN_STATUSES]);
	const [hiddenPriorities, setHiddenPriorities] = usePersistentState<string[]>(OWNER, "hiddenPriorities", []);
	const [collapsed, setCollapsed] = usePersistentState<string[]>(OWNER, "collapsed", []);
	const [selected, setSelected] = usePersistentState<string | null>(OWNER, "selected", null);
	const [extendedMarking, setExtendedMarking] = usePersistentState<boolean>(OWNER, "extendedMarking", true);

	const expanded = useCallback((id: string) => !collapsed.includes(id), [collapsed]);
	const toggleCollapsed = useCallback(
		(id: string) => setCollapsed((current) => (current.includes(id) ? current.filter((entry) => entry !== id) : [...current, id])),
		[setCollapsed],
	);
	const setAllCollapsed = useCallback(
		(ids: readonly string[], value: boolean) =>
			setCollapsed((current) => (value ? [...new Set([...current, ...ids])] : current.filter((entry) => !ids.includes(entry)))),
		[setCollapsed],
	);
	/** Opens the given nodes, e.g. the ancestors of a row chosen in a filtered list, so the row is visible when the filter ends. */
	const expand = useCallback((ids: readonly string[]) => setCollapsed((current) => (ids.some((id) => current.includes(id)) ? current.filter((entry) => !ids.includes(entry)) : current)), [setCollapsed]);
	return useMemo(
		() => ({ hiddenStatuses, setHiddenStatuses, hiddenPriorities, setHiddenPriorities, collapsed, expanded, toggleCollapsed, setAllCollapsed, expand, selected, setSelected, extendedMarking, setExtendedMarking }),
		[hiddenStatuses, setHiddenStatuses, hiddenPriorities, setHiddenPriorities, collapsed, expanded, toggleCollapsed, setAllCollapsed, expand, selected, setSelected, extendedMarking, setExtendedMarking],
	);
}

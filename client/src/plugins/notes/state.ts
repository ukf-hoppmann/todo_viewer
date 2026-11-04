import { useCallback, useMemo } from "react";
import { usePersistentState } from "../../core";
import { DEFAULT_SHOWN_STATUSES, STATUSES } from "./constants";

const OWNER = "notes";

/** What the user chose in the notes view, kept in the UI state of the server (owner `notes`). */
export function useNotesState() {
	const [shownStatuses, setShownStatuses] = usePersistentState<string[]>(OWNER, "shownStatuses", [...DEFAULT_SHOWN_STATUSES]);
	const [collapsed, setCollapsed] = usePersistentState<string[]>(OWNER, "collapsed", []);
	const [selected, setSelected] = usePersistentState<string | null>(OWNER, "selected", null);
	const [extendedMarking, setExtendedMarking] = usePersistentState<boolean>(OWNER, "extendedMarking", true);
	const [showArchivedTopics, setShowArchivedTopics] = usePersistentState<boolean>(OWNER, "showArchivedTopics", false);

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
		() => ({
			shownStatuses: STATUSES.filter((status) => shownStatuses.includes(status)) as string[],
			setShownStatuses,
			collapsed,
			expanded,
			toggleCollapsed,
			setAllCollapsed,
			expand,
			selected,
			setSelected,
			extendedMarking,
			setExtendedMarking,
			showArchivedTopics,
			setShowArchivedTopics,
		}),
		[shownStatuses, setShownStatuses, collapsed, expanded, toggleCollapsed, setAllCollapsed, expand, selected, setSelected, extendedMarking, setExtendedMarking, showArchivedTopics, setShowArchivedTopics],
	);
}

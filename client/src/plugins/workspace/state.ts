import { useCallback, useMemo } from "react";
import { usePersistentState } from "../../core";
import { useListProjectsQuery, type Project } from "./api";

const OWNER = "workspace";

/** The search text of the sidebar; every plugin with a list filters by it. */
export function useSearchText(): [string, (text: string) => void] {
	const [text, setText] = usePersistentState<string>(OWNER, "search", "");
	return [text, setText];
}

/**
 * The projects that are shown (checkbox in the sidebar) and the one that is marked (click), kept in the UI
 * state of the server. A project nobody switched off is visible, so a new project appears at once.
 */
export function useProjectSelection() {
	const { data: projects = [] } = useListProjectsQuery();
	const [hidden, setHidden] = usePersistentState<string[]>(OWNER, "hidden", []);
	const [markedUid, setMarked] = usePersistentState<string | null>(OWNER, "marked", null);

	const visible = useMemo(() => projects.filter((project) => !hidden.includes(project.uid)), [projects, hidden]);
	const marked = useMemo(() => projects.find((project) => project.uid === markedUid), [projects, markedUid]);

	const toggleVisible = useCallback(
		(uid: string) => setHidden((current) => (current.includes(uid) ? current.filter((entry) => entry !== uid) : [...current, uid])),
		[setHidden],
	);
	const mark = useCallback((uid: string | null) => setMarked(uid), [setMarked]);
	return { projects, visible, marked, toggleVisible, mark };
}

export type { Project };

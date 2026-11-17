import { useCallback, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { viewPath } from "../../core";

/** The query parameter of the map's address that holds the node the view starts at (the focus). */
const FOCUS_PARAM = "focus";

/** The address of the map: `mindmap/main`, with `?focus=<uid>` when the view starts at a node. */
export function mapAddress(focusUid?: string | null): string {
	const path = viewPath("mindmap", "main");
	return focusUid ? `${path}?${FOCUS_PARAM}=${encodeURIComponent(focusUid)}` : path;
}

/**
 * Where the map's focus lives: in the address, so every view is reachable by URL. `focus` is the uid in the address
 * (`null` without one); `openFocus` goes to the map with that node as the root, without a uid to the whole map. The
 * page and the item actions share it; whether a focus exists in the tree is for the page to decide.
 */
export function useMapNavigation() {
	const [params] = useSearchParams();
	const navigate = useNavigate();
	const focus = params.get(FOCUS_PARAM) || null;
	const openFocus = useCallback((uid?: string | null) => void navigate(mapAddress(uid)), [navigate]);
	return useMemo(() => ({ focus, openFocus }), [focus, openFocus]);
}

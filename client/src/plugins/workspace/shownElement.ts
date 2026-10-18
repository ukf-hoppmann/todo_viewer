import { createContext, useContext } from "react";

/** The element an `ElementDetail` shows, handed to the detail view of its kind. */
export interface ShownElement {
	uid: string;
	/** The element kind, e.g. `story` or `note`. */
	kind: string;
	/** Closes the detail; the detail view puts it on its close button. */
	onClose?: () => void;
	/** Shows another element instead, e.g. a dependency the user clicked. */
	onSelect?: (uid: string) => void;
}

export const ShownElementState = createContext<ShownElement | undefined>(undefined);

/**
 * For a detail view that a plugin hangs into the slot `workspace.element-detail`: the element to show. A widget
 * gets no properties (plugin contract), so `ElementDetail` hands the element over like this.
 */
export function useShownElement(): ShownElement {
	const value = useContext(ShownElementState);
	if (!value) throw new Error("useShownElement is only available inside an ElementDetail");
	return value;
}

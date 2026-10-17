import { createContext, useContext } from "react";

/** The element whose detail panel shows the widgets of the slot `workspace.detail-sections`. */
export interface DetailElement {
	uid: string;
	label: string;
	/** The project the element belongs to. */
	projectUid: string;
}

export const DetailElementState = createContext<DetailElement | undefined>(undefined);

/**
 * For a widget that a plugin hangs into the slot `workspace.detail-sections`: the element of the detail panel it stands
 * in. A widget gets no properties (plugin contract), so the panel hands the element over like this.
 */
export function useDetailElement(): DetailElement {
	const value = useContext(DetailElementState);
	if (!value) throw new Error("useDetailElement is only available inside the detail panel of an element");
	return value;
}

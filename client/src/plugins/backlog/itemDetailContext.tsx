import { createContext, useContext } from "react";
import type { ItemOut } from "./api";

/** The item whose detail panel shows the widgets of the slot `backlog.item-detail`. */
export const ItemDetailState = createContext<ItemOut | undefined>(undefined);

/**
 * For a widget that a plugin hangs into the slot `backlog.item-detail`: the item of the detail panel it stands
 * in. A widget gets no properties (plugin contract), so the panel hands the item over like this.
 */
export function useItemDetail(): ItemOut {
	const value = useContext(ItemDetailState);
	if (!value) throw new Error("useItemDetail is only available inside the detail panel of an item");
	return value;
}

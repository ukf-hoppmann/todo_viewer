import { createContext, useContext } from "react";
import type { DropZone } from "./domain/tree";
import type { MenuAnchor } from "./NodeMenus";

/** What a node of the map can ask the page to do. `id` is the node's `uid`, for the root the project's. */
export interface MapActions {
	toggle: (id: string) => void;
	add: (id: string) => void;
	startRename: (id: string) => void;
	/** Ends the renaming of `id`: saves `title` if it is not empty and differs. */
	commitTitle: (id: string, title: string) => void;
	cancelRename: () => void;
	remove: (id: string) => void;
	/** Opens the map with the node `id` as the root of the view (the focus). */
	openAsRoot: (id: string) => void;
	/** A drag of the node `id` begins or ends. */
	dragStart: (id: string) => void;
	/** A drag of the item `uid` from the side view begins (it ends with `dragEnd`). */
	dragStartItem: (uid: string) => void;
	/** A drag of the deleted branch `uid` from the side view "Papierkorb" begins (it ends with `dragEnd`). */
	dragStartTrash: (uid: string) => void;
	dragEnd: () => void;
	/** The dragged node or item is over `id` in `zone`; true if it may be dropped there (the page then marks the place). */
	dragOver: (id: string, zone: DropZone) => boolean;
	dragLeave: (id: string) => void;
	/** Drops the dragged node on `id` in `zone`. */
	drop: (id: string, zone: DropZone) => void;
	/** Opens the menu of the node `id` (hang over, transfer, remove, delete) at `anchor`. */
	openMenu: (id: string, anchor: MenuAnchor) => void;
	/** Opens the list of the trees the node `id` stands in, to jump to one. */
	openTrees: (id: string, anchor: MenuAnchor) => void;
}

const idle = () => undefined;
export const MapActionsContext = createContext<MapActions>({ toggle: idle, add: idle, startRename: idle, commitTitle: idle, cancelRename: idle, remove: idle, openAsRoot: idle, dragStart: idle, dragStartItem: idle, dragStartTrash: idle, dragEnd: idle, dragOver: () => false, dragLeave: idle, drop: idle, openMenu: idle, openTrees: idle });

export function useMapActions(): MapActions {
	return useContext(MapActionsContext);
}

import { createContext, useContext } from "react";
import type { DropZone } from "./domain/tree";

/** What a node of the map can ask the page to do. `id` is the node's `uid`, for the root the project's. */
export interface MapActions {
	toggle: (id: string) => void;
	add: (id: string) => void;
	startRename: (id: string) => void;
	/** Ends the renaming of `id`: saves `title` if it is not empty and differs. */
	commitTitle: (id: string, title: string) => void;
	cancelRename: () => void;
	remove: (id: string) => void;
	/** A drag of the node `id` begins or ends. */
	dragStart: (id: string) => void;
	dragEnd: () => void;
	/** The dragged node is over `id` in `zone`; true if it may be dropped there (the page then marks the place). */
	dragOver: (id: string, zone: DropZone) => boolean;
	dragLeave: (id: string) => void;
	/** Drops the dragged node on `id` in `zone`. */
	drop: (id: string, zone: DropZone) => void;
}

const idle = () => undefined;
export const MapActionsContext = createContext<MapActions>({ toggle: idle, add: idle, startRename: idle, commitTitle: idle, cancelRename: idle, remove: idle, dragStart: idle, dragEnd: idle, dragOver: () => false, dragLeave: idle, drop: idle });

export function useMapActions(): MapActions {
	return useContext(MapActionsContext);
}

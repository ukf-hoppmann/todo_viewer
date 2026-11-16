import { createContext, useContext } from "react";

/** What a node of the map can ask the page to do. `id` is the node's `uid`, for the root the project's. */
export interface MapActions {
	toggle: (id: string) => void;
	add: (id: string) => void;
	startRename: (id: string) => void;
	/** Ends the renaming of `id`: saves `title` if it is not empty and differs. */
	commitTitle: (id: string, title: string) => void;
	cancelRename: () => void;
	remove: (id: string) => void;
}

const idle = () => undefined;
export const MapActionsContext = createContext<MapActions>({ toggle: idle, add: idle, startRename: idle, commitTitle: idle, cancelRename: idle, remove: idle });

export function useMapActions(): MapActions {
	return useContext(MapActionsContext);
}

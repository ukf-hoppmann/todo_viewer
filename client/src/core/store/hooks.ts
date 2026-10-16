import { useDispatch, useSelector } from "react-redux";
import type { AppState, AppStore } from "./createAppStore";

/**
 * Dispatches actions to the store. A plugin dispatches only its own actions
 * and those the owner of another compartment exports (architecture rule 5.1).
 */
export const useAppDispatch = useDispatch.withTypes<AppStore["dispatch"]>();

/**
 * Selects from the whole state. The core does not know the plugins, so a
 * plugin writes selectors that start at `state["<its id>"]` and narrows the
 * type itself.
 */
export const useAppSelector = useSelector.withTypes<AppState>();

import { modals } from "./modals";
import type { Modals } from "./types";

/** The central dialog object `modals`, for use in components. */
export function useModals(): Modals {
	return modals;
}

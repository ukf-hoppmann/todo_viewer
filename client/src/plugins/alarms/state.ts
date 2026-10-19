import { usePersistentState } from "../../core";

/** The reminder open in the detail column of the alarms view, kept in the UI state of the server (owner `alarms`). */
export function useOpenAlarm() {
	return usePersistentState<string | null>("alarms", "selected", null);
}

// While a dialog is open or a field is being edited, polling pauses so inputs stay stable.
import { useEffect, useSyncExternalStore } from "react";

let holders = 0;
const listeners = new Set<() => void>();

function change(delta: number) {
  holders += delta;
  listeners.forEach((l) => l());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function usePollingPaused(): boolean {
  return useSyncExternalStore(subscribe, () => holders > 0);
}

/** Pauses polling for as long as `active` is true and the component is mounted. */
export function usePausePolling(active: boolean): void {
  useEffect(() => {
    if (!active) return;
    change(1);
    return () => change(-1);
  }, [active]);
}

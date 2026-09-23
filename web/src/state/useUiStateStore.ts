import { createContext, useContext, useEffect, useReducer, useRef } from "react";
import { fetchUiState, saveUiState } from "../api/queries";
import { INITIAL_UI_STATE, snapshot, type UiAction, type UiState, uiReducer } from "./uiState";

const LOCAL_KEY = "todoViewerState";
const SAVE_DELAY_MS = 300;

function readLocal(): unknown {
  try {
    return JSON.parse(localStorage.getItem(LOCAL_KEY) ?? "null");
  } catch {
    return null;
  }
}

/**
 * The server (configs/ui_state.json) is the source of truth. localStorage is only a
 * cache so the UI starts without flicker before the server answers.
 */
export function useUiStateStore(): [UiState, (action: UiAction) => void] {
  const [state, dispatch] = useReducer(uiReducer, INITIAL_UI_STATE, (s) => uiReducer(s, { type: "load", stored: readLocal() }));
  const hydrated = useRef(false);

  useEffect(() => {
    let cancelled = false;
    fetchUiState()
      .then((stored) => !cancelled && dispatch({ type: "load", stored }))
      .catch(() => undefined) // server unreachable: the local cache stays valid
      .finally(() => {
        hydrated.current = true;
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const data = snapshot(state);
    try {
      localStorage.setItem(LOCAL_KEY, JSON.stringify(data));
    } catch {
      // storage unavailable
    }
    if (!hydrated.current) return;
    const timer = setTimeout(() => saveUiState(data).catch(() => undefined), SAVE_DELAY_MS);
    return () => clearTimeout(timer);
  }, [state]);

  return [state, dispatch];
}

export const UiStateContext = createContext<{ state: UiState; dispatch: (a: UiAction) => void }>({
  state: INITIAL_UI_STATE,
  dispatch: () => undefined,
});

export function useUiState() {
  return useContext(UiStateContext);
}

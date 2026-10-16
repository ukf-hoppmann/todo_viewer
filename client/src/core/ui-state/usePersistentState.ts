import { useCallback, useEffect, useRef } from "react";
import { useStore } from "react-redux";
import type { AppStore } from "../store/createAppStore";
import { useGetUiStateQuery } from "./coreApi";
import { setUiStateValue } from "./uiState";

export type PersistentSetter<T> = (value: T | ((previous: T) => T)) => void;

/**
 * A value that outlives the page, kept in the UI state of the server (`/api/core/ui-state/{owner}`) and not
 * in the storage of the browser. `owner` is `core` or the plugin id, `key` names the value in the owner's
 * document. Until the document is loaded (or when it holds no value yet) the default is returned; `loaded`
 * tells which. The setter takes a value or a function of the previous value; the new value is visible
 * everywhere at once and reaches the server a moment later.
 */
export function usePersistentState<T>(owner: string, key: string, defaultValue: T): [T, PersistentSetter<T>, boolean] {
	const store = useStore.withTypes<AppStore>()();
	const { data } = useGetUiStateQuery(owner);
	const stored = data?.document[key];
	const value = (stored === undefined ? defaultValue : stored) as T;

	// The setter must see the latest value without changing identity at each change.
	const latest = useRef(value);
	useEffect(() => {
		latest.current = value;
	}, [value]);

	const set = useCallback<PersistentSetter<T>>(
		(next) => {
			const resolved = typeof next === "function" ? (next as (previous: T) => T)(latest.current) : next;
			latest.current = resolved;
			void setUiStateValue(store, owner, key, resolved);
		},
		[store, owner, key],
	);

	return [value, set, data !== undefined];
}

import type { AppState, AppStore } from "../store/createAppStore";
import { coreApi, type UiStateDocument } from "./coreApi";

/** Time the writes of one owner are collected before the document is sent. */
export const uiStateWriteDelayMs = 300;

/** What the UI state needs of the store. */
export type UiStateStore = Pick<AppStore, "dispatch" | "getState">;

const timers = new Map<string, ReturnType<typeof setTimeout>>();

/** The document of the owner as the cache holds it, or nothing if it is not loaded yet. */
export function selectUiDocument(state: AppState, owner: string): UiStateDocument | undefined {
	return coreApi.endpoints.getUiState.select(owner)(state as never).data?.document;
}

function send(store: UiStateStore, owner: string): Promise<unknown> {
	const document = selectUiDocument(store.getState(), owner);
	if (!document) return Promise.resolve();
	return store.dispatch(coreApi.endpoints.putUiState.initiate({ owner, document }) as never) as unknown as Promise<unknown>;
}

/** Loads the owner's document into the cache, if it is not there yet; false if that failed. */
async function ensureLoaded(store: UiStateStore, owner: string): Promise<boolean> {
	if (selectUiDocument(store.getState(), owner)) return true;
	const request = store.dispatch(coreApi.endpoints.getUiState.initiate(owner) as never) as unknown as Promise<{ isError: boolean }> & {
		unsubscribe: () => void;
	};
	const result = await request;
	request.unsubscribe();
	return !result.isError;
}

/**
 * Sets one key of the owner's document: the cache changes at once (every reader sees the new value), the
 * whole document goes to the server after a short delay, one request for a burst of changes. The document
 * is loaded first if it is not in the cache yet, so that a write never replaces what the server holds.
 */
export async function setUiStateValue(store: UiStateStore, owner: string, key: string, value: unknown): Promise<void> {
	if (!(await ensureLoaded(store, owner))) return;
	store.dispatch(
		coreApi.util.updateQueryData("getUiState", owner, (draft) => {
			draft.document[key] = value;
		}) as never,
	);
	clearTimeout(timers.get(owner));
	timers.set(
		owner,
		setTimeout(() => {
			timers.delete(owner);
			void send(store, owner);
		}, uiStateWriteDelayMs),
	);
}

/** Sends what is still waiting, at once (before the page closes, and in tests). */
export async function flushUiState(store: UiStateStore, owner?: string): Promise<void> {
	const owners = owner ? [owner] : [...timers.keys()];
	await Promise.all(
		owners.map((name) => {
			if (!timers.has(name)) return Promise.resolve();
			clearTimeout(timers.get(name));
			timers.delete(name);
			return send(store, name);
		}),
	);
}

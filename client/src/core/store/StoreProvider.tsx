import type { ReactNode } from "react";
import { Provider } from "react-redux";
import type { AppStore } from "./createAppStore";

interface StoreProviderProps {
	store: AppStore;
	children: ReactNode;
}

/** Provides the store created by `src/app` to the components below. */
export function StoreProvider({ store, children }: StoreProviderProps) {
	return <Provider store={store}>{children}</Provider>;
}

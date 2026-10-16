import { createContext, type ReactNode } from "react";

export interface PageHeaderContextValue {
	/** Whether the main route asked for a header (`layout.header`). */
	enabled: boolean;
	/** Sets the content of the header; `undefined` empties it. */
	set: (content: ReactNode) => void;
}

/** Provided by `SubLayout`; missing for a page that is shown outside of one. */
export const PageHeaderContext = createContext<PageHeaderContextValue | undefined>(undefined);

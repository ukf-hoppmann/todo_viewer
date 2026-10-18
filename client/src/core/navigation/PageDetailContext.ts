import { createContext, type ReactNode } from "react";

export interface PageDetailContextValue {
	/** Whether the main route asked for a detail column (`layout.detail`). */
	enabled: boolean;
	/** Sets the content of the detail column; `undefined` empties and hides it. */
	set: (content: ReactNode) => void;
}

/** Provided by `SubLayout`; missing for a page that is shown outside of one. */
export const PageDetailContext = createContext<PageDetailContextValue | undefined>(undefined);

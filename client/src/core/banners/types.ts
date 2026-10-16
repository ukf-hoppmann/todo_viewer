import type { Text } from "../modals/text";

export type BannerSeverity = "error" | "warning" | "info" | "success";

/** A button in a banner. */
export interface BannerAction {
	label: Text;
	/** What the button does; may be asynchronous. It gets the handle of its banner. */
	onClick(banner: BannerHandle): void | Promise<void>;
	/** Default `false`: the banner closes after the click. */
	keepOpen?: boolean;
}

export interface BannerRequest {
	/** Default `info`. */
	severity?: BannerSeverity;
	/** Without it: no title. */
	title?: Text;
	message: Text;
	actions?: BannerAction[];
	/** Default `true`: a small X at the top right closes the banner. */
	dismissible?: boolean;
	/** Without it the banner stays until it is closed. */
	autoHideMs?: number;
}

/** What `show` returns: lets the code that showed the banner change or close it. */
export interface BannerHandle {
	/** Changes only the fields named in `patch`; has no effect once the banner is closed. */
	update(patch: Partial<BannerRequest>): void;
	/** May be called more than once. */
	close(): void;
}

/** A banner as the display gets it. */
export interface VisibleBanner {
	id: number;
	request: BannerRequest;
	handle: BannerHandle;
}

/** What the app config says about banners (section `banners`). */
export interface BannerSettings {
	/** How many banners are visible at the same time; the others wait. Default 20. */
	maxVisible?: number;
}

export interface Banners {
	show(request: BannerRequest): BannerHandle;
	/** Closes all banners, visible and waiting; their handles behave as closed afterwards. */
	clear(): void;
	/** Applies the settings from the app config; called once at the start. A banner that is visible stays. */
	configure(settings: BannerSettings): void;
	/** For the display (`useSyncExternalStore`). */
	subscribe(listener: () => void): () => void;
	/** The banners to show, oldest first; the same list until something changes. */
	getSnapshot(): readonly VisibleBanner[];
}

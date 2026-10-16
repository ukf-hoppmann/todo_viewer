import type { BannerHandle, BannerRequest, Banners, VisibleBanner } from "./types";

/** How many banners are visible at the same time unless the app config says otherwise. */
const DEFAULT_MAX_VISIBLE = 20;

interface Entry {
	id: number;
	request: BannerRequest;
	closed: boolean;
	/** Banners over the limit wait invisibly; a visible one stays visible. */
	visible: boolean;
	/** Runs while a visible banner has `autoHideMs`. */
	timer?: ReturnType<typeof setTimeout>;
	handle: BannerHandle;
}

/**
 * Creates an independent list of banners. The core uses one instance
 * (`banners`); tests create their own. It is not bound to React: anything can
 * show banners, the display (`BannerHost`) shows them.
 */
export function createBanners(): Banners {
	let entries: Entry[] = [];
	let snapshot: readonly VisibleBanner[] = [];
	let maxVisible = DEFAULT_MAX_VISIBLE;
	let nextId = 1;
	const listeners = new Set<() => void>();

	const stopTimer = (entry: Entry) => {
		clearTimeout(entry.timer);
		entry.timer = undefined;
	};

	/** (Re)starts the time of a visible banner that has one; a waiting banner starts it when it becomes visible. */
	const startTimer = (entry: Entry) => {
		stopTimer(entry);
		const time = entry.request.autoHideMs;
		if (!entry.visible || time === undefined || !(time > 0)) return;
		entry.timer = setTimeout(() => entry.handle.close(), time);
	};

	/** Lets the oldest waiting banners become visible as long as there is room. */
	const promote = () => {
		let visible = entries.filter((entry) => entry.visible).length;
		for (const entry of entries) {
			if (visible >= maxVisible) break;
			if (!entry.visible) {
				entry.visible = true;
				visible++;
				startTimer(entry);
			}
		}
	};

	const publish = () => {
		snapshot = entries.filter((entry) => entry.visible).map(({ id, request, handle }) => ({ id, request, handle }));
		listeners.forEach((listener) => listener());
	};

	return {
		show(request) {
			const entry: Entry = {
				id: nextId++,
				request,
				closed: false,
				visible: false,
				handle: {
					update(patch) {
						if (entry.closed) return;
						entry.request = { ...entry.request, ...patch };
						// Only a change of the time starts it again.
						if ("autoHideMs" in patch) startTimer(entry);
						publish();
					},
					close() {
						if (entry.closed) return;
						entry.closed = true;
						stopTimer(entry);
						entries = entries.filter((other) => other !== entry);
						promote();
						publish();
					},
				},
			};
			entries = [...entries, entry];
			promote();
			publish();
			return entry.handle;
		},

		clear() {
			if (entries.length === 0) return;
			for (const entry of entries) {
				entry.closed = true;
				stopTimer(entry);
			}
			entries = [];
			publish();
		},

		configure(settings) {
			const limit = settings.maxVisible;
			if (limit === undefined || !Number.isInteger(limit) || limit < 1) return;
			maxVisible = limit;
			promote();
			publish();
		},

		subscribe(listener) {
			listeners.add(listener);
			return () => {
				listeners.delete(listener);
			};
		},

		getSnapshot: () => snapshot,
	};
}

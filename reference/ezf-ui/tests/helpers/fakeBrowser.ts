import { vi } from "vitest";
import type { BrowserLocation } from "../../src/core/auth/types";

/** A storage in memory with the part of `Storage` the core uses. */
export function fakeStorage(initial: Record<string, string> = {}) {
	const items = new Map(Object.entries(initial));
	return {
		items,
		getItem: (key: string) => items.get(key) ?? null,
		setItem: (key: string, value: string) => {
			items.set(key, value);
		},
		removeItem: (key: string) => {
			items.delete(key);
		},
	};
}

/** The address bar as the core sees it: the current address and the two ways to leave. */
export function fakeLocation(current = "/") {
	return { current: () => current, assign: vi.fn<(url: string) => void>(), replace: vi.fn<(url: string) => void>() } satisfies BrowserLocation;
}

import { vi } from "vitest";

type Listener = (event: { matches: boolean }) => void;

/**
 * The color scheme the operating system asks for: installs `window.matchMedia` (jsdom has none) and lets the
 * test change the setting. The test removes it again with `vi.unstubAllGlobals()`.
 */
export function fakeSystemColorScheme(initial: "light" | "dark") {
	let dark = initial === "dark";
	const listeners = new Set<Listener>();

	vi.stubGlobal(
		"matchMedia",
		vi.fn((media: string) => ({
			media,
			get matches() {
				return dark;
			},
			// The deprecated pair is the one MUI uses.
			addListener: (listener: Listener) => listeners.add(listener),
			removeListener: (listener: Listener) => listeners.delete(listener),
			addEventListener: (_type: string, listener: Listener) => listeners.add(listener),
			removeEventListener: (_type: string, listener: Listener) => listeners.delete(listener),
		})),
	);

	return {
		/** The user changes the setting of the operating system. */
		set(next: "light" | "dark") {
			dark = next === "dark";
			for (const listener of [...listeners]) listener({ matches: dark });
		},
	};
}

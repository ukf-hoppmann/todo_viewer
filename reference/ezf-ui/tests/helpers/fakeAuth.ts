import { vi } from "vitest";
import type { Auth, AuthState } from "../../src/core/auth/types";

/** A login in memory: the state is set by the test, `login` and `logout` are spies. */
export function fakeAuth(initial: AuthState = "authenticated") {
	let state = initial;
	const listeners = new Set<() => void>();
	const set = (next: AuthState) => {
		if (state === next) return;
		state = next;
		for (const listener of [...listeners]) listener();
	};

	const auth: Auth & { login: ReturnType<typeof vi.fn<() => Promise<void>>>; logout: ReturnType<typeof vi.fn<() => Promise<void>>> } = {
		getState: () => state,
		subscribe(listener) {
			listeners.add(listener);
			return () => {
				listeners.delete(listener);
			};
		},
		check: async () => state,
		login: vi.fn<() => Promise<void>>(async () => {}),
		logout: vi.fn<() => Promise<void>>(async () => {}),
		unauthorized: () => set("unauthenticated"),
	};
	return auth;
}

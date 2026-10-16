import { failureKindOfStatus } from "../backend/classifyFailure";
import { errors as defaultErrors } from "../errors/errors";
import type { Errors } from "../errors/types";
import { AuthCheckError } from "./AuthCheckError";
import { clearReturnTo, saveReturnTo, tabStorage } from "./returnTo";
import type { Auth, AuthState, BrowserLocation, CheckOptions, StorageLike } from "./types";

export interface CreateAuthOptions {
	/** Complete address of the backend (`api.url`). */
	url: string;
	/** The global `fetch` by default. */
	fetch?: (url: string, init: RequestInit) => Promise<Response>;
	/** Where failures of `login` and `logout` are reported; the central `errors` by default. */
	errors?: Errors;
	/** The address bar of the browser by default. */
	location?: BrowserLocation;
	/** The `sessionStorage` of the tab by default. */
	storage?: StorageLike;
	now?: () => number;
}

const browserLocation: BrowserLocation = {
	current: () => `${globalThis.location.pathname}${globalThis.location.search}${globalThis.location.hash}`,
	assign: (url) => globalThis.location.assign(url),
	replace: (url) => globalThis.location.replace(url),
};

/** Creates the login of the application; `src/app` does this once and hands it on. */
export function createAuth({
	url,
	fetch = (input, init) => globalThis.fetch(input, init),
	errors = defaultErrors,
	location = browserLocation,
	storage = tabStorage(),
	now = Date.now,
}: CreateAuthOptions): Auth {
	let state: AuthState = "unknown";
	const listeners = new Set<() => void>();

	const setState = (next: AuthState) => {
		if (state === next) return;
		state = next;
		for (const listener of [...listeners]) listener();
	};

	/** `GET <url>/<endpoint>` with the cookies; anything but a 2xx answer is an error. */
	const get = async (endpoint: string): Promise<Response> => {
		const response = await fetch(`${url}/${endpoint}`, { credentials: "include" });
		if (!response.ok) throw new Error(`/${endpoint} answered with HTTP status ${response.status}`);
		return response;
	};

	/** The endpoints for the Keycloak addresses answer a JSON text. */
	const getAddress = async (endpoint: string): Promise<string> => {
		const address: unknown = await (await get(endpoint)).json();
		if (typeof address !== "string" || address === "") throw new Error(`/${endpoint} did not answer an address`);
		return address;
	};

	const report = (key: string, action: string, error: unknown) =>
		void errors.forOrigin("core")({ userMessage: { key }, action, error });

	return {
		getState: () => state,

		subscribe(listener) {
			listeners.add(listener);
			return () => {
				listeners.delete(listener);
			};
		},

		async check({ timeoutMs }: CheckOptions = {}) {
			const controller = timeoutMs === undefined ? undefined : new AbortController();
			const timer = controller && setTimeout(() => controller.abort(), timeoutMs);
			let response: Response;
			try {
				response = await fetch(`${url}/isAuthenticated`, { credentials: "include", ...(controller && { signal: controller.signal }) });
			} catch (cause) {
				throw new AuthCheckError("unreachable", "the backend could not be requested", cause);
			} finally {
				clearTimeout(timer);
			}
			if (response.status === 200) setState("authenticated");
			else if (failureKindOfStatus(response.status) === "unauthorized") setState("unauthenticated");
			else throw new AuthCheckError("unexpected", `/isAuthenticated answered with HTTP status ${response.status}`);
			return state;
		},

		async login() {
			saveReturnTo(storage, location.current(), now());
			try {
				location.assign(await getAddress("getLoginUrl"));
			} catch (error) {
				clearReturnTo(storage);
				report("auth.loginFailed", "login", error);
			}
		},

		async logout() {
			try {
				const address = await getAddress("getLogoutUrl");
				// Waited for, so that leaving the page does not cancel the request.
				await get("getlogout");
				location.replace(address);
			} catch (error) {
				report("auth.logoutFailed", "logout", error);
			}
		},

		unauthorized() {
			setState("unauthenticated");
		},
	};
}

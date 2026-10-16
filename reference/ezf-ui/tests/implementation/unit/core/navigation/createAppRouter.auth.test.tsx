import { act, cleanup, render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { RouterProvider } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, coreTestIds, initI18n, PluginRegistryProvider, type AuthState } from "../../../../../src/core";
import { createAppRouter, type AppRouterOptions } from "../../../../../src/core/navigation/createAppRouter";
import type { ActivePlugin, Contribution, PluginRegistry } from "../../../../../src/core/plugins/types";
import { fakeAuth } from "../../../../helpers/fakeAuth";

const icon = () => null;
const i18n = { de: {}, en: {}, fr: {} };

function tab(name: string): Contribution {
	return { slot: "core.main", name, title: `tab.${name}`, icon, page: async () => ({ default: () => <p>{`Seite ${name}`}</p> }) };
}

const active: ActivePlugin[] = [{ id: "example", definition: { i18n, contributions: [tab("overview"), tab("details")] } }];
const registry: PluginRegistry = { active: () => active, statuses: () => active.map(({ id }) => ({ id, status: "active" as const })) };

async function renderRouter(path: string, state: AuthState, options: Partial<AppRouterOptions> = {}) {
	const lng = await initI18n({ lng: "de" });
	lng.addResourceBundle("de", "example", { "tab.overview": "Übersicht", "tab.details": "Details" });
	const auth = fakeAuth(state);
	const router = createAppRouter({ registry, initialEntries: [path], ...options });
	render(
		<I18nextProvider i18n={lng}>
			<AuthProvider auth={auth}>
				<PluginRegistryProvider registry={registry}>
					<RouterProvider router={router} />
				</PluginRegistryProvider>
			</AuthProvider>
		</I18nextProvider>,
	);
	return { router, auth };
}

describe("createAppRouter: the guard around all views", () => {
	afterEach(cleanup);

	it("shows the frame and the view when the user is logged in", async () => {
		await renderRouter("/example/overview", "authenticated");

		expect(await screen.findByText("Seite overview")).toBeTruthy();
		expect(screen.getByTestId(coreTestIds.rootLayout)).toBeTruthy();
		expect(screen.queryByTestId(coreTestIds.loginPage)).toBeNull();
	});

	it.each(["/", "/example/overview", "/example/details?x=1", "/example/gone", "/nowhere/at/all", "/dev/core/dialogs"])(
		"shows only the login page for %s when the user is not logged in, and the address stays",
		async (path) => {
			const devRoutes = [{ ownerId: "core", name: "dialogs", load: async () => ({ default: () => <p>Entwicklungsseite</p> }) }];
			const { router } = await renderRouter(path, "unauthenticated", { devRoutes });

			expect(await screen.findByTestId(coreTestIds.loginPage)).toBeTruthy();
			expect(screen.queryByTestId(coreTestIds.tabBar)).toBeNull();
			expect(screen.queryByText("Seite overview")).toBeNull();
			expect(screen.queryByText("Entwicklungsseite")).toBeNull();
			const { pathname, search } = router.state.location;
			expect(`${pathname}${search}`).toBe(path);
		},
	);

	it("replaces the frame by the login page when a request reports 401 or 407 during the work, and the address stays", async () => {
		const { router, auth } = await renderRouter("/example/details", "authenticated");
		expect(await screen.findByText("Seite details")).toBeTruthy();

		act(() => auth.unauthorized());

		expect(await screen.findByTestId(coreTestIds.loginPage)).toBeTruthy();
		expect(screen.queryByTestId(coreTestIds.tabBar)).toBeNull();
		expect(router.state.location.pathname).toBe("/example/details");
	});
});

describe("createAppRouter: return to the address from before the login", () => {
	afterEach(() => {
		cleanup();
		window.history.replaceState(null, "", "/");
	});

	it("asks for the address once, and tells whether a path leads to an available view", async () => {
		const returnTo = vi.fn<NonNullable<AppRouterOptions["returnTo"]>>(() => undefined);

		await renderRouter("/", "authenticated", { returnTo });

		expect(returnTo).toHaveBeenCalledOnce();
		const isAvailable = returnTo.mock.calls[0]![0];
		expect(isAvailable("/example/details")).toBe(true);
		expect(isAvailable("/example/gone")).toBe(false);
		expect(isAvailable("/nowhere/at/all")).toBe(false);
		expect(isAvailable("/")).toBe(false);
	});

	it("starts at the returned address, with query and fragment, instead of the start view", async () => {
		const { router } = await renderRouter("/", "authenticated", { returnTo: () => "/example/details?tab=lab#top" });

		expect(await screen.findByText("Seite details")).toBeTruthy();
		expect(router.state.location).toMatchObject({ pathname: "/example/details", search: "?tab=lab", hash: "#top" });
	});

	it("replaces the opened address: there is no entry for it to go back to", async () => {
		const { router } = await renderRouter("/example/overview", "authenticated", { returnTo: () => "/example/details" });

		expect(await screen.findByText("Seite details")).toBeTruthy();
		expect(router.state.historyAction).toBe("POP");
		expect(router.state.location.pathname).toBe("/example/details");
	});

	it("starts at the start view when nothing is returned", async () => {
		const { router } = await renderRouter("/", "authenticated", { returnTo: () => undefined });

		expect(await screen.findByText("Seite overview")).toBeTruthy();
		expect(router.state.location.pathname).toBe("/example/overview");
	});

	it("puts the returned address into the address bar of the browser before the router starts", () => {
		const router = createAppRouter({ registry, returnTo: () => "/example/details?tab=lab" });

		try {
			expect(`${window.location.pathname}${window.location.search}`).toBe("/example/details?tab=lab");
			expect(router.state.location.pathname).toBe("/example/details");
		} finally {
			router.dispose();
		}
	});
});

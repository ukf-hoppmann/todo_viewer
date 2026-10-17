import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ComponentType } from "react";
import { I18nextProvider } from "react-i18next";
import { RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { coreTestIds, initI18n, PluginRegistryProvider } from "../../../../../../client/src/core";
import { logging } from "../../../../../../client/src/core/logging/logging";
import { MemorySink } from "../../../../../../client/src/core/logging/MemorySink";
import type { Logger } from "../../../../../../client/src/core/logging/types";
import { createAppRouter, type AppRouterOptions } from "../../../../../../client/src/core/navigation/createAppRouter";
import { usePageHeader } from "../../../../../../client/src/core/navigation/usePageHeader";
import type { ActivePlugin, Contribution, PluginRegistry, PluginStatus } from "../../../../../../client/src/core/plugins/types";

const i18n = { de: {}, en: {} };
const icon = () => null;

type Loader = () => Promise<{ default: ComponentType }>;

function pageOf(text: string): Loader {
	return async () => ({ default: () => <p>{text}</p> });
}

function tab(name: string, load: Loader = pageOf(`Seite ${name}`), layout?: { header?: boolean }): Contribution {
	return { slot: "core.main", name, title: `tab.${name}`, icon, page: load, ...(layout ? { layout } : {}) };
}

function plugin(id: string, ...contributions: Contribution[]): ActivePlugin {
	return { id, definition: { i18n, contributions } };
}

function registryOf(active: ActivePlugin[], others: PluginStatus[] = []): PluginRegistry {
	const statuses = [...active.map(({ id }): PluginStatus => ({ id, status: "active" })), ...others];
	return { active: () => active, statuses: () => statuses };
}

const sink = new MemorySink("create-app-router-test");

async function renderRouter(registry: PluginRegistry, path: string, options: Partial<AppRouterOptions> = {}) {
	const lng = await initI18n({ lng: "en" });
	lng.addResourceBundle("en", "example", { "tab.overview": "Overview", "tab.details": "Details", "tab.hub": "Hub" });
	const router = createAppRouter({ registry, initialEntries: [path], ...options });
	render(
		<I18nextProvider i18n={lng}>
				<PluginRegistryProvider registry={registry}>
					<RouterProvider router={router} />
				</PluginRegistryProvider>
		</I18nextProvider>,
	);
	return { router };
}

function warnings(): string[] {
	return sink.entries.filter((entry) => entry.level === "warn").map((entry) => entry.message ?? "");
}

describe("createAppRouter", () => {
	beforeEach(() => {
		logging.addSink(sink, { level: "debug" });
	});

	afterEach(() => {
		cleanup();
		logging.removeSink(sink.name);
		sink.entries.length = 0;
		vi.restoreAllMocks();
	});

	describe("views of active plugins", () => {
		const example = plugin("example", tab("overview"), tab("details"));

		it("shows the tabs of the active plugin and the page under its URL", async () => {
			await renderRouter(registryOf([example]), "/example/details");

			expect(await screen.findByText("Seite details")).toBeTruthy();
			expect(screen.getByTestId(coreTestIds.navTab("example", "overview")).textContent).toBe("Overview");
			expect(screen.getByTestId(coreTestIds.navTab("example", "details")).getAttribute("aria-selected")).toBe("true");
		});

		it("builds the same view from the URL alone, as after a reload", async () => {
			await renderRouter(registryOf([example]), "/example/overview");

			expect(await screen.findByText("Seite overview")).toBeTruthy();
			expect(screen.getByTestId(coreTestIds.navTab("example", "overview")).getAttribute("aria-selected")).toBe("true");
		});

		it("goes to another page when its tab is clicked", async () => {
			const { router } = await renderRouter(registryOf([example]), "/example/overview");
			await screen.findByText("Seite overview");

			fireEvent.click(screen.getByTestId(coreTestIds.navTab("example", "details")));

			expect(await screen.findByText("Seite details")).toBeTruthy();
			expect(router.state.location.pathname).toBe("/example/details");
		});

		it("keeps every view below one common node", async () => {
			const { router } = await renderRouter(registryOf([example]), "/example/overview");

			expect(router.routes).toHaveLength(1);
		});

		it("lets two owners use the same name", async () => {
			const registry = registryOf([plugin("alpha", tab("overview")), plugin("beta", tab("overview"))]);
			await renderRouter(registry, "/beta/overview");

			expect(await screen.findByText("Seite overview")).toBeTruthy();
			expect(screen.getByTestId(coreTestIds.navTab("beta", "overview")).getAttribute("aria-selected")).toBe("true");
			expect(screen.getByTestId(coreTestIds.navTab("alpha", "overview")).getAttribute("aria-selected")).toBe("false");
		});

		it("shows the tabs of the core as well, behind those of the plugins", async () => {
			await renderRouter(registryOf([example]), "/core/patients", { coreContributions: [tab("patients")] });

			expect(await screen.findByText("Seite patients")).toBeTruthy();
			expect(screen.getAllByRole("tab").at(-1)?.getAttribute("data-testid")).toBe(coreTestIds.navTab("core", "patients"));
		});

		it("refuses a contribution of the core that uses a reserved name", () => {
			expect(() => createAppRouter({ registry: registryOf([]), coreContributions: [tab("link")] })).toThrow(/reserved/);
		});
	});

	describe("pages that cannot be shown", () => {
		const example = plugin("example", tab("overview"));

		it("shows 'not available' for a plugin that is switched off, with no tab, and logs it at info level", async () => {
			const registry = registryOf([example], [{ id: "off", status: "disabled" }]);
			await renderRouter(registry, "/off/overview");

			expect(await screen.findByTestId(coreTestIds.unavailable)).toBeTruthy();
			expect(screen.getAllByRole("tab")).toHaveLength(1);
			expect(sink.entries.filter((entry) => entry.level === "info")).toEqual([expect.objectContaining({ data: { path: "/off/overview" } })]);
		});

		it("shows 'not available' for a failed plugin without a new log entry", async () => {
			const registry = registryOf([example], [{ id: "bad", status: "failed", code: "import-failed" }]);
			await renderRouter(registry, "/bad/overview");

			expect(await screen.findByTestId(coreTestIds.unavailable)).toBeTruthy();
			expect(sink.entries).toHaveLength(0);
		});

		it("shows 'does not exist' for an unknown owner and for an unknown view of an active plugin", async () => {
			await renderRouter(registryOf([example]), "/ghost/overview");
			expect(await screen.findByTestId(coreTestIds.notFound)).toBeTruthy();

			cleanup();
			await renderRouter(registryOf([example]), "/example/missing");
			expect(await screen.findByTestId(coreTestIds.notFound)).toBeTruthy();
		});

		it("keeps the tabs usable next to the notice", async () => {
			const { router } = await renderRouter(registryOf([example]), "/ghost/overview");
			await screen.findByTestId(coreTestIds.notFound);

			fireEvent.click(screen.getByTestId(coreTestIds.navTab("example", "overview")));

			expect(await screen.findByText("Seite overview")).toBeTruthy();
			expect(router.state.location.pathname).toBe("/example/overview");
		});

		it("goes to the start page from the notice", async () => {
			const { router } = await renderRouter(registryOf([example]), "/ghost/overview");
			await screen.findByTestId(coreTestIds.notFound);

			fireEvent.click(screen.getByTestId(coreTestIds.homeButton));

			expect(await screen.findByText("Seite overview")).toBeTruthy();
			expect(router.state.location.pathname).toBe("/example/overview");
		});

		it("replaces only the page when its import fails; the tabs stay usable", async () => {
			vi.spyOn(console, "error").mockImplementation(() => undefined);
			const broken = plugin("example", tab("overview", () => Promise.reject(new Error("chunk fehlt"))), tab("details"));
			await renderRouter(registryOf([broken]), "/example/overview");

			expect(await screen.findByTestId(coreTestIds.errorFallback)).toBeTruthy();
			fireEvent.click(screen.getByTestId(coreTestIds.navTab("example", "details")));

			expect(await screen.findByText("Seite details")).toBeTruthy();
			expect(screen.queryByTestId(coreTestIds.errorFallback)).toBeNull();
		});
	});

	describe("order and start view", () => {
		const registry = registryOf([plugin("alpha", tab("a1")), plugin("beta", tab("b1"))]);

		function tabIds() {
			return screen.getAllByRole("tab").map((element) => element.getAttribute("data-testid"));
		}

		it("leads / to the first tab and replaces the entry in the history", async () => {
			const { router } = await renderRouter(registry, "/");

			expect(await screen.findByText("Seite a1")).toBeTruthy();
			expect(router.state.location.pathname).toBe("/alpha/a1");
			expect(router.state.historyAction).toBe("REPLACE");
		});

		it("does not keep query parameters when it leads on", async () => {
			const { router } = await renderRouter(registry, "/?filter=1");
			await screen.findByText("Seite a1");

			expect(router.state.location.search).toBe("");
		});

		it("leads / to the start view of the config", async () => {
			await renderRouter(registry, "/", { navigation: { start: "beta/b1" } });

			expect(await screen.findByText("Seite b1")).toBeTruthy();
		});

		it("falls back to the first tab and warns in development when the start view is not available", async () => {
			await renderRouter(registry, "/", { navigation: { start: "ghost/view" } });

			expect(await screen.findByText("Seite a1")).toBeTruthy();
			expect(warnings()).toEqual([expect.stringContaining("ghost/view")]);
		});

		it("orders the tabs by the list in the config and the rest by the fixed rule", async () => {
			await renderRouter(registry, "/alpha/a1", { navigation: { "core.main": ["beta/b1"] } });
			await screen.findByText("Seite a1");

			expect(tabIds()).toEqual([coreTestIds.navTab("beta", "b1"), coreTestIds.navTab("alpha", "a1")]);
		});

		it("skips unknown entries of the list and warns in development", async () => {
			await renderRouter(registry, "/alpha/a1", { navigation: { "core.main": ["ghost/view", "beta/b1"] } });
			await screen.findByText("Seite a1");

			expect(tabIds()).toEqual([coreTestIds.navTab("beta", "b1"), coreTestIds.navTab("alpha", "a1")]);
			expect(warnings()).toEqual([expect.stringContaining("ghost/view")]);
		});

		it("shows a notice that no views are available when there is no tab", async () => {
			await renderRouter(registryOf([]), "/");

			expect(await screen.findByTestId(coreTestIds.noViews)).toBeTruthy();
			expect(screen.queryAllByRole("tab")).toHaveLength(0);
		});

		it("takes the logger of the options for its warnings", async () => {
			const warn = vi.fn();
			const logger = { warn, info: vi.fn(), debug: vi.fn(), error: vi.fn() } as unknown as Logger;
			await renderRouter(registry, "/alpha/a1", { logger, navigation: { start: "ghost/view" } });

			expect(warn).toHaveBeenCalledOnce();
		});
	});

	describe("layout of a main route", () => {
		function WithHeader() {
			usePageHeader(<h2>Kopfzeile</h2>);
			return <p>Inhalt</p>;
		}

		it("reserves the header area for a main route that asks for it and lets the page fill it", async () => {
			const registry = registryOf([plugin("example", tab("overview", async () => ({ default: WithHeader }), { header: true }))]);
			await renderRouter(registry, "/example/overview");

			expect(await screen.findByText("Inhalt")).toBeTruthy();
			expect((await screen.findByText("Kopfzeile")).closest(`[data-testid="${coreTestIds.pageHeader}"]`)).toBeTruthy();
		});

		it("has no header area for a main route that does not ask for it", async () => {
			await renderRouter(registryOf([plugin("example", tab("overview"))]), "/example/overview");
			await screen.findByText("Seite overview");

			expect(screen.queryByTestId(coreTestIds.pageHeader)).toBeNull();
		});
	});

	describe("development routes", () => {
		const registry = registryOf([plugin("example", tab("overview"))]);
		const devRoutes = [{ ownerId: "core", name: "dialogs", load: pageOf("Demo") }];

		it("shows a development page under /dev/<owner>/<name> without a tab", async () => {
			await renderRouter(registry, "/dev/core/dialogs", { devRoutes });

			expect(await screen.findByText("Demo")).toBeTruthy();
			expect(screen.getAllByRole("tab")).toHaveLength(1);
		});

		it("does not know the page without development routes", async () => {
			await renderRouter(registry, "/dev/core/dialogs");

			expect(await screen.findByTestId(coreTestIds.notFound)).toBeTruthy();
		});
	});

	it("can be reached through the router provider of the DOM", async () => {
		const { AppRouter } = await import("../../../../../../client/src/core/navigation/AppRouter");
		const registry = registryOf([plugin("example", tab("overview"))]);
		const lng = await initI18n({ lng: "en" });
		const router = createAppRouter({ registry, initialEntries: ["/example/overview"] });

		await act(async () => {
			render(
				<I18nextProvider i18n={lng}>
						<PluginRegistryProvider registry={registry}>
							<AppRouter router={router} />
						</PluginRegistryProvider>
				</I18nextProvider>,
			);
		});

		expect(await screen.findByText("Seite overview")).toBeTruthy();
	});
});

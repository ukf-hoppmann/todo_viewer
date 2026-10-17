import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ComponentType } from "react";
import { I18nextProvider } from "react-i18next";
import { RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { coreTestIds, initI18n, PluginRegistryProvider } from "../../../../../../client/src/core";
import { logging } from "../../../../../../client/src/core/logging/logging";
import { MemorySink } from "../../../../../../client/src/core/logging/MemorySink";
import { createAppRouter, type AppRouterOptions } from "../../../../../../client/src/core/navigation/createAppRouter";
import { usePageHeader } from "../../../../../../client/src/core/navigation/usePageHeader";
import type { ActivePlugin, Contribution, PluginRegistry, PluginStatus } from "../../../../../../client/src/core/plugins/types";

const i18n = { de: {}, en: {}, fr: {} };
const icon = () => null;

type Loader = () => Promise<{ default: ComponentType }>;

function pageOf(text: string): Loader {
	return async () => ({ default: () => <p>{text}</p> });
}

function hub(layout: { header?: boolean } = {}): Contribution {
	return { slot: "core.main", name: "hub", title: "t.hub", icon, layout: { ...layout, sidebar: true } };
}

function entry(slot: string, name: string, load: Loader = pageOf(`Seite ${name}`)): Contribution {
	return { slot, name, title: `t.${name}`, icon, page: load };
}

function plugin(id: string, ...contributions: Contribution[]): ActivePlugin {
	return { id, definition: { i18n, contributions } };
}

function registryOf(active: ActivePlugin[], others: PluginStatus[] = []): PluginRegistry {
	const statuses = [...active.map(({ id }): PluginStatus => ({ id, status: "active" })), ...others];
	return { active: () => active, statuses: () => statuses };
}

const sink = new MemorySink("create-app-router-sidebar-test");

async function renderRouter(registry: PluginRegistry, path: string, options: Partial<AppRouterOptions> = {}) {
	const lng = await initI18n({ lng: "en" });
	lng.addResourceBundle("en", "example", { "t.hub": "Hub", "t.start": "Start", "t.second": "Second" });
	lng.addResourceBundle("en", "addon", { "t.panel": "Panel" });
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

const item = (ownerId: string, name: string, slot = "example.hub") => screen.getByTestId(coreTestIds.sidebarItem(slot, ownerId, name));

/** `example` with a sidebar and its own entry `start`, and `addon` with the entry `panel`. */
const example = plugin("example", hub(), entry("example.hub", "start"));
const addon = plugin("addon", entry("example.hub", "panel"));

describe("createAppRouter: sidebars", () => {
	beforeEach(() => {
		logging.addSink(sink, { level: "debug" });
	});

	afterEach(() => {
		cleanup();
		logging.removeSink(sink.name);
		sink.entries.length = 0;
		vi.restoreAllMocks();
	});

	describe("entries", () => {
		it("shows the entry of another plugin under its address, with the tab and the entry selected", async () => {
			await renderRouter(registryOf([example, addon]), "/example/hub/addon/panel");

			expect(await screen.findByText("Seite panel")).toBeTruthy();
			expect(screen.getByTestId(coreTestIds.navTab("example", "hub")).getAttribute("aria-selected")).toBe("true");
			expect(item("addon", "panel").getAttribute("aria-current")).toBe("page");
			expect(item("example", "start").getAttribute("aria-current")).toBeNull();
		});

		it("shows every entry with its translated title, the entries of the host first", async () => {
			await renderRouter(registryOf([addon, example]), "/example/hub/example/start");
			await screen.findByText("Seite start");

			const items = screen.getByTestId(coreTestIds.sidebar).querySelectorAll("a");
			expect([...items].map((link) => link.textContent)).toEqual(["Start", "Panel"]);
		});

		it("goes to another entry when it is clicked and keeps the tab", async () => {
			const { router } = await renderRouter(registryOf([example, addon]), "/example/hub/example/start");
			await screen.findByText("Seite start");

			fireEvent.click(item("addon", "panel"));

			expect(await screen.findByText("Seite panel")).toBeTruthy();
			expect(router.state.location.pathname).toBe("/example/hub/addon/panel");
			expect(item("addon", "panel").getAttribute("aria-current")).toBe("page");
			expect(screen.getByTestId(coreTestIds.navTab("example", "hub")).getAttribute("aria-selected")).toBe("true");
		});

		it("lets a tab of the core have a sidebar that plugins hang entries into without requires", async () => {
			const core = [hub(), entry("core.hub", "list")];
			const plain = plugin("addon", entry("core.hub", "panel"));
			await renderRouter(registryOf([plain]), "/core/hub/addon/panel", { coreContributions: core });

			expect(await screen.findByText("Seite panel")).toBeTruthy();
			expect(screen.getByTestId(coreTestIds.sidebarItem("core.hub", "core", "list"))).toBeTruthy();
		});

		it("fills the header of the main route from the page of the selected entry", async () => {
			function WithHeader() {
				usePageHeader(<h2>Kopfzeile des Eintrags</h2>);
				return <p>Inhalt des Eintrags</p>;
			}
			const withHeader = plugin("example", hub({ header: true }), entry("example.hub", "start", async () => ({ default: WithHeader })));
			await renderRouter(registryOf([withHeader]), "/example/hub/example/start");

			expect(await screen.findByText("Inhalt des Eintrags")).toBeTruthy();
			expect((await screen.findByText("Kopfzeile des Eintrags")).closest(`[data-testid="${coreTestIds.pageHeader}"]`)).toBeTruthy();
		});

		it("replaces only the content when the import of an entry fails; sidebar and tabs stay usable", async () => {
			vi.spyOn(console, "error").mockImplementation(() => undefined);
			const broken = plugin("example", hub(), entry("example.hub", "start", () => Promise.reject(new Error("chunk fehlt"))), entry("example.hub", "second"));
			await renderRouter(registryOf([broken]), "/example/hub/example/start");

			expect(await screen.findByTestId(coreTestIds.errorFallback)).toBeTruthy();
			expect(screen.getByTestId(coreTestIds.sidebar)).toBeTruthy();
			fireEvent.click(item("example", "second"));

			expect(await screen.findByText("Seite second")).toBeTruthy();
			expect(screen.queryByTestId(coreTestIds.errorFallback)).toBeNull();
		});
	});

	describe("no entry chosen", () => {
		it("leads the main route to its first entry and replaces the history entry", async () => {
			const { router } = await renderRouter(registryOf([example, addon]), "/example/hub");

			expect(await screen.findByText("Seite start")).toBeTruthy();
			expect(router.state.location.pathname).toBe("/example/hub/example/start");
			expect(router.state.historyAction).toBe("REPLACE");
		});

		it("leads to the first entry of the order in the config", async () => {
			await renderRouter(registryOf([example, addon]), "/example/hub", { navigation: { "example.hub": ["addon/panel", "example/start"] } });

			expect(await screen.findByText("Seite panel")).toBeTruthy();
		});

		it("orders the entries by the list and the rest by the fixed rule", async () => {
			const more = plugin("example", hub(), entry("example.hub", "start"), entry("example.hub", "second"));
			await renderRouter(registryOf([more, addon]), "/example/hub/example/start", { navigation: { "example.hub": ["addon/panel"] } });
			await screen.findByText("Seite start");

			const items = screen.getByTestId(coreTestIds.sidebar).querySelectorAll("a");
			expect([...items].map((link) => link.textContent)).toEqual(["Panel", "Start", "Second"]);
		});

		it("skips unknown entries of the list and warns in development", async () => {
			await renderRouter(registryOf([example, addon]), "/example/hub/example/start", { navigation: { "example.hub": ["ghost/view", "addon/panel"] } });
			await screen.findByText("Seite start");

			const warnings = sink.entries.filter((entry) => entry.level === "warn").map((entry) => entry.message ?? "");
			expect(warnings).toEqual([expect.stringContaining("example.hub")]);
			expect(warnings[0]).toContain("ghost/view");
		});

		it("leads / to an entry of a sidebar when that is the start view", async () => {
			await renderRouter(registryOf([example, addon]), "/", { navigation: { start: "example/hub/addon/panel" } });

			expect(await screen.findByText("Seite panel")).toBeTruthy();
		});

		it("keeps the tab and shows a notice in the content when the sidebar has no entry, and warns", async () => {
			await renderRouter(registryOf([plugin("example", hub())]), "/example/hub");

			expect(await screen.findByTestId(coreTestIds.noEntries)).toBeTruthy();
			expect(screen.getByTestId(coreTestIds.navTab("example", "hub")).getAttribute("aria-selected")).toBe("true");
			expect(sink.entries.filter((entry) => entry.level === "warn")).toHaveLength(1);
		});
	});

	describe("plugins that are not there", () => {
		it("has neither the tab nor the entry when the host is switched off, and blocks the addon without an error", async () => {
			const registry = registryOf([], [
				{ id: "example", status: "disabled" },
				{ id: "addon", status: "blocked", code: "requires-disabled", cause: ["example"] },
			]);
			await renderRouter(registry, "/example/hub/addon/panel");

			expect(await screen.findByTestId(coreTestIds.unavailable)).toBeTruthy();
			expect(screen.queryAllByRole("tab")).toHaveLength(0);
			expect(screen.queryByTestId(coreTestIds.sidebar)).toBeNull();
		});

		it("shows only the remaining entries and the notice in the content, with the sidebar and the header in place, when the addon is switched off", async () => {
			const registry = registryOf([plugin("example", hub({ header: true }), entry("example.hub", "start"))], [{ id: "addon", status: "disabled" }]);
			await renderRouter(registry, "/example/hub/addon/panel");

			expect(await screen.findByTestId(coreTestIds.unavailable)).toBeTruthy();
			expect(screen.getByTestId(coreTestIds.sidebar)).toBeTruthy();
			expect(screen.queryByTestId(coreTestIds.sidebarItem("example.hub", "addon", "panel"))).toBeNull();
			expect(item("example", "start")).toBeTruthy();
			expect(screen.getByTestId(coreTestIds.pageHeader)).toBeTruthy();
			expect(screen.getByTestId(coreTestIds.content).contains(screen.getByTestId(coreTestIds.unavailable))).toBe(true);
			expect(sink.entries.filter((entry) => entry.level === "info")).toEqual([expect.objectContaining({ data: { path: "/example/hub/addon/panel" } })]);
		});

		it("shows 'does not exist' in the content for an entry that nobody contributed, with the sidebar in place", async () => {
			await renderRouter(registryOf([example, addon]), "/example/hub/ghost/view");

			expect(await screen.findByTestId(coreTestIds.notFound)).toBeTruthy();
			expect(screen.getByTestId(coreTestIds.sidebar)).toBeTruthy();
			expect(screen.getByTestId(coreTestIds.navTab("example", "hub")).getAttribute("aria-selected")).toBe("true");
		});

		it("does not log again for an entry of a plugin that failed", async () => {
			const registry = registryOf([example], [{ id: "addon", status: "failed", code: "contribution-invalid" }]);
			await renderRouter(registry, "/example/hub/addon/panel");

			expect(await screen.findByTestId(coreTestIds.unavailable)).toBeTruthy();
			expect(sink.entries).toHaveLength(0);
		});
	});
});

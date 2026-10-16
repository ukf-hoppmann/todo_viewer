import { ThemeProvider } from "@mui/material";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, describe, expect, it } from "vitest";
import { coreTestIds, initI18n, ModalHost, PluginRegistryProvider, theme } from "../../../../../../client/src/core";
import { AppFrame } from "../../../../../../client/src/core/navigation/AppFrame";
import type { NavEntry } from "../../../../../../client/src/core/navigation/types";
import type { PluginStatus } from "../../../../../../client/src/core/plugins/types";

const page = async () => ({ default: () => null });

function entry(ownerId: string, name: string): NavEntry {
	const Icon = () => <svg data-testid={`icon.${ownerId}.${name}`} />;
	return { ownerId, name, contribution: { slot: "core.main", name, title: `tab.${name}`, icon: Icon, page } };
}

async function renderFrame(path: string, tabs: NavEntry[], { lng = "en", statuses = [] as PluginStatus[] } = {}) {
	const i18n = await initI18n({ lng });
	i18n.addResourceBundle("en", "example", { tab: { overview: "Overview", details: "Details" } });
	i18n.addResourceBundle("de", "example", { tab: { overview: "Übersicht", details: "Details" } });
	const router = createMemoryRouter(
		[
			{
				path: "/",
				element: <AppFrame tabs={tabs} />,
				children: [
					{ path: "example/overview", element: <p>Seite Übersicht</p> },
					{ path: "example/details", element: <p>Seite Details</p> },
					{ path: "*", element: <p>Auffang</p> },
				],
			},
		],
		{ initialEntries: [path] },
	);
	render(
		<I18nextProvider i18n={i18n}>
			<ThemeProvider theme={theme}>
					<PluginRegistryProvider registry={{ active: () => [], statuses: () => statuses }}>
						<ModalHost />
						<RouterProvider router={router} />
					</PluginRegistryProvider>
			</ThemeProvider>
		</I18nextProvider>,
	);
	return { router };
}

const tabs = [entry("example", "overview"), entry("example", "details")];

describe("AppFrame: frame", () => {
	afterEach(cleanup);

	it("shows the language select in the app bar, behind the tabs", async () => {
		await renderFrame("/example/overview", tabs);

		const bar = screen.getByTestId(coreTestIds.appBar);
		const order = [screen.getByTestId(coreTestIds.tabBar), screen.getByTestId(coreTestIds.languageSelect)];
		for (const element of order) expect(bar.contains(element)).toBe(true);
		expect(order[0]!.compareDocumentPosition(order[1]!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
	});

	it("renders root, app bar and main area with their test ids", async () => {
		await renderFrame("/example/overview", tabs);

		expect(screen.getByTestId(coreTestIds.rootLayout)).toBeTruthy();
		expect(screen.getByTestId(coreTestIds.appBar)).toBeTruthy();
		expect(screen.getByTestId(coreTestIds.main)).toBeTruthy();
	});

	it("shows the logo named by the app title in the app bar", async () => {
		await renderFrame("/example/overview", tabs, { lng: "de" });

		expect(screen.getByRole("heading", { level: 1, name: "ToDo Viewer" })).toBeTruthy();
	});

	it("labels the main area in the active language", async () => {
		await renderFrame("/example/overview", tabs);

		expect(screen.getByTestId(coreTestIds.main).getAttribute("aria-label")).toBe("Main content");
	});

	it("shows the page of the current route in the main area", async () => {
		await renderFrame("/example/details", tabs);

		expect(screen.getByTestId(coreTestIds.main).textContent).toBe("Seite Details");
	});

	it("announces failed plugins once, as before", async () => {
		const failed: PluginStatus = { id: "broken", status: "failed", code: "import-failed", message: "x" };
		await renderFrame("/example/overview", tabs, { statuses: [failed] });

		expect(await screen.findByTestId(coreTestIds.modal)).toBeTruthy();
	});
});

describe("AppFrame: tabs", () => {
	afterEach(cleanup);

	it("shows a tab per entry with the translated title and the icon", async () => {
		await renderFrame("/example/overview", tabs);

		const tab = screen.getByTestId(coreTestIds.navTab("example", "overview"));
		expect(tab.textContent).toBe("Overview");
		expect(screen.getByTestId("icon.example.overview")).toBeTruthy();
		expect(screen.getByTestId(coreTestIds.navTab("example", "details")).textContent).toBe("Details");
		expect(screen.getByTestId(coreTestIds.tabBar)).toBeTruthy();
	});

	it("translates the titles into the language of the interface", async () => {
		await renderFrame("/example/overview", tabs, { lng: "de" });

		expect(screen.getByTestId(coreTestIds.navTab("example", "overview")).textContent).toBe("Übersicht");
	});

	it("selects the tab of the current main route, also when the page is opened directly", async () => {
		await renderFrame("/example/details", tabs);

		expect(screen.getByTestId(coreTestIds.navTab("example", "details")).getAttribute("aria-selected")).toBe("true");
		expect(screen.getByTestId(coreTestIds.navTab("example", "overview")).getAttribute("aria-selected")).toBe("false");
	});

	it("keeps the tab selected on a route below the main route", async () => {
		await renderFrame("/example/details/example/entry", tabs);

		expect(screen.getByTestId(coreTestIds.navTab("example", "details")).getAttribute("aria-selected")).toBe("true");
	});

	it("selects no tab on a path that belongs to none", async () => {
		await renderFrame("/ghost/view", tabs);

		for (const { ownerId, name } of tabs) {
			expect(screen.getByTestId(coreTestIds.navTab(ownerId, name)).getAttribute("aria-selected")).toBe("false");
		}
	});

	it("goes to the route of a tab when it is clicked", async () => {
		const { router } = await renderFrame("/example/overview", tabs);

		fireEvent.click(screen.getByTestId(coreTestIds.navTab("example", "details")));

		expect(router.state.location.pathname).toBe("/example/details");
		expect(screen.getByText("Seite Details")).toBeTruthy();
		expect(screen.getByTestId(coreTestIds.navTab("example", "details")).getAttribute("aria-selected")).toBe("true");
	});

	it("shows no tabs without entries", async () => {
		await renderFrame("/", []);

		expect(screen.queryAllByRole("tab")).toHaveLength(0);
	});
});

import { createTheme, ThemeProvider } from "@mui/material";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, describe, expect, it } from "vitest";
import { coreTestIds, initI18n } from "../../../../../../client/src/core";
import { Sidebar } from "../../../../../../client/src/core/navigation/Sidebar";
import type { SidebarEntry } from "../../../../../../client/src/core/navigation/types";

const page = async () => ({ default: () => null });
const host = { ownerId: "example", name: "hub" };

function entry(ownerId: string, name: string): SidebarEntry {
	const Icon = () => <svg data-testid={`icon.${ownerId}.${name}`} />;
	return { ownerId, name, slot: "example.hub", hostId: "example", hostName: "hub", contribution: { slot: "example.hub", name, title: `entry.${name}`, icon: Icon, page } };
}

const entries = [entry("example", "start"), entry("example-addon", "panel")];

async function renderSidebar(path: string, { lng = "en", theme }: { lng?: string; theme?: ReturnType<typeof createTheme> } = {}) {
	const i18n = await initI18n({ lng });
	i18n.addResourceBundle("en", "example", { "entry.start": "Start" });
	i18n.addResourceBundle("de", "example", { "entry.start": "Anfang" });
	i18n.addResourceBundle("en", "example-addon", { "entry.panel": "A very long name of a panel that does not fit" });
	const router = createMemoryRouter([{ path: "*", element: <Sidebar host={host} entries={entries} /> }], { initialEntries: [path] });
	const view = (
		<I18nextProvider i18n={i18n}>
			<RouterProvider router={router} />
		</I18nextProvider>
	);
	render(theme ? <ThemeProvider theme={theme}>{view}</ThemeProvider> : view);
	return { router };
}

const startId = coreTestIds.sidebarItem("example.hub", "example", "start");
const panelId = coreTestIds.sidebarItem("example.hub", "example-addon", "panel");

describe("Sidebar", () => {
	afterEach(cleanup);

	it("shows an entry per contribution with its translated title and its icon", async () => {
		await renderSidebar("/example/hub/example/start");

		expect(screen.getByTestId(startId).textContent).toBe("Start");
		expect(screen.getByTestId("icon.example.start")).toBeTruthy();
		expect(screen.getByTestId(panelId).textContent).toContain("A very long name");
		expect(screen.getByTestId(coreTestIds.sidebar)).toBeTruthy();
	});

	it("translates the titles into the language of the interface", async () => {
		await renderSidebar("/example/hub/example/start", { lng: "de" });

		expect(screen.getByTestId(startId).textContent).toBe("Anfang");
	});

	it("makes every entry a link to its own address", async () => {
		await renderSidebar("/example/hub/example/start");

		expect(screen.getByTestId(startId).getAttribute("href")).toBe("/example/hub/example/start");
		expect(screen.getByTestId(panelId).getAttribute("href")).toBe("/example/hub/example-addon/panel");
	});

	it("marks the selected entry for screen readers and no other", async () => {
		await renderSidebar("/example/hub/example-addon/panel");

		expect(screen.getByTestId(panelId).getAttribute("aria-current")).toBe("page");
		expect(screen.getByTestId(startId).getAttribute("aria-current")).toBeNull();
	});

	it("selects no entry when the address names none", async () => {
		await renderSidebar("/example/hub");

		expect(screen.getByTestId(startId).getAttribute("aria-current")).toBeNull();
		expect(screen.getByTestId(panelId).getAttribute("aria-current")).toBeNull();
	});

	it("goes to the address of an entry when it is clicked", async () => {
		const { router } = await renderSidebar("/example/hub/example/start");

		fireEvent.click(screen.getByTestId(panelId));

		expect(router.state.location.pathname).toBe("/example/hub/example-addon/panel");
		expect(screen.getByTestId(panelId).getAttribute("aria-current")).toBe("page");
	});

	it("shortens a long text with an ellipsis and keeps the full text for a tooltip", async () => {
		await renderSidebar("/example/hub/example/start");

		const link = screen.getByTestId(panelId);
		const text = link.querySelector("span.MuiTypography-root") as HTMLElement;
		expect(getComputedStyle(text).textOverflow).toBe("ellipsis");
		expect(getComputedStyle(text).whiteSpace).toBe("nowrap");
		expect(link.getAttribute("aria-label")).toBe("A very long name of a panel that does not fit");
	});

	it("keeps a minimum width so icon and text stay readable in a narrow window", async () => {
		await renderSidebar("/example/hub/example/start");

		expect(getComputedStyle(screen.getByTestId(coreTestIds.sidebar)).minWidth).toBe("200px");
	});

	it("highlights the selected entry with the secondary color of the theme and no fixed color", async () => {
		const theme = createTheme({ palette: { secondary: { main: "#123456" } } });
		await renderSidebar("/example/hub/example/start", { theme });

		const selected = screen.getByTestId(startId).closest(".MuiPaper-root") as HTMLElement;
		const other = screen.getByTestId(panelId).closest(".MuiPaper-root") as HTMLElement;
		expect(getComputedStyle(selected).backgroundColor).toBe("rgb(18, 52, 86)");
		expect(getComputedStyle(other).backgroundColor).not.toBe("rgb(18, 52, 86)");
	});
});

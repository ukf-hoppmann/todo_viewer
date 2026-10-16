import { ThemeProvider } from "@mui/material";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ComponentProps } from "react";
import { I18nextProvider } from "react-i18next";
import { afterEach, describe, expect, it } from "vitest";
import { banners, coreTestIds, initI18n, RootLayout, theme } from "../../../../../src/core";

/** Rendered without a router, a plugin registry, and a login: the layout must work before the login. */
async function renderLayout(props: ComponentProps<typeof RootLayout> = {}, lng = "en") {
	const i18n = await initI18n({ lng });
	render(
		<I18nextProvider i18n={i18n}>
			<ThemeProvider theme={theme}>
				<RootLayout {...props} />
			</ThemeProvider>
		</I18nextProvider>,
	);
}

function isBefore(first: HTMLElement, second: HTMLElement) {
	return Boolean(first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING);
}

describe("RootLayout", () => {
	afterEach(() => {
		cleanup();
		// The standard banner list is shared; close what a test left open.
		banners.clear();
	});

	it("shows the banners between the app bar and the main area", async () => {
		await renderLayout();

		act(() => {
			banners.show({ message: "Hinweis" });
		});

		const host = screen.getByTestId(coreTestIds.bannerHost);
		expect(screen.getByTestId(coreTestIds.rootLayout).contains(host)).toBe(true);
		expect(isBefore(screen.getByTestId(coreTestIds.appBar), host)).toBe(true);
		expect(isBefore(host, screen.getByTestId(coreTestIds.main))).toBe(true);
		expect(screen.getByTestId(coreTestIds.bannerMessage).textContent).toBe("Hinweis");
	});

	it("takes no room for banners while there is none", async () => {
		await renderLayout();

		expect(screen.queryByTestId(coreTestIds.bannerHost)).toBeNull();
	});

	it("renders the root, the app bar and the main area with their test ids", async () => {
		await renderLayout();

		const root = screen.getByTestId(coreTestIds.rootLayout);
		expect(root.contains(screen.getByTestId(coreTestIds.appBar))).toBe(true);
		expect(root.contains(screen.getByTestId(coreTestIds.main))).toBe(true);
	});

	it("puts the children into the main area, below the app bar", async () => {
		await renderLayout({ children: <p data-testid="content">Inhalt</p> });

		const main = screen.getByTestId(coreTestIds.main);
		expect(main.contains(screen.getByTestId("content"))).toBe(true);
		expect(screen.getByTestId(coreTestIds.appBar).contains(screen.getByTestId("content"))).toBe(false);
		expect(isBefore(screen.getByTestId(coreTestIds.appBar), main)).toBe(true);
	});

	it("labels the main area in the active language", async () => {
		await renderLayout({}, "en");

		expect(screen.getByTestId(coreTestIds.main).getAttribute("aria-label")).toBe("Main content");
	});

	it("shows the logo named by the app title in the app bar", async () => {
		await renderLayout({}, "de");

		const logo = screen.getByRole("heading", { level: 1, name: "ET" });
		expect(screen.getByTestId(coreTestIds.appBar).contains(logo)).toBe(true);
	});

	it("shows the tabs behind the logo and before the switches, and the actions behind the switches", async () => {
		await renderLayout({ tabs: <nav data-testid="tabs">Tabs</nav>, actions: <button data-testid="action">Aktion</button> });

		const bar = screen.getByTestId(coreTestIds.appBar);
		const order = [
			screen.getByRole("heading", { level: 1, name: "ET" }),
			screen.getByTestId("tabs"),
			screen.getByTestId(coreTestIds.languageSelect),
			screen.getByTestId(coreTestIds.colorSchemeButton),
			screen.getByTestId("action"),
		];
		for (const element of order) expect(bar.contains(element)).toBe(true);
		for (let index = 1; index < order.length; index++) expect(isBefore(order[index - 1]!, order[index]!)).toBe(true);
	});

	it("shows only the logo and the switches without tabs and actions", async () => {
		await renderLayout();

		const bar = screen.getByTestId(coreTestIds.appBar);
		expect(bar.contains(screen.getByTestId(coreTestIds.languageSelect))).toBe(true);
		expect(bar.contains(screen.getByTestId(coreTestIds.colorSchemeButton))).toBe(true);
		expect(screen.queryByTestId(coreTestIds.tabBar)).toBeNull();
		expect(screen.queryByTestId(coreTestIds.logoutButton)).toBeNull();
	});

	it("lets the user switch the language without a router, a registry, or a login", async () => {
		await renderLayout({}, "de");
		const before = screen.getByTestId(coreTestIds.main).getAttribute("aria-label");

		fireEvent.mouseDown(screen.getByTestId(coreTestIds.languageSelect));
		fireEvent.click(screen.getByTestId(coreTestIds.languageOption("en")));

		expect(before).not.toBe("Main content");
		expect(screen.getByTestId(coreTestIds.main).getAttribute("aria-label")).toBe("Main content");
	});
});

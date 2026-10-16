import { ThemeProvider } from "@mui/material";
import { cleanup, render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, describe, expect, it } from "vitest";
import { coreTestIds, initI18n, PluginRegistryProvider, theme } from "../../../../../../client/src/core";
import { definePlugin } from "../../../../../../client/src/core/plugins/definePlugin";
import type { ActivePlugin, Contribution } from "../../../../../../client/src/core/plugins/types";
import SettingsPage from "../../../../../../client/src/core/settings/SettingsPage";
import { settingsContribution } from "../../../../../../client/src/core/settings/settingsContribution";
import { SubLayout } from "../../../../../../client/src/core/navigation/SubLayout";

const i18nTexts = { de: {}, en: {} };
const section = (name: string, text: string, extra: Partial<Contribution> = {}) =>
	({ slot: "core.settings-sections", name, component: () => <p>{text}</p>, ...extra }) as Contribution;
const plugin = (id: string, contributions: Contribution[]): ActivePlugin => ({ id, definition: definePlugin({ i18n: i18nTexts, contributions }) });

async function renderPage(active: ActivePlugin[], lng = "en") {
	const i18n = await initI18n({ lng });
	const router = createMemoryRouter(
		[
			{
				path: "/core/settings",
				element: (
					<SubLayout header>
						<SettingsPage />
					</SubLayout>
				),
			},
		],
		{ initialEntries: ["/core/settings"] },
	);
	render(
		<I18nextProvider i18n={i18n}>
			<ThemeProvider theme={theme}>
				<PluginRegistryProvider registry={{ active: () => active, statuses: () => [] }}>
					<RouterProvider router={router} />
				</PluginRegistryProvider>
			</ThemeProvider>
		</I18nextProvider>,
	);
}

describe("SettingsPage", () => {
	afterEach(cleanup);

	it("says so when no plugin contributes a section", async () => {
		await renderPage([plugin("a", [])]);

		expect(screen.getByTestId(coreTestIds.settingsEmpty).textContent).toBe("There are no settings yet.");
	});

	it("draws one card per section, in the order of the slot, each with its test id", async () => {
		await renderPage([plugin("b", [section("late", "B spät")]), plugin("a", [section("two", "A zwei"), section("one", "A eins", { order: -1 })])]);

		const texts = screen.getAllByTestId(/^core\.settings-section\./).map((card) => [card.getAttribute("data-testid"), card.textContent]);
		expect(texts).toEqual([
			["core.settings-section.a.one", "A eins"],
			["core.settings-section.a.two", "A zwei"],
			["core.settings-section.b.late", "B spät"],
		]);
		expect(screen.queryByTestId(coreTestIds.settingsEmpty)).toBeNull();
	});

	it("fills the header of its main route with the title in the active language", async () => {
		await renderPage([], "de");

		expect(screen.getByTestId(coreTestIds.pageHeader).textContent).toBe("Einstellungen");
	});
});

describe("settingsContribution", () => {
	it("is the main route core/settings with a header", () => {
		expect(settingsContribution).toMatchObject({ slot: "core.main", name: "settings", title: "settings.tab", layout: { header: true } });
	});
});

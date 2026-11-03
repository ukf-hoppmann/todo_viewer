import { ThemeProvider } from "@mui/material";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
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

async function renderPage(active: ActivePlugin[], lng = "en", location = "/core/settings") {
	const i18n = await initI18n({ lng });
	const router = createMemoryRouter(
		[
			{
				path: "/core/settings",
				element: (
					<SubLayout ownerId="core" layout={{ header: true }}>
						<SettingsPage />
					</SubLayout>
				),
			},
		],
		{ initialEntries: [location] },
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
	return router;
}

describe("SettingsPage", () => {
	afterEach(cleanup);

	it("says so when no plugin contributes a section", async () => {
		await renderPage([plugin("a", [])]);

		expect(screen.getByTestId(coreTestIds.settingsEmpty).textContent).toBe("There are no settings yet.");
	});

	it("draws one card per section of the group, in the order of the slot, each with its test id", async () => {
		await renderPage(
			[plugin("b", [section("late", "B spät")]), plugin("a", [section("two", "A zwei"), section("one", "A eins", { order: -1 })])],
			"en",
			"/core/settings?group=system",
		);

		const texts = screen.getAllByTestId(/^core\.settings-section\./).map((card) => [card.getAttribute("data-testid"), card.textContent]);
		expect(texts).toEqual([
			["core.settings-section.a.one", "A eins"],
			["core.settings-section.a.two", "A zwei"],
			["core.settings-section.b.late", "B spät"],
		]);
		expect(screen.queryByTestId(coreTestIds.settingsEmpty)).toBeNull();
	});

	it("shows only the sections of the group in the URL and marks its entry in the navigation", async () => {
		await renderPage([plugin("a", [section("p", "Projekt", { group: "projects" }), section("s", "System", { group: "system" })])], "en", "/core/settings?group=projects");

		expect(screen.getAllByTestId(/^core\.settings-section\./).map((card) => card.textContent)).toEqual(["Projekt"]);
		expect(screen.getByTestId(coreTestIds.settingsGroup("projects")).getAttribute("aria-current")).toBe("page");
		expect(screen.getByTestId(coreTestIds.settingsGroup("system")).getAttribute("aria-current")).toBeNull();
	});

	it("lists the groups in the navigation with their names in the active language", async () => {
		await renderPage([plugin("a", [section("s", "System")])], "de");

		expect(screen.getByTestId(coreTestIds.settingsGroup("projects")).textContent).toBe("Projekte");
		expect(screen.getByTestId(coreTestIds.settingsGroup("system")).textContent).toBe("System");
	});

	it("opens the first group that has sections when the URL names none or an unknown group", async () => {
		await renderPage([plugin("a", [section("s", "System")])]);
		expect(screen.getAllByTestId(/^core\.settings-section\./).map((card) => card.textContent)).toEqual(["System"]);
		cleanup();

		await renderPage([plugin("a", [section("s", "System"), section("p", "Projekt", { group: "projects" })])], "en", "/core/settings?group=nope");
		expect(screen.getAllByTestId(/^core\.settings-section\./).map((card) => card.textContent)).toEqual(["Projekt"]);
	});

	it("puts a section without a group into the group system", async () => {
		await renderPage([plugin("a", [section("plain", "Ohne Gruppe")])], "en", "/core/settings?group=system");

		expect(screen.getByTestId(coreTestIds.settingsSection("a", "plain")).textContent).toBe("Ohne Gruppe");
	});

	it("switches the group by clicking its entry and puts it into the URL", async () => {
		const router = await renderPage([plugin("a", [section("p", "Projekt", { group: "projects" }), section("s", "System", { group: "system" })])]);

		fireEvent.click(screen.getByTestId(coreTestIds.settingsGroup("system")));

		expect(router.state.location.search).toBe("?group=system");
		expect(screen.getAllByTestId(/^core\.settings-section\./).map((card) => card.textContent)).toEqual(["System"]);
	});

	it("says so when the open group has no sections", async () => {
		await renderPage([plugin("a", [section("s", "System")])], "en", "/core/settings?group=projects");

		expect(screen.getByTestId(coreTestIds.settingsGroupEmpty).textContent).toBe("There are no settings in this group.");
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

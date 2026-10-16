import { ThemeProvider } from "@mui/material";
import { act, cleanup, render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { afterEach, describe, expect, it } from "vitest";
import { StartedView } from "../../../../src/app/StartedView";
import type { StartResult } from "../../../../src/app/startApp";
import { banners, coreTestIds, initI18n, theme } from "../../../../src/core";
import { fakeAuth } from "../../../helpers/fakeAuth";

async function show(started: StartResult | undefined, lng = "de") {
	const i18n = await initI18n({ lng });
	render(
		<I18nextProvider i18n={i18n}>
			<ThemeProvider theme={theme}>
				<StartedView started={started} />
			</ThemeProvider>
		</I18nextProvider>,
	);
}

describe("StartedView: the layout in every state of the start", () => {
	afterEach(() => {
		cleanup();
		// The standard banner list is shared; close what a test left open.
		banners.clear();
	});

	it.each([
		["the start is still running", undefined],
		["the start has stopped", { kind: "stopped" } as StartResult],
		["the user is not logged in", { kind: "login", auth: fakeAuth("unauthenticated") } as StartResult],
	])("shows banners when %s", async (_name, started) => {
		await show(started);

		act(() => {
			banners.show({ message: "Hinweis" });
		});

		expect(screen.getByTestId(coreTestIds.rootLayout).contains(screen.getByTestId(coreTestIds.bannerHost))).toBe(true);
		expect(screen.getByTestId(coreTestIds.bannerMessage).textContent).toBe("Hinweis");
	});

	it("shows the layout with an empty main area while the start is still running, so that there is no blank page when the backend does not answer", async () => {
		await show(undefined);

		expect(screen.getByTestId(coreTestIds.rootLayout)).toBeTruthy();
		expect(screen.getByTestId(coreTestIds.appBar).contains(screen.getByTestId(coreTestIds.languageSelect))).toBe(true);
		expect(screen.getByTestId(coreTestIds.main).textContent).toBe("");
		expect(screen.queryByTestId(coreTestIds.tabBar)).toBeNull();
		expect(screen.queryByTestId(coreTestIds.loginPage)).toBeNull();
	});

	it("shows the layout with an empty main area when the start has stopped, so that the switches stay usable", async () => {
		await show({ kind: "stopped" });

		expect(screen.getByTestId(coreTestIds.rootLayout)).toBeTruthy();
		expect(screen.getByTestId(coreTestIds.appBar).contains(screen.getByTestId(coreTestIds.languageSelect))).toBe(true);
		expect(screen.getByTestId(coreTestIds.main).textContent).toBe("");
		expect(screen.queryByTestId(coreTestIds.tabBar)).toBeNull();
		expect(screen.queryByTestId(coreTestIds.loginPage)).toBeNull();
	});

	it("shows the layout with the login in the main area when the user is not logged in, without tabs", async () => {
		await show({ kind: "login", auth: fakeAuth("unauthenticated") });

		expect(screen.getByTestId(coreTestIds.rootLayout)).toBeTruthy();
		expect(screen.getByTestId(coreTestIds.main).contains(screen.getByTestId(coreTestIds.loginPage))).toBe(true);
		expect(screen.getByTestId(coreTestIds.loginButton)).toBeTruthy();
		expect(screen.queryByTestId(coreTestIds.tabBar)).toBeNull();
	});
});

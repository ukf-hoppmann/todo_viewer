import { ThemeProvider } from "@mui/material";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { afterEach, describe, expect, it } from "vitest";
import { AuthProvider, coreTestIds, initI18n, LoginPage, theme } from "../../../../../src/core";
import { fakeAuth } from "../../../../helpers/fakeAuth";

async function renderPage(lng = "de") {
	const i18n = await initI18n({ lng });
	const auth = fakeAuth("unauthenticated");
	render(
		<I18nextProvider i18n={i18n}>
			<ThemeProvider theme={theme}>
				<AuthProvider auth={auth}>
					<LoginPage />
				</AuthProvider>
			</ThemeProvider>
		</I18nextProvider>,
	);
	return { auth };
}

describe("LoginPage", () => {
	afterEach(cleanup);

	it("shows the page with the sentence and the button in German", async () => {
		await renderPage("de");

		expect(screen.getByTestId(coreTestIds.loginPage).textContent).toContain("Bitte melden Sie sich an.");
		expect(screen.getByTestId(coreTestIds.loginButton).textContent).toBe("Anmelden");
	});

	it.each([
		["en", "Please sign in.", "Sign in"],
		["fr", "Veuillez vous connecter.", "Se connecter"],
	])("shows the texts in %s", async (lng, sentence, button) => {
		await renderPage(lng);

		expect(screen.getByTestId(coreTestIds.loginPage).textContent).toContain(sentence);
		expect(screen.getByTestId(coreTestIds.loginButton).textContent).toBe(button);
	});

	it("shows the logo named by the app title in the app bar, and neither tabs nor the logout button", async () => {
		await renderPage();

		expect(screen.getByRole("heading", { level: 1, name: "ET" })).toBeTruthy();
		expect(screen.queryByTestId(coreTestIds.tabBar)).toBeNull();
		expect(screen.queryByTestId(coreTestIds.logoutButton)).toBeNull();
	});

	it("shows the language select and the color scheme menu in the app bar, so they work before the login", async () => {
		await renderPage();

		const bar = screen.getByTestId(coreTestIds.appBar);
		expect(bar.contains(screen.getByTestId(coreTestIds.languageSelect))).toBe(true);
		expect(bar.contains(screen.getByTestId(coreTestIds.colorSchemeButton))).toBe(true);
	});

	it("shows the page in the language chosen in the app bar", async () => {
		await renderPage("de");

		fireEvent.mouseDown(screen.getByTestId(coreTestIds.languageSelect));
		fireEvent.click(screen.getByTestId(coreTestIds.languageOption("en")));

		expect(screen.getByTestId(coreTestIds.loginPage).textContent).toContain("Please sign in.");
		expect(screen.getByTestId(coreTestIds.loginButton).textContent).toBe("Sign in");
	});

	it("starts the login when the button is clicked", async () => {
		const { auth } = await renderPage();

		fireEvent.click(screen.getByTestId(coreTestIds.loginButton));

		expect(auth.login).toHaveBeenCalledOnce();
	});
});

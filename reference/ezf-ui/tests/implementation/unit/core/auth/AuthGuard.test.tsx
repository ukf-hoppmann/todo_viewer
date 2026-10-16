import { act, cleanup, render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { afterEach, describe, expect, it } from "vitest";
import { AuthGuard, AuthProvider, coreTestIds, initI18n, useAuth } from "../../../../../src/core";
import type { AuthState } from "../../../../../src/core";
import { fakeAuth } from "../../../../helpers/fakeAuth";

async function renderGuard(state: AuthState) {
	const i18n = await initI18n({ lng: "de" });
	const auth = fakeAuth(state);
	render(
		<I18nextProvider i18n={i18n}>
			<AuthProvider auth={auth}>
				<AuthGuard>
					<p data-testid="inside">Geschützter Inhalt</p>
				</AuthGuard>
			</AuthProvider>
		</I18nextProvider>,
	);
	return { auth };
}

describe("AuthGuard", () => {
	afterEach(cleanup);

	it("shows the content when the user is logged in", async () => {
		await renderGuard("authenticated");

		expect(screen.getByTestId("inside")).toBeTruthy();
		expect(screen.queryByTestId(coreTestIds.loginPage)).toBeNull();
	});

	it("shows the login page instead of the content when the user is not logged in", async () => {
		await renderGuard("unauthenticated");

		expect(screen.getByTestId(coreTestIds.loginPage)).toBeTruthy();
		expect(screen.queryByTestId("inside")).toBeNull();
	});

	it("shows nothing before the login has been checked", async () => {
		await renderGuard("unknown");

		expect(screen.queryByTestId("inside")).toBeNull();
		expect(screen.queryByTestId(coreTestIds.loginPage)).toBeNull();
	});

	it("replaces the content by the login page as soon as a request reports 401 or 407", async () => {
		const { auth } = await renderGuard("authenticated");

		act(() => auth.unauthorized());

		expect(screen.getByTestId(coreTestIds.loginPage)).toBeTruthy();
		expect(screen.queryByTestId("inside")).toBeNull();
	});
});

describe("useAuth", () => {
	afterEach(cleanup);

	function Probe() {
		const { state } = useAuth();
		return <p data-testid="state">{state}</p>;
	}

	it("gives the state and follows its changes", async () => {
		const auth = fakeAuth("authenticated");
		render(
			<AuthProvider auth={auth}>
				<Probe />
			</AuthProvider>,
		);
		expect(screen.getByTestId("state").textContent).toBe("authenticated");

		act(() => auth.unauthorized());

		expect(screen.getByTestId("state").textContent).toBe("unauthenticated");
	});

	it("throws without a provider, so that nothing is shown unprotected by mistake", () => {
		expect(() => render(<Probe />)).toThrow("useAuth must be used inside an AuthProvider");
	});
});

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { coreTestIds, initI18n } from "../../../../../src/core";
import { ErrorBoundary } from "../../../../../src/core/errors/ErrorBoundary";

let broken = true;
function Flaky() {
	if (broken) throw new Error("kaputt");
	return <p>repariert</p>;
}

describe("ErrorBoundary: onRetry", () => {
	beforeEach(() => {
		broken = true;
		vi.spyOn(console, "error").mockImplementation(() => undefined);
	});

	afterEach(() => {
		cleanup();
		vi.restoreAllMocks();
	});

	it("calls onRetry when the user tries again, before the area is rendered again", async () => {
		const i18n = await initI18n({ lng: "en" });
		const onRetry = vi.fn(() => {
			broken = false;
		});
		render(
			<I18nextProvider i18n={i18n}>
				<ErrorBoundary origin="core" onRetry={onRetry}>
					<Flaky />
				</ErrorBoundary>
			</I18nextProvider>,
		);

		fireEvent.click(screen.getByTestId(coreTestIds.errorFallbackRetry));

		expect(onRetry).toHaveBeenCalledOnce();
		expect(screen.getByText("repariert")).toBeTruthy();
	});
});

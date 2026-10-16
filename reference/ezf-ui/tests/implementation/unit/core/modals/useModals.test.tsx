import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useEffect } from "react";
import { I18nextProvider } from "react-i18next";
import { afterEach, describe, expect, it } from "vitest";
import { coreTestIds, initI18n, ModalHost, modals, useModals } from "../../../../../src/core";
import type { Modals } from "../../../../../src/core";

afterEach(cleanup);

describe("useModals", () => {
	it("returns the same object as modals", () => {
		let captured: Modals | undefined;
		function Capture() {
			const value = useModals();
			useEffect(() => {
				captured = value;
			}, [value]);
			return null;
		}

		render(<Capture />);

		expect(captured).toBe(modals);
	});

	it("opens a dialog from a component", async () => {
		const i18n = await initI18n({ lng: "en" });
		function Opener() {
			const dialogs = useModals();
			return <button data-testid="test.open" onClick={() => void dialogs.alert({ title: "From component" })} />;
		}
		render(
			<I18nextProvider i18n={i18n}>
				<Opener />
				<ModalHost />
			</I18nextProvider>,
		);

		fireEvent.click(screen.getByTestId("test.open"));

		expect(screen.getByTestId(coreTestIds.modalTitle).textContent).toBe("From component");
		fireEvent.click(screen.getByTestId(coreTestIds.modalClose));
		await waitFor(() => expect(screen.queryByTestId(coreTestIds.modal)).toBeNull());
	});
});

describe("modals outside of React", () => {
	it("shows a dialog requested before the host was mounted, and resolves it", async () => {
		let closed = false;
		void modals.alert({ title: "Early" }).then(() => {
			closed = true;
		});
		const i18n = await initI18n({ lng: "en" });

		act(() => {
			render(
				<I18nextProvider i18n={i18n}>
					<ModalHost />
				</I18nextProvider>,
			);
		});

		expect(screen.getByTestId(coreTestIds.modalTitle).textContent).toBe("Early");
		fireEvent.click(screen.getByTestId(coreTestIds.modalClose));
		await waitFor(() => expect(closed).toBe(true));
	});
});

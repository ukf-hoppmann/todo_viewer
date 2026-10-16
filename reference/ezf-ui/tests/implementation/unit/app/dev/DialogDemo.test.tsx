import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { afterEach, describe, expect, it } from "vitest";
import { DialogDemo } from "../../../../../src/app/dev/DialogDemo";
import { demoTestIds } from "../../../../../src/app/dev/demoTestIds";
import { coreTestIds, initI18n, ModalHost, modals } from "../../../../../src/core";

async function renderDemo() {
	const i18n = await initI18n({ lng: "de" });
	render(
		<I18nextProvider i18n={i18n}>
			<ModalHost />
			<DialogDemo />
		</I18nextProvider>,
	);
}

/** Answers everything still in the queue, so that the next test starts empty. */
function drainQueue() {
	for (let pending = modals.getSnapshot(); pending; pending = modals.getSnapshot()) {
		if (pending.kind === "alert") pending.close();
		else if (pending.kind === "confirm") pending.answer(false);
		else pending.answer(false, pending.request.initialData);
	}
}

const click = (id: string) => fireEvent.click(screen.getByTestId(id));
const title = () => screen.getByTestId(coreTestIds.modalTitle).textContent;
const result = () => screen.getByTestId(demoTestIds.result).textContent;

afterEach(() => {
	drainQueue();
	cleanup();
});

describe("DialogDemo", () => {
	it("shows the demo page without a result and without a dialog", async () => {
		await renderDemo();

		expect(screen.getByTestId(demoTestIds.page)).toBeDefined();
		expect(screen.queryByTestId(coreTestIds.modal)).toBeNull();
		expect(result()).toBe("–");
	});

	it.each([
		[demoTestIds.alertError, "Fehler"],
		[demoTestIds.alertWarning, "Warnung"],
		[demoTestIds.alertInfo, "Information"],
		[demoTestIds.alertSuccess, "Erfolg"],
	])("opens an alert for %s with the default title %s", async (id, expectedTitle) => {
		await renderDemo();

		click(id);

		expect(title()).toBe(expectedTitle);
		expect(screen.getByTestId(coreTestIds.modalMessage).textContent).not.toBe("");
	});

	it("notes that the alert was closed", async () => {
		await renderDemo();
		click(demoTestIds.alertInfo);

		click(coreTestIds.modalClose);

		await waitFor(() => expect(result()).toContain("geschlossen"));
	});

	it("opens an alert with technical details", async () => {
		await renderDemo();

		click(demoTestIds.alertDetails);

		expect(screen.getByTestId(coreTestIds.modalDetailsToggle)).toBeDefined();
		fireEvent.click(screen.getByTestId(coreTestIds.modalDetailsToggle));
		expect(screen.getByTestId(coreTestIds.modalDetails).textContent).toContain("Fehler-ID");
	});

	it("shows the answer of a confirmation", async () => {
		await renderDemo();
		click(demoTestIds.confirm);

		click(coreTestIds.modalConfirm);
		await waitFor(() => expect(result()).toContain("bestätigt"));

		click(demoTestIds.confirm);
		click(coreTestIds.modalCancel);
		await waitFor(() => expect(result()).toContain("abgebrochen"));
	});

	it("returns what was entered in the dialog with content", async () => {
		await renderDemo();
		click(demoTestIds.confirmBody);

		fireEvent.change(screen.getByTestId(demoTestIds.bodyName), { target: { value: "Ada" } });
		fireEvent.click(screen.getByTestId(demoTestIds.bodyCounter));
		fireEvent.click(screen.getByTestId(demoTestIds.bodyCounter));
		click(coreTestIds.modalConfirm);

		await waitFor(() => expect(result()).toContain("bestätigt"));
		expect(result()).toContain('"name":"Ada"');
		expect(result()).toContain('"count":2');
	});

	it("queues several dialogs one after another", async () => {
		await renderDemo();

		click(demoTestIds.queue);

		expect(title()).toBe("Erster Hinweis");
		click(coreTestIds.modalClose);
		await waitFor(() => expect(title()).toBe("Rückfrage dazwischen"));
		click(coreTestIds.modalConfirm);
		await waitFor(() => expect(title()).toBe("Letzter Hinweis"));
	});

	it("reports an error with log entry and alert", async () => {
		await renderDemo();

		click(demoTestIds.reportError);

		expect(title()).toBe("Fehler");
		fireEvent.click(screen.getByTestId(coreTestIds.modalDetailsToggle));
		const details = screen.getByTestId(coreTestIds.modalDetails).textContent ?? "";
		expect(details).toContain("TypeError: Failed to fetch");
		expect(details).toContain("Fehler-ID");
	});

	it("reports a warning", async () => {
		await renderDemo();

		click(demoTestIds.reportWarning);

		expect(title()).toBe("Warnung");
	});
});

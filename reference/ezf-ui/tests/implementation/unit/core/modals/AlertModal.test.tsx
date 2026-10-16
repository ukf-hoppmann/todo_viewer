import { act, cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { coreTestIds } from "../../../../../src/core";
import { renderHost } from "../../../../helpers/renderHost";

afterEach(() => {
	cleanup();
	vi.unstubAllGlobals();
});

const details = [
	{ label: "Time", value: "2026-09-30T12:00:00.000Z" },
	{ label: { key: "modals.close" }, value: "abc12345" },
];

describe("alert", () => {
	it("shows nothing while the queue is empty", async () => {
		await renderHost();

		expect(screen.queryByTestId(coreTestIds.modal)).toBeNull();
	});

	it("shows title, message and a close button", async () => {
		const { modals } = await renderHost();

		act(() => {
			void modals.alert({ severity: "error", title: "Save failed", message: "Try again later" });
		});

		expect(screen.getByTestId(coreTestIds.modalTitle).textContent).toBe("Save failed");
		expect(screen.getByTestId(coreTestIds.modalMessage).textContent).toBe("Try again later");
		expect(screen.getByTestId(coreTestIds.modalClose).textContent).toBe("Close");
	});

	it.each([
		["error", "Error"],
		["warning", "Warning"],
		["info", "Information"],
		["success", "Success"],
	] as const)("uses the default title of severity %s", async (severity, title) => {
		const { modals } = await renderHost();

		act(() => {
			void modals.alert({ severity });
		});

		expect(screen.getByTestId(coreTestIds.modalTitle).textContent).toBe(title);
	});

	it("uses the severity info and its title when none is given", async () => {
		const { modals } = await renderHost();

		act(() => {
			void modals.alert({ message: "x" });
		});

		expect(screen.getByTestId(coreTestIds.modalTitle).textContent).toBe("Information");
	});

	it("shows default titles in the language of the app", async () => {
		const { modals } = await renderHost("de");

		act(() => {
			void modals.alert({ severity: "warning" });
		});

		expect(screen.getByTestId(coreTestIds.modalTitle).textContent).toBe("Warnung");
		expect(screen.getByTestId(coreTestIds.modalClose).textContent).toBe("Schließen");
	});

	it("leaves out the message when there is none", async () => {
		const { modals } = await renderHost();

		act(() => {
			void modals.alert({});
		});

		expect(screen.queryByTestId(coreTestIds.modalMessage)).toBeNull();
	});

	it("translates keys and keeps finished texts", async () => {
		const { modals } = await renderHost("fr");

		act(() => {
			void modals.alert({ title: { key: "modals.technicalDetails" }, message: "Texte du serveur" });
		});

		expect(screen.getByTestId(coreTestIds.modalTitle).textContent).toBe("Détails techniques");
		expect(screen.getByTestId(coreTestIds.modalMessage).textContent).toBe("Texte du serveur");
	});

	it("keeps line breaks of the message", async () => {
		const { modals } = await renderHost();

		act(() => {
			void modals.alert({ message: "first\n\nsecond" });
		});

		const message = screen.getByTestId(coreTestIds.modalMessage);
		expect(message.textContent).toBe("first\n\nsecond");
		expect(getComputedStyle(message).whiteSpace).toBe("pre-line");
	});

	it("resolves the promise only when it is closed with the button", async () => {
		const { modals } = await renderHost();
		const done = vi.fn();
		act(() => {
			void modals.alert({ message: "x" }).then(done);
		});
		await Promise.resolve();
		expect(done).not.toHaveBeenCalled();

		fireEvent.click(screen.getByTestId(coreTestIds.modalClose));

		await waitFor(() => expect(done).toHaveBeenCalledTimes(1));
		await waitFor(() => expect(screen.queryByTestId(coreTestIds.modal)).toBeNull());
	});

	it("closes with Escape", async () => {
		const { modals } = await renderHost();
		const done = vi.fn();
		act(() => {
			void modals.alert({ message: "x" }).then(done);
		});

		fireEvent.keyDown(screen.getByTestId(coreTestIds.modal), { key: "Escape" });

		await waitFor(() => expect(done).toHaveBeenCalledTimes(1));
	});

	it("shows the next queued alert after closing", async () => {
		const { modals } = await renderHost();
		act(() => {
			void modals.alert({ title: "one" });
			void modals.alert({ title: "two" });
		});
		expect(screen.getByTestId(coreTestIds.modalTitle).textContent).toBe("one");

		fireEvent.click(screen.getByTestId(coreTestIds.modalClose));

		await waitFor(() => expect(screen.getByTestId(coreTestIds.modalTitle).textContent).toBe("two"));
	});
});

describe("alert details", () => {
	it("has no details section without details", async () => {
		const { modals } = await renderHost();

		act(() => {
			void modals.alert({ message: "x" });
		});

		expect(screen.queryByTestId(coreTestIds.modalDetailsToggle)).toBeNull();
	});

	it("keeps details collapsed until the toggle is used", async () => {
		const { modals } = await renderHost();
		act(() => {
			void modals.alert({ message: "x", details });
		});

		const toggle = screen.getByTestId(coreTestIds.modalDetailsToggle);
		expect(toggle.textContent).toContain("Technical details");
		expect(toggle.getAttribute("aria-expanded")).toBe("false");
		expect(screen.queryByTestId(coreTestIds.modalDetails)).toBeNull();

		fireEvent.click(toggle);

		expect(toggle.getAttribute("aria-expanded")).toBe("true");
		const shown = screen.getByTestId(coreTestIds.modalDetails);
		expect(shown.textContent).toContain("Time");
		expect(shown.textContent).toContain("2026-09-30T12:00:00.000Z");
		expect(shown.textContent).toContain("Close");
		expect(shown.textContent).toContain("abc12345");
	});

	it("collapses again with a second click", async () => {
		const { modals } = await renderHost();
		act(() => {
			void modals.alert({ message: "x", details });
		});
		const toggle = screen.getByTestId(coreTestIds.modalDetailsToggle);

		fireEvent.click(toggle);
		fireEvent.click(toggle);

		expect(screen.queryByTestId(coreTestIds.modalDetails)).toBeNull();
	});

	it("does not offer copying without navigator.clipboard", async () => {
		vi.stubGlobal("navigator", { ...navigator, clipboard: undefined });
		const { modals } = await renderHost();
		act(() => {
			void modals.alert({ message: "x", details });
		});

		fireEvent.click(screen.getByTestId(coreTestIds.modalDetailsToggle));

		expect(screen.getByTestId(coreTestIds.modalDetails)).toBeDefined();
		expect(screen.queryByTestId(coreTestIds.modalDetailsCopy)).toBeNull();
	});

	it("copies all rows as label: value lines and confirms it", async () => {
		const writeText = vi.fn().mockResolvedValue(undefined);
		vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText } });
		const { modals } = await renderHost();
		act(() => {
			void modals.alert({ message: "x", details });
		});
		fireEvent.click(screen.getByTestId(coreTestIds.modalDetailsToggle));

		const copy = screen.getByTestId(coreTestIds.modalDetailsCopy);
		expect(copy.textContent).toBe("Copy");
		fireEvent.click(copy);

		expect(writeText).toHaveBeenCalledWith("Time: 2026-09-30T12:00:00.000Z\nClose: abc12345");
		await waitFor(() => expect(copy.textContent).toBe("Copied"));
	});

	it("keeps the details inside the dialog", async () => {
		const { modals } = await renderHost();
		act(() => {
			void modals.alert({ message: "x", details });
		});
		fireEvent.click(screen.getByTestId(coreTestIds.modalDetailsToggle));

		const dialog = screen.getByTestId(coreTestIds.modal);

		expect(within(dialog).getByTestId(coreTestIds.modalDetails)).toBeDefined();
	});
});

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { coreTestIds, initI18n } from "../../../../../src/core";
import { LanguageSelect } from "../../../../../src/core/navigation/LanguageSelect";
import { fakeStorage } from "../../../../helpers/fakeBrowser";

async function renderSelect(lng = "de") {
	const i18n = await initI18n({ lng });
	render(
		<I18nextProvider i18n={i18n}>
			<LanguageSelect />
		</I18nextProvider>,
	);
	return { i18n };
}

function choose(lng: string) {
	fireEvent.mouseDown(screen.getByTestId(coreTestIds.languageSelect));
	fireEvent.click(screen.getByTestId(coreTestIds.languageOption(lng)));
}

describe("LanguageSelect", () => {
	// The storage of the language detection: a fresh one in memory for every test.
	let storage: ReturnType<typeof fakeStorage>;

	beforeEach(() => {
		storage = fakeStorage();
		vi.stubGlobal("localStorage", storage);
		window.history.replaceState(null, "", "/");
	});
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
	});

	it("shows the name of the active language", async () => {
		await renderSelect("en");

		expect(screen.getByTestId(coreTestIds.languageSelect).textContent).toBe("English");
	});

	it("offers every supported language under its own name", async () => {
		await renderSelect();

		fireEvent.mouseDown(screen.getByTestId(coreTestIds.languageSelect));

		expect(screen.getByTestId(coreTestIds.languageOption("de")).textContent).toBe("Deutsch");
		expect(screen.getByTestId(coreTestIds.languageOption("en")).textContent).toBe("English");
		expect(screen.getByTestId(coreTestIds.languageOption("fr")).textContent).toBe("Français");
	});

	it("labels the select in the active language", async () => {
		await renderSelect("fr");

		expect(screen.getByTestId(coreTestIds.languageSelect).getAttribute("aria-label")).toBe("Langue");
	});

	it("changes the language of the interface and shows the new name", async () => {
		const { i18n } = await renderSelect("de");

		choose("en");

		expect(i18n.resolvedLanguage).toBe("en");
		expect(screen.getByTestId(coreTestIds.languageSelect).textContent).toBe("English");
		expect(screen.getByTestId(coreTestIds.languageSelect).getAttribute("aria-label")).toBe("Language");
	});

	it("remembers the choice for the next visit", async () => {
		await renderSelect("de");

		choose("fr");

		expect(storage.getItem("i18nextLng")).toBe("fr");
	});

	it("shows the matching entry when the browser language is a regional variant", async () => {
		await renderSelect("de-DE");

		expect(screen.getByTestId(coreTestIds.languageSelect).textContent).toBe("Deutsch");
	});

	it("removes the language parameter from the address, keeping the rest and the history", async () => {
		window.history.replaceState({ idx: 4 }, "", "/example/overview?a=1&lng=en#prefill");
		const entries = window.history.length;
		await renderSelect("en");

		choose("de");

		expect(window.location.pathname + window.location.search + window.location.hash).toBe("/example/overview?a=1#prefill");
		expect(window.history.length).toBe(entries);
		expect(window.history.state).toEqual({ idx: 4 });
	});

	it("leaves the address alone without the language parameter", async () => {
		window.history.replaceState({ idx: 2 }, "", "/example/overview?a=1");
		await renderSelect("en");

		choose("de");

		expect(window.location.pathname + window.location.search).toBe("/example/overview?a=1");
		expect(window.history.state).toEqual({ idx: 2 });
	});
});

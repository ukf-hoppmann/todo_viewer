import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { afterEach, describe, expect, it } from "vitest";
import { coreTestIds, initI18n } from "../../../../../../client/src/core";
import { LanguageSelect } from "../../../../../../client/src/core/navigation/LanguageSelect";

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
	afterEach(cleanup);

	it("shows the name of the active language", async () => {
		await renderSelect("en");

		expect(screen.getByTestId(coreTestIds.languageSelect).textContent).toBe("English");
	});

	it("offers German and English under their own names, and nothing else", async () => {
		await renderSelect();

		fireEvent.mouseDown(screen.getByTestId(coreTestIds.languageSelect));

		expect(screen.getByTestId(coreTestIds.languageOption("de")).textContent).toBe("Deutsch");
		expect(screen.getByTestId(coreTestIds.languageOption("en")).textContent).toBe("English");
		expect(screen.getAllByRole("option")).toHaveLength(2);
	});

	it("labels the select in the active language", async () => {
		await renderSelect("en");

		expect(screen.getByTestId(coreTestIds.languageSelect).getAttribute("aria-label")).toBe("Language");
	});

	it("changes the language of the interface and shows the new name", async () => {
		const { i18n } = await renderSelect("de");

		choose("en");

		expect(i18n.resolvedLanguage).toBe("en");
		expect(await screen.findByText("English")).toBeTruthy();
	});

	it("counts a regional variant as its language", async () => {
		await renderSelect("de-DE");

		expect(screen.getByTestId(coreTestIds.languageSelect).textContent).toBe("Deutsch");
	});

	it("does not use the storage of the browser", async () => {
		const before = { ...localStorage };
		await renderSelect("de");

		choose("en");

		expect({ ...localStorage }).toEqual(before);
	});
});

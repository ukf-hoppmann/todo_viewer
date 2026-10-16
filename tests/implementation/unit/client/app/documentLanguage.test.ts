import { describe, expect, it } from "vitest";
import { syncDocumentLanguage } from "../../../../../client/src/app/documentLanguage";
import { initI18n } from "../../../../../client/src/core";

/** An empty document of its own, so that the test does not touch the page of the test run. */
const newDocument = () => document.implementation.createHTMLDocument("test");

describe("syncDocumentLanguage", () => {
	it("sets the language of the document to the active language at once", async () => {
		const i18n = await initI18n({ lng: "en" });
		const doc = newDocument();

		syncDocumentLanguage(i18n, doc);

		expect(doc.documentElement.lang).toBe("en");
	});

	it("names a regional variant by the language in effect", async () => {
		const i18n = await initI18n({ lng: "de-DE" });
		const doc = newDocument();

		syncDocumentLanguage(i18n, doc);

		expect(doc.documentElement.lang).toBe("de");
	});

	it("follows every change of the language", async () => {
		const i18n = await initI18n({ lng: "de" });
		const doc = newDocument();
		syncDocumentLanguage(i18n, doc);

		await i18n.changeLanguage("en");
		expect(doc.documentElement.lang).toBe("en");

		await i18n.changeLanguage("de");
		expect(doc.documentElement.lang).toBe("de");
	});

	it("stops following after the returned function was called", async () => {
		const i18n = await initI18n({ lng: "de" });
		const doc = newDocument();
		const stop = syncDocumentLanguage(i18n, doc);

		stop();
		await i18n.changeLanguage("en");

		expect(doc.documentElement.lang).toBe("de");
	});
});

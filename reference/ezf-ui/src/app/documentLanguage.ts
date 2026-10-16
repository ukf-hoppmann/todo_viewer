import type { i18n } from "i18next";

/**
 * Keeps `lang` of the document equal to the language of the interface, so that screen readers and the
 * spell checker of the browser treat the texts in the right language. Sets it at once and after every
 * change; returns the function that stops following.
 */
export function syncDocumentLanguage(instance: i18n, doc: Document = document): () => void {
	const apply = () => {
		doc.documentElement.lang = instance.resolvedLanguage ?? instance.language;
	};

	apply();
	instance.on("languageChanged", apply);
	return () => instance.off("languageChanged", apply);
}

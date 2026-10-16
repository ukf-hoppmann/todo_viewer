import { createInstance, type i18n } from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";
import de from "./locales/de.json";
import en from "./locales/en.json";

/** Languages of the interface; core and every plugin bring texts for each of them. */
export const supportedLanguages = ["de", "en"] as const;

export type SupportedLanguage = (typeof supportedLanguages)[number];

export type InitI18nOptions = {
	/** Fixed language; without it the language is detected from the browser. */
	lng?: string;
};

/**
 * Creates and initialises a new i18next instance with the core texts
 * (namespace `core`). Each call returns its own instance; nothing global is
 * changed.
 */
export async function initI18n(options: InitI18nOptions = {}): Promise<i18n> {
	const instance = createInstance();

	await instance
		.use(LanguageDetector)
		.use(initReactI18next)
		.init({
			lng: options.lng,
			resources: {
				de: { core: de },
				en: { core: en },
			},
			supportedLngs: [...supportedLanguages],
			fallbackLng: "de",
			ns: ["core"],
			defaultNS: "core",
			interpolation: {
				// React escapes output itself.
				escapeValue: false,
			},
		});

	return instance;
}
